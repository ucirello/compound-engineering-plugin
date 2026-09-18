#!/bin/bash

# Experiment workspace manager
# Creates, cleans up, and manages JJ workspaces for optimization experiments.
# Each experiment gets an isolated workspace with copied shared resources.
#
# The script name is kept for skill invocation compatibility. Internals use
# public `jj` only (jj workspace add|list|forget|root). Never parse .jj/ or
# .git/, and never use their existence as repo identity.
#
# Usage:
#   experiment-worktree.sh create <spec_name> <exp_index> <base_branch> [shared_file ...]
#   experiment-worktree.sh cleanup <spec_name> <exp_index>
#   experiment-worktree.sh cleanup-all <spec_name>
#   experiment-worktree.sh count
#
# Workspaces are created at: .worktrees/optimize-<spec>-exp-<NNN>/
# Bookmarks are named: optimize-exp/<spec>/exp-<NNN>

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

DEFAULT_ROOT=$(jj workspace root 2>/dev/null) || {
  echo -e "${RED}Error: Not in a Jujutsu workspace${NC}" >&2
  exit 1
}

WORKSPACE_DIR="$DEFAULT_ROOT/.worktrees"

jj_at() {
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

list_workspace_names() {
  jj_at "$DEFAULT_ROOT" workspace list -T 'name ++ "\n"'
}

workspace_root_for_name() {
  local name="${1:?Error: workspace name required}"
  jj_at "$DEFAULT_ROOT" workspace root --name "$name"
}

is_registered_workspace() {
  local workspace_path="${1:?Error: workspace_path required}"
  local workspace_name="${2:?Error: workspace_name required}"
  local actual

  actual=$(workspace_root_for_name "$workspace_name" 2>/dev/null) || return 1
  [[ "$actual" == "$workspace_path" ]]
}

bookmark_exists() {
  local bookmark_name="${1:?Error: bookmark_name required}"
  local listed

  listed=$(jj_at "$DEFAULT_ROOT" bookmark list "exact:${bookmark_name}" -T 'name ++ "\n"' 2>/dev/null || true)
  [[ -n "$listed" ]]
}

bookmark_held_by_other_workspace() {
  local bookmark_name="${1:?Error: bookmark_name required}"
  local skip_name="${2:-}"
  local name root held

  while IFS= read -r name; do
    [[ -z "$name" || "$name" == "$skip_name" ]] && continue
    root=$(workspace_root_for_name "$name" 2>/dev/null) || continue
    held=$(jj_at "$root" bookmark list -r @ "exact:${bookmark_name}" -T 'name ++ "\n"' 2>/dev/null || true)
    if [[ -n "$held" ]]; then
      return 0
    fi
  done < <(list_workspace_names)
  return 1
}

point_bookmark_at_working_copy() {
  local workspace_path="${1:?Error: workspace_path required}"
  local bookmark_name="${2:?Error: bookmark_name required}"

  if bookmark_exists "$bookmark_name"; then
    jj_at "$workspace_path" bookmark set --allow-backwards "$bookmark_name" -r @ >/dev/null
  else
    jj_at "$workspace_path" bookmark create "$bookmark_name" -r @ >/dev/null
  fi
}

reset_workspace_to_base() {
  local workspace_path="${1:?Error: workspace_path required}"
  local workspace_name="${2:?Error: workspace_name required}"
  local bookmark_name="${3:?Error: bookmark_name required}"
  local base_branch="${4:?Error: base_branch required}"
  local held

  held=$(jj_at "$workspace_path" bookmark list -r @ "exact:${bookmark_name}" -T 'name ++ "\n"' 2>/dev/null || true)
  if [[ -z "$held" ]]; then
    echo -e "${RED}Error: Existing workspace is not on expected bookmark: $bookmark_name${NC}" >&2
    echo -e "${RED}Clean up the stale workspace before rerunning this experiment.${NC}" >&2
    return 1
  fi

  echo -e "${YELLOW}Resetting existing experiment workspace to base: $bookmark_name -> $base_branch${NC}" >&2
  jj_at "$workspace_path" new "$base_branch" >/dev/null
  point_bookmark_at_working_copy "$workspace_path" "$bookmark_name"
  rm -f "$workspace_path/result.yaml"
}

copy_shared_into_workspace() {
  local workspace_path="${1:?Error: workspace_path required}"
  shift

  local f basename dir shared_file
  for f in "$DEFAULT_ROOT"/.env*; do
    if [[ -f "$f" ]]; then
      basename=$(basename "$f")
      if [[ "$basename" != ".env.example" ]]; then
        cp "$f" "$workspace_path/$basename"
      fi
    fi
  done

  for shared_file in "$@"; do
    if [[ -f "$DEFAULT_ROOT/$shared_file" ]]; then
      dir=$(dirname "$workspace_path/$shared_file")
      mkdir -p "$dir"
      cp "$DEFAULT_ROOT/$shared_file" "$workspace_path/$shared_file"
    elif [[ -d "$DEFAULT_ROOT/$shared_file" ]]; then
      dir=$(dirname "$workspace_path/$shared_file")
      mkdir -p "$dir"
      rm -rf "$workspace_path/$shared_file"
      cp -R "$DEFAULT_ROOT/$shared_file" "$workspace_path/$shared_file"
    fi
  done
}

create_workspace() {
  local spec_name="${1:?Error: spec_name required}"
  local exp_index="${2:?Error: exp_index required}"
  local base_branch="${3:?Error: base_branch required}"
  shift 3

  local padded_index
  padded_index=$(printf "%03d" "$exp_index")
  local workspace_name="optimize-${spec_name}-exp-${padded_index}"
  local bookmark_name
  bookmark_name=$(experiment_bookmark_name "$spec_name" "$padded_index")
  local workspace_path="$WORKSPACE_DIR/$workspace_name"
  local existing_root

  if [[ -d "$workspace_path" ]]; then
    if ! is_registered_workspace "$workspace_path" "$workspace_name"; then
      echo -e "${RED}Error: Existing path is not a registered JJ workspace: $workspace_path${NC}" >&2
      echo -e "${RED}Remove or repair that directory before rerunning the experiment.${NC}" >&2
      return 1
    fi

    echo -e "${YELLOW}Workspace already exists: $workspace_path${NC}" >&2
    reset_workspace_to_base "$workspace_path" "$workspace_name" "$bookmark_name" "$base_branch"
  else
    existing_root=$(workspace_root_for_name "$workspace_name" 2>/dev/null || true)
    if [[ -n "$existing_root" && "$existing_root" != "$workspace_path" ]]; then
      echo -e "${RED}Error: Existing experiment workspace is already checked out: $workspace_name ($existing_root)${NC}" >&2
      echo -e "${RED}Clean up the stale workspace before rerunning this experiment.${NC}" >&2
      return 1
    fi

    mkdir -p "$WORKSPACE_DIR"

    if ! jj_at "$DEFAULT_ROOT" workspace add --name "$workspace_name" --revision "$base_branch" "$workspace_path" >/dev/null; then
      if bookmark_exists "$bookmark_name"; then
        if bookmark_held_by_other_workspace "$bookmark_name" "$workspace_name"; then
          echo -e "${RED}Error: Existing experiment bookmark is already checked out: $bookmark_name${NC}" >&2
          echo -e "${RED}Clean up the stale workspace before rerunning this experiment.${NC}" >&2
          return 1
        fi

        echo -e "${YELLOW}Resetting existing experiment bookmark to base: $bookmark_name -> $base_branch${NC}" >&2
        jj_at "$DEFAULT_ROOT" bookmark set --allow-backwards "$bookmark_name" -r "$base_branch" >/dev/null
        jj_at "$DEFAULT_ROOT" workspace add --name "$workspace_name" --revision "$bookmark_name" "$workspace_path" >/dev/null
      else
        echo -e "${RED}Error: Failed to create workspace $workspace_name from $base_branch${NC}" >&2
        return 1
      fi
    fi

    point_bookmark_at_working_copy "$workspace_path" "$bookmark_name"
  fi

  copy_shared_into_workspace "$workspace_path" "$@"
  echo "$workspace_path"
}

forget_and_remove_workspace() {
  local workspace_name="${1:?Error: workspace_name required}"
  local workspace_path="${2:?Error: workspace_path required}"

  if is_registered_workspace "$workspace_path" "$workspace_name" || workspace_root_for_name "$workspace_name" >/dev/null 2>&1; then
    jj_at "$DEFAULT_ROOT" workspace forget "$workspace_name" >/dev/null 2>&1 || true
  fi
  rm -rf "$workspace_path" 2>/dev/null || true
}

cleanup_workspace() {
  local spec_name="${1:?Error: spec_name required}"
  local exp_index="${2:?Error: exp_index required}"

  local padded_index
  padded_index=$(printf "%03d" "$exp_index")
  local workspace_name="optimize-${spec_name}-exp-${padded_index}"
  local bookmark_name
  bookmark_name=$(experiment_bookmark_name "$spec_name" "$padded_index")
  local workspace_path="$WORKSPACE_DIR/$workspace_name"

  forget_and_remove_workspace "$workspace_name" "$workspace_path"
  jj_at "$DEFAULT_ROOT" bookmark delete "exact:${bookmark_name}" >/dev/null 2>&1 || true

  echo -e "${GREEN}Cleaned up: $workspace_name${NC}" >&2
}

cleanup_all() {
  local spec_name="${1:?Error: spec_name required}"
  local prefix="optimize-${spec_name}-exp-"
  local count=0
  local name root index_str bookmark_name

  while IFS= read -r name; do
    [[ -z "$name" ]] && continue
    case "$name" in
      "$prefix"*)
        root=$(workspace_root_for_name "$name" 2>/dev/null || true)
        index_str="${name#$prefix}"
        bookmark_name=$(experiment_bookmark_name "$spec_name" "$index_str")
        if [[ -n "$root" ]]; then
          forget_and_remove_workspace "$name" "$root"
        else
          jj_at "$DEFAULT_ROOT" workspace forget "$name" >/dev/null 2>&1 || true
        fi
        jj_at "$DEFAULT_ROOT" bookmark delete "exact:${bookmark_name}" >/dev/null 2>&1 || true
        count=$((count + 1))
        ;;
    esac
  done < <(list_workspace_names)

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

count_workspaces() {
  local count=0
  local name root

  while IFS= read -r name; do
    [[ -z "$name" ]] && continue
    root=$(workspace_root_for_name "$name" 2>/dev/null) || continue
    case "$root" in
      "$WORKSPACE_DIR"/*)
        count=$((count + 1))
        ;;
    esac
  done < <(list_workspace_names)
  echo "$count"
}

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
  experiment-worktree.sh create <spec_name> <exp_index> <base_branch> [shared_file ...]
  experiment-worktree.sh cleanup <spec_name> <exp_index>
  experiment-worktree.sh cleanup-all <spec_name>
  experiment-worktree.sh count

Commands:
  create       Create an experiment JJ workspace with copied shared files
  cleanup      Remove a single experiment workspace and its bookmark
  cleanup-all  Remove all experiment workspaces for a spec
  count        Count total active experiment workspaces (for budget checking)

Workspaces: .worktrees/optimize-<spec>-exp-<NNN>/
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
