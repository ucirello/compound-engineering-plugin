#!/bin/bash

# Experiment Workspace Manager
# Creates, cleans up, and manages jj workspaces for optimization experiments.
# Each experiment gets an isolated workspace with copied shared resources.
#
# Usage:
#   experiment-worktree.sh create <spec_name> <exp_index> <base_bookmark> [shared_file ...]
#   experiment-worktree.sh cleanup <spec_name> <exp_index>
#   experiment-worktree.sh cleanup-all <spec_name>
#   experiment-worktree.sh count
#
# Workspaces are created at: .workspaces/optimize-<spec>-exp-<NNN>/
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

WORKSPACE_DIR="$JJ_ROOT/.workspaces"

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

jj_at_root() {
  (cd "$JJ_ROOT" && jj "$@")
}

jj_in_workspace() {
  local workspace_path="${1:?Error: workspace_path required}"
  shift
  (cd "$workspace_path" && jj "$@")
}

bookmark_exists() {
  local bookmark_name="${1:?Error: bookmark_name required}"
  jj_at_root bookmark list -r "$bookmark_name" >/dev/null 2>&1
}

is_registered_workspace() {
  local workspace_name="${1:?Error: workspace_name required}"
  local workspace_path="${2:?Error: workspace_path required}"
  local registered

  registered=$(jj_at_root workspace root --name "$workspace_name" 2>/dev/null) || return 1
  [[ "$registered" == "$workspace_path" ]]
}

workspace_name_in_use_elsewhere() {
  local workspace_name="${1:?Error: workspace_name required}"
  local workspace_path="${2:?Error: workspace_path required}"
  local registered

  registered=$(jj_at_root workspace root --name "$workspace_name" 2>/dev/null) || return 1
  [[ "$registered" != "$workspace_path" ]]
}

reset_workspace_to_base() {
  local workspace_path="${1:?Error: workspace_path required}"
  local bookmark_name="${2:?Error: bookmark_name required}"
  local base_bookmark="${3:?Error: base_bookmark required}"
  local current_bookmarks

  current_bookmarks=$(jj_in_workspace "$workspace_path" log -r @ -T 'bookmarks ++ "\n"' --no-graph 2>/dev/null || true)
  if ! grep -F -q "$bookmark_name" <<<"$current_bookmarks"; then
    echo -e "${RED}Error: Existing workspace is on unexpected bookmark: ${current_bookmarks:-none} (expected $bookmark_name)${NC}" >&2
    echo -e "${RED}Clean up the stale workspace before rerunning this experiment.${NC}" >&2
    return 1
  fi

  echo -e "${YELLOW}Resetting existing experiment workspace to base: $bookmark_name -> $base_bookmark${NC}" >&2
  jj_in_workspace "$workspace_path" new "$base_bookmark"
  jj_in_workspace "$workspace_path" bookmark set "$bookmark_name" -r @ --allow-backwards >/dev/null
}

copy_shared_into_workspace() {
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

point_bookmark_at_workspace() {
  local workspace_path="${1:?Error: workspace_path required}"
  local bookmark_name="${2:?Error: bookmark_name required}"

  if bookmark_exists "$bookmark_name"; then
    jj_in_workspace "$workspace_path" bookmark set "$bookmark_name" -r @ --allow-backwards >/dev/null
  else
    jj_in_workspace "$workspace_path" bookmark create "$bookmark_name" >/dev/null
  fi
}

# Create an experiment workspace
create_workspace() {
  local spec_name="${1:?Error: spec_name required}"
  local exp_index="${2:?Error: exp_index required}"
  local base_bookmark="${3:?Error: base_bookmark required}"
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
      echo -e "${RED}Error: Existing path is not a valid registered jj workspace: $workspace_path${NC}" >&2
      echo -e "${RED}Remove or repair that directory before rerunning the experiment.${NC}" >&2
      return 1
    fi

    echo -e "${YELLOW}Workspace already exists: $workspace_path${NC}" >&2
    reset_workspace_to_base "$workspace_path" "$bookmark_name" "$base_bookmark"
  else
    mkdir -p "$WORKSPACE_DIR"

    if workspace_name_in_use_elsewhere "$workspace_name" "$workspace_path"; then
      echo -e "${RED}Error: Existing experiment workspace name is already in use: $workspace_name${NC}" >&2
      echo -e "${RED}Clean up the stale workspace before rerunning this experiment.${NC}" >&2
      return 1
    fi

    if ! jj_at_root --quiet workspace add "$workspace_path" --name "$workspace_name" -r "$base_bookmark"; then
      if bookmark_exists "$bookmark_name"; then
        echo -e "${YELLOW}Resetting existing experiment bookmark to base: $bookmark_name -> $base_bookmark${NC}" >&2
        jj_at_root bookmark set "$bookmark_name" -r "$base_bookmark" --allow-backwards >/dev/null
        jj_at_root --quiet workspace add "$workspace_path" --name "$workspace_name" -r "$bookmark_name" || {
          echo -e "${RED}Error: Failed to create workspace for $bookmark_name from $base_bookmark${NC}" >&2
          return 1
        }
      else
        echo -e "${RED}Error: Failed to create workspace for $bookmark_name from $base_bookmark${NC}" >&2
        return 1
      fi
    fi

    point_bookmark_at_workspace "$workspace_path" "$bookmark_name"
  fi

  copy_shared_into_workspace "$workspace_path" "$@"

  echo "$workspace_path"
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
  local registered_path

  registered_path=$(jj_at_root workspace root --name "$workspace_name" 2>/dev/null || true)
  if [[ -n "$registered_path" ]]; then
    jj_at_root workspace forget "$workspace_name" >/dev/null 2>&1 || true
    rm -rf "$registered_path" 2>/dev/null || true
  fi

  if [[ -d "$workspace_path" ]]; then
    rm -rf "$workspace_path" 2>/dev/null || true
  fi

  jj_at_root bookmark delete "$bookmark_name" >/dev/null 2>&1 || true

  echo -e "${GREEN}Cleaned up: $workspace_name${NC}" >&2
}

# Clean up all experiment workspaces for a spec
cleanup_all() {
  local spec_name="${1:?Error: spec_name required}"
  local prefix="optimize-${spec_name}-exp-"
  local count=0
  local name

  while IFS= read -r name; do
    [[ -z "$name" ]] && continue
    case "$name" in
      ${prefix}*)
        local index_str="${name#$prefix}"
        local bookmark_name
        bookmark_name=$(experiment_bookmark_name "$spec_name" "$index_str")
        local registered_path
        registered_path=$(jj_at_root workspace root --name "$name" 2>/dev/null || true)
        jj_at_root workspace forget "$name" >/dev/null 2>&1 || true
        if [[ -n "$registered_path" ]]; then
          rm -rf "$registered_path" 2>/dev/null || true
        fi
        jj_at_root bookmark delete "$bookmark_name" >/dev/null 2>&1 || true
        count=$((count + 1))
        ;;
    esac
  done < <(jj_at_root workspace list -T 'name ++ "\n"')

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

  if [[ "$count" -eq 0 ]]; then
    echo -e "${YELLOW}No experiment workspaces found for $spec_name${NC}" >&2
    return 0
  fi

  echo -e "${GREEN}Cleaned up $count experiment workspace(s) for $spec_name${NC}" >&2
}

# Count experiment workspaces (for budget check)
count_workspaces() {
  local count=0
  local name
  while IFS= read -r name; do
    [[ -z "$name" ]] && continue
    case "$name" in
      optimize-*-exp-*)
        count=$((count + 1))
        ;;
    esac
  done < <(jj_at_root workspace list -T 'name ++ "\n"')
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
  experiment-worktree.sh create <spec_name> <exp_index> <base_bookmark> [shared_file ...]
  experiment-worktree.sh cleanup <spec_name> <exp_index>
  experiment-worktree.sh cleanup-all <spec_name>
  experiment-worktree.sh count

Commands:
  create       Create an experiment workspace with copied shared files
  cleanup      Remove a single experiment workspace and its bookmark
  cleanup-all  Remove all experiment workspaces for a spec
  count        Count total active experiment workspaces (for budget checking)

Workspaces: .workspaces/optimize-<spec>-exp-<NNN>/
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
