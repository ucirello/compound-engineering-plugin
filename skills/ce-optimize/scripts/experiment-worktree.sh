#!/bin/bash

# Experiment Workspace Manager
# Creates, cleans up, and manages JJ workspaces for optimization experiments.
# Each experiment gets an isolated workspace with copied shared resources.
#
# Usage:
#   experiment-worktree.sh create <spec_name> <exp_index> <base_revision> [shared_file ...]
#   experiment-worktree.sh cleanup <spec_name> <exp_index>
#   experiment-worktree.sh cleanup-all <spec_name>
#   experiment-worktree.sh count
#
# Workspaces are created at: .tmp/ce-optimize/workspaces/optimize-<spec>-exp-<NNN>/
# Bookmarks are named: optimize-exp/<spec>/exp-<NNN>

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

JJ_ROOT=$(jj workspace root 2>/dev/null) || {
  echo -e "${RED}Error: Not in a Jujutsu repository${NC}" >&2
  exit 1
}

WORKSPACE_DIR="$JJ_ROOT/.tmp/ce-optimize/workspaces"

jj_in() {
  local cwd="${1:?Error: cwd required}"
  shift
  (cd "$cwd" && jj "$@")
}

experiment_bookmark_name() {
  local spec_name="${1:?Error: spec_name required}"
  local padded_index="${2:?Error: padded_index required}"

  # Keep experiment refs outside optimize/<spec> so they do not collide
  # with the long-lived optimization bookmark namespace.
  echo "optimize-exp/${spec_name}/exp-${padded_index}"
}

experiment_workspace_name() {
  local spec_name="${1:?Error: spec_name required}"
  local padded_index="${2:?Error: padded_index required}"

  echo "optimize-${spec_name}-exp-${padded_index}"
}

bookmark_exists() {
  local bookmark_name="${1:?Error: bookmark_name required}"
  local listing
  listing=$(jj_in "$JJ_ROOT" bookmark list "exact:${bookmark_name}" 2>/dev/null || true)
  [[ -n "$listing" ]]
}

is_registered_workspace() {
  local workspace_name="${1:?Error: workspace_name required}"
  local workspace_path="${2:?Error: workspace_path required}"
  local actual actual_abs path_abs

  actual=$(jj_in "$JJ_ROOT" workspace root --name "$workspace_name" 2>/dev/null) || return 1
  actual_abs=$(cd "$actual" && pwd -P)
  path_abs=$(cd "$workspace_path" && pwd -P)
  [[ "$actual_abs" == "$path_abs" ]]
}

workspace_name_in_use() {
  local workspace_name="${1:?Error: workspace_name required}"
  jj_in "$JJ_ROOT" workspace root --name "$workspace_name" >/dev/null 2>&1
}

current_local_bookmarks() {
  local workspace_path="${1:?Error: workspace_path required}"
  jj_in "$workspace_path" log -r @ --no-graph -T 'local_bookmarks.map(|b| stringify(b.name())).join("\n")' 2>/dev/null || true
}

reset_workspace_to_base() {
  local workspace_path="${1:?Error: workspace_path required}"
  local bookmark_name="${2:?Error: bookmark_name required}"
  local base_revision="${3:?Error: base_revision required}"
  local current_bookmarks

  current_bookmarks=$(current_local_bookmarks "$workspace_path")
  if ! echo "$current_bookmarks" | grep -qxF "$bookmark_name"; then
    echo -e "${RED}Error: Existing workspace is on unexpected bookmark: ${current_bookmarks:-none} (expected $bookmark_name)${NC}" >&2
    echo -e "${RED}Clean up the stale workspace before rerunning this experiment.${NC}" >&2
    return 1
  fi

  echo -e "${YELLOW}Resetting existing experiment workspace to base: $bookmark_name -> $base_revision${NC}" >&2
  jj_in "$workspace_path" new "$base_revision" >/dev/null
  jj_in "$workspace_path" bookmark set --allow-backwards "$bookmark_name" -r @ >/dev/null
}

copy_shared_resources() {
  local workspace_path="${1:?Error: workspace_path required}"
  shift

  local f
  for f in "$JJ_ROOT"/.env*; do
    if [[ -f "$f" ]]; then
      local basename
      basename=$(basename "$f")
      if [[ "$basename" != ".env.example" ]]; then
        cp "$f" "$workspace_path/$basename"
      fi
    fi
  done

  local shared_file
  for shared_file in "$@"; do
    if [[ -f "$JJ_ROOT/$shared_file" ]]; then
      local dir
      dir=$(dirname "$workspace_path/$shared_file")
      mkdir -p "$dir"
      cp "$JJ_ROOT/$shared_file" "$workspace_path/$shared_file"
    elif [[ -d "$JJ_ROOT/$shared_file" ]]; then
      local dir
      dir=$(dirname "$workspace_path/$shared_file")
      mkdir -p "$dir"
      rm -rf "$workspace_path/$shared_file"
      cp -R "$JJ_ROOT/$shared_file" "$workspace_path/$shared_file"
    fi
  done
}

# Create an experiment workspace
create_workspace() {
  local spec_name="${1:?Error: spec_name required}"
  local exp_index="${2:?Error: exp_index required}"
  local base_revision="${3:?Error: base_revision required}"
  shift 3

  local padded_index
  padded_index=$(printf "%03d" "$exp_index")
  local workspace_name
  workspace_name=$(experiment_workspace_name "$spec_name" "$padded_index")
  local bookmark_name
  bookmark_name=$(experiment_bookmark_name "$spec_name" "$padded_index")
  local workspace_path="$WORKSPACE_DIR/$workspace_name"

  if [[ -d "$workspace_path" ]]; then
    if ! is_registered_workspace "$workspace_name" "$workspace_path"; then
      echo -e "${RED}Error: Existing path is not a valid registered JJ workspace: $workspace_path${NC}" >&2
      echo -e "${RED}Remove or repair that directory before rerunning the experiment.${NC}" >&2
      return 1
    fi

    echo -e "${YELLOW}Workspace already exists: $workspace_path${NC}" >&2
    reset_workspace_to_base "$workspace_path" "$bookmark_name" "$base_revision"
  else
    mkdir -p "$WORKSPACE_DIR"

    if ! jj_in "$JJ_ROOT" workspace add --name "$workspace_name" --revision "$base_revision" "$workspace_path" >/dev/null 2>&1; then
      if workspace_name_in_use "$workspace_name"; then
        echo -e "${RED}Error: Existing experiment workspace name is already in use: $workspace_name${NC}" >&2
        echo -e "${RED}Clean up the stale workspace before rerunning this experiment.${NC}" >&2
        return 1
      fi

      if bookmark_exists "$bookmark_name"; then
        echo -e "${YELLOW}Resetting existing experiment bookmark to base: $bookmark_name -> $base_revision${NC}" >&2
        jj_in "$JJ_ROOT" bookmark set --allow-backwards "$bookmark_name" -r "$base_revision" >/dev/null
        if ! jj_in "$JJ_ROOT" workspace add --name "$workspace_name" --revision "$bookmark_name" "$workspace_path" >/dev/null; then
          echo -e "${RED}Error: Failed to create workspace for $bookmark_name from $base_revision${NC}" >&2
          return 1
        fi
      else
        echo -e "${RED}Error: Failed to create workspace for $bookmark_name from $base_revision${NC}" >&2
        return 1
      fi
    fi

    jj_in "$workspace_path" bookmark set --allow-backwards "$bookmark_name" -r @ >/dev/null
  fi

  copy_shared_resources "$workspace_path" "$@"

  echo "$workspace_path"
}

forget_workspace_and_bookmark() {
  local workspace_name="${1:?Error: workspace_name required}"
  local workspace_path="${2:?Error: workspace_path required}"
  local bookmark_name="${3:?Error: bookmark_name required}"

  if workspace_name_in_use "$workspace_name"; then
    jj_in "$JJ_ROOT" workspace forget "$workspace_name" >/dev/null 2>&1 || true
  fi

  if [[ -d "$workspace_path" ]]; then
    rm -rf "$workspace_path" 2>/dev/null || true
  fi

  if bookmark_exists "$bookmark_name"; then
    jj_in "$JJ_ROOT" bookmark forget "$bookmark_name" >/dev/null 2>&1 || true
  fi
}

# Clean up a single experiment workspace
cleanup_workspace() {
  local spec_name="${1:?Error: spec_name required}"
  local exp_index="${2:?Error: exp_index required}"

  local padded_index
  padded_index=$(printf "%03d" "$exp_index")
  local workspace_name
  workspace_name=$(experiment_workspace_name "$spec_name" "$padded_index")
  local bookmark_name
  bookmark_name=$(experiment_bookmark_name "$spec_name" "$padded_index")
  local workspace_path="$WORKSPACE_DIR/$workspace_name"

  forget_workspace_and_bookmark "$workspace_name" "$workspace_path" "$bookmark_name"

  echo -e "${GREEN}Cleaned up: $workspace_name${NC}" >&2
}

# Clean up all experiment workspaces for a spec
cleanup_all() {
  local spec_name="${1:?Error: spec_name required}"
  local prefix="optimize-${spec_name}-exp-"
  local count=0
  local workspace_name workspace_path bookmark_name padded_index

  while IFS= read -r workspace_name; do
    [[ -z "$workspace_name" ]] && continue
    [[ "$workspace_name" == "$prefix"* ]] || continue

    padded_index="${workspace_name#$prefix}"
    bookmark_name=$(experiment_bookmark_name "$spec_name" "$padded_index")
    workspace_path=$(jj_in "$JJ_ROOT" workspace root --name "$workspace_name" 2>/dev/null || echo "$WORKSPACE_DIR/$workspace_name")
    forget_workspace_and_bookmark "$workspace_name" "$workspace_path" "$bookmark_name"
    count=$((count + 1))
  done < <(jj_in "$JJ_ROOT" workspace list -T 'stringify(name) ++ "\n"' 2>/dev/null || true)

  if [[ -d "$WORKSPACE_DIR" ]]; then
    local leftover
    for leftover in "$WORKSPACE_DIR"/${prefix}*; do
      if [[ -d "$leftover" ]]; then
        rm -rf "$leftover" 2>/dev/null || true
      fi
    done
    if [[ -z "$(ls -A "$WORKSPACE_DIR" 2>/dev/null)" ]]; then
      rmdir "$WORKSPACE_DIR" 2>/dev/null || true
    fi
  fi

  echo -e "${GREEN}Cleaned up $count experiment workspace(s) for $spec_name${NC}" >&2
}

# Count total experiment workspaces (for budget check)
count_workspaces() {
  local count=0
  local workspace_name
  while IFS= read -r workspace_name; do
    [[ -z "$workspace_name" ]] && continue
    case "$workspace_name" in
      optimize-*-exp-*)
        count=$((count + 1))
        ;;
    esac
  done < <(jj_in "$JJ_ROOT" workspace list -T 'stringify(name) ++ "\n"' 2>/dev/null || true)
  echo "$count"
}

# Main
main() {
  local command="${1:-help}"

  case "$command" in
    create)
      shift
      create_workspace "$@"
      ;;
    cleanup)
      shift
      cleanup_workspace "$@"
      ;;
    cleanup-all)
      shift
      cleanup_all "$@"
      ;;
    count)
      count_workspaces
      ;;
    help)
      cat << 'EOF'
Experiment Workspace Manager

Usage:
  experiment-worktree.sh create <spec_name> <exp_index> <base_revision> [shared_file ...]
  experiment-worktree.sh cleanup <spec_name> <exp_index>
  experiment-worktree.sh cleanup-all <spec_name>
  experiment-worktree.sh count

Commands:
  create       Create an experiment JJ workspace with copied shared files
  cleanup      Remove a single experiment workspace and its bookmark
  cleanup-all  Remove all experiment workspaces for a spec
  count        Count total active experiment workspaces (for budget checking)

Workspaces: .tmp/ce-optimize/workspaces/optimize-<spec>-exp-<NNN>/
Bookmarks:  optimize-exp/<spec>/exp-<NNN>
EOF
      ;;
    *)
      echo -e "${RED}Unknown command: $command${NC}" >&2
      exit 1
      ;;
  esac
}

main "$@"
