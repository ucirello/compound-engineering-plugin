#!/bin/bash

# Experiment Workspace Manager
# Creates, cleans up, and manages JJ workspaces for optimization experiments.
# Each experiment gets an isolated workspace with copied shared resources.
#
# Usage:
#   experiment-worktree.sh create <spec_name> <exp_index> <base_bookmark> [shared_file ...]
#   experiment-worktree.sh cleanup <spec_name> <exp_index>
#   experiment-worktree.sh cleanup-all <spec_name>
#   experiment-worktree.sh count
#
# Workspaces are created at: .worktrees/optimize-<spec>-exp-<NNN>/
# Bookmarks are named: optimize-exp/<spec>/exp-<NNN>
#
# All jj invocations use cwd = the target workspace's absolute root.
# Never read or parse files inside .jj/.

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

JJ_ROOT=$(jj workspace root 2>/dev/null) || {
  echo -e "${RED}Error: Not in a jj workspace${NC}" >&2
  exit 1
}

WORKTREE_DIR="$JJ_ROOT/.worktrees"

jj_at() {
  local cwd="${1:?Error: cwd required}"
  shift
  (cd "$cwd" && jj --no-pager "$@")
}

experiment_branch_name() {
  local spec_name="${1:?Error: spec_name required}"
  local padded_index="${2:?Error: padded_index required}"

  # Keep experiment refs outside optimize/<spec> so they do not collide
  # with the long-lived optimization bookmark namespace.
  echo "optimize-exp/${spec_name}/exp-${padded_index}"
}

bookmark_exists() {
  local bookmark_name="${1:?Error: bookmark_name required}"
  local cwd="${2:-$JJ_ROOT}"
  local out
  out=$(jj_at "$cwd" bookmark list "exact:${bookmark_name}" 2>/dev/null || true)
  [[ -n "$out" ]]
}

is_registered_workspace() {
  local workspace_name="${1:?Error: workspace_name required}"
  local expected_path="${2:?Error: expected_path required}"
  local actual
  actual=$(jj_at "$JJ_ROOT" workspace root --name "$workspace_name" 2>/dev/null) || return 1
  [[ "$actual" == "$expected_path" ]]
}

reset_workspace_to_base() {
  local workspace_path="${1:?Error: workspace_path required}"
  local workspace_name="${2:?Error: workspace_name required}"
  local branch_name="${3:?Error: branch_name required}"
  local base_bookmark="${4:?Error: base_bookmark required}"

  if ! is_registered_workspace "$workspace_name" "$workspace_path"; then
    echo -e "${RED}Error: Existing path is not a registered jj workspace: $workspace_path${NC}" >&2
    echo -e "${RED}Clean up the stale workspace before rerunning this experiment.${NC}" >&2
    return 1
  fi

  echo -e "${YELLOW}Resetting existing experiment workspace to base: $branch_name -> $base_bookmark${NC}" >&2
  jj_at "$workspace_path" new "$base_bookmark"
  point_experiment_bookmark "$workspace_path" "$branch_name"
}

point_experiment_bookmark() {
  local workspace_path="${1:?Error: workspace_path required}"
  local branch_name="${2:?Error: branch_name required}"

  if bookmark_exists "$branch_name" "$workspace_path"; then
    jj_at "$workspace_path" bookmark set "$branch_name" --allow-backwards -r @ >/dev/null
  else
    jj_at "$workspace_path" bookmark create "$branch_name" -r @ >/dev/null
  fi
}

# Create an experiment workspace
create_worktree() {
  local spec_name="${1:?Error: spec_name required}"
  local exp_index="${2:?Error: exp_index required}"
  local base_bookmark="${3:?Error: base_bookmark required}"
  shift 3

  local padded_index
  padded_index=$(printf "%03d" "$exp_index")
  local worktree_name="optimize-${spec_name}-exp-${padded_index}"
  local branch_name
  branch_name=$(experiment_branch_name "$spec_name" "$padded_index")
  local worktree_path="$WORKTREE_DIR/$worktree_name"

  if [[ -d "$worktree_path" ]]; then
    if ! is_registered_workspace "$worktree_name" "$worktree_path"; then
      echo -e "${RED}Error: Existing path is not a valid registered jj workspace: $worktree_path${NC}" >&2
      echo -e "${RED}Remove or repair that directory before rerunning the experiment.${NC}" >&2
      return 1
    fi

    echo -e "${YELLOW}Workspace already exists: $worktree_path${NC}" >&2
    reset_workspace_to_base "$worktree_path" "$worktree_name" "$branch_name" "$base_bookmark"
  else
    mkdir -p "$WORKTREE_DIR"

    if ! jj_at "$JJ_ROOT" workspace add --name "$worktree_name" -r "$base_bookmark" "$worktree_path"; then
      if is_registered_workspace "$worktree_name" "$worktree_path"; then
        echo -e "${YELLOW}Workspace already exists: $worktree_path${NC}" >&2
        reset_workspace_to_base "$worktree_path" "$worktree_name" "$branch_name" "$base_bookmark"
      else
        local existing_root
        existing_root=$(jj_at "$JJ_ROOT" workspace root --name "$worktree_name" 2>/dev/null || true)
        if [[ -n "$existing_root" ]]; then
          echo -e "${RED}Error: Existing experiment workspace is already registered: $worktree_name ($existing_root)${NC}" >&2
          echo -e "${RED}Clean up the stale workspace before rerunning this experiment.${NC}" >&2
          return 1
        fi
        echo -e "${RED}Error: Failed to create workspace $worktree_name from $base_bookmark${NC}" >&2
        return 1
      fi
    else
      point_experiment_bookmark "$worktree_path" "$branch_name"
    fi
  fi

  # Copy .env files from main workspace
  for f in "$JJ_ROOT"/.env*; do
    if [[ -f "$f" ]]; then
      local basename
      basename=$(basename "$f")
      if [[ "$basename" != ".env.example" ]]; then
        cp "$f" "$worktree_path/$basename"
      fi
    fi
  done

  # Copy shared files
  for shared_file in "$@"; do
    if [[ -f "$JJ_ROOT/$shared_file" ]]; then
      local dir
      dir=$(dirname "$worktree_path/$shared_file")
      mkdir -p "$dir"
      cp "$JJ_ROOT/$shared_file" "$worktree_path/$shared_file"
    elif [[ -d "$JJ_ROOT/$shared_file" ]]; then
      local dir
      dir=$(dirname "$worktree_path/$shared_file")
      mkdir -p "$dir"
      rm -rf "$worktree_path/$shared_file"
      cp -R "$JJ_ROOT/$shared_file" "$worktree_path/$shared_file"
    fi
  done

  echo "$worktree_path"
}

forget_and_remove_workspace() {
  local workspace_name="${1:?Error: workspace_name required}"
  local workspace_path="${2:-}"
  local root

  root=$(jj_at "$JJ_ROOT" workspace root --name "$workspace_name" 2>/dev/null || true)
  if [[ -z "$root" && -n "$workspace_path" ]]; then
    root="$workspace_path"
  fi

  if [[ -n "$workspace_name" ]]; then
    jj_at "$JJ_ROOT" workspace forget "$workspace_name" 2>/dev/null || true
  fi
  if [[ -n "$root" && -d "$root" ]]; then
    rm -rf "$root" 2>/dev/null || true
  fi
}

# Clean up a single experiment workspace
cleanup_worktree() {
  local spec_name="${1:?Error: spec_name required}"
  local exp_index="${2:?Error: exp_index required}"

  local padded_index
  padded_index=$(printf "%03d" "$exp_index")
  local worktree_name="optimize-${spec_name}-exp-${padded_index}"
  local branch_name
  branch_name=$(experiment_branch_name "$spec_name" "$padded_index")
  local worktree_path="$WORKTREE_DIR/$worktree_name"

  forget_and_remove_workspace "$worktree_name" "$worktree_path"

  jj_at "$JJ_ROOT" bookmark delete "$branch_name" 2>/dev/null || true

  echo -e "${GREEN}Cleaned up: $worktree_name${NC}" >&2
}

# Clean up all experiment workspaces for a spec
cleanup_all() {
  local spec_name="${1:?Error: spec_name required}"
  local prefix="optimize-${spec_name}-exp-"
  local count=0
  local names name root index_str branch_name

  names=$(jj_at "$JJ_ROOT" workspace list -T 'name ++ "\n"' 2>/dev/null || true)

  while IFS= read -r name; do
    [[ -z "$name" ]] && continue
    [[ "$name" == "$prefix"* ]] || continue

    root=$(jj_at "$JJ_ROOT" workspace root --name "$name" 2>/dev/null || true)
    forget_and_remove_workspace "$name" "$root"

    index_str="${name#$prefix}"
    branch_name=$(experiment_branch_name "$spec_name" "$index_str")
    jj_at "$JJ_ROOT" bookmark delete "$branch_name" 2>/dev/null || true

    count=$((count + 1))
  done <<< "$names"

  if [[ -d "$WORKTREE_DIR" ]]; then
    for leftover in "$WORKTREE_DIR"/${prefix}*; do
      if [[ -d "$leftover" ]]; then
        rm -rf "$leftover" 2>/dev/null || true
      fi
    done
    if [[ -z "$(ls -A "$WORKTREE_DIR" 2>/dev/null)" ]]; then
      rmdir "$WORKTREE_DIR" 2>/dev/null || true
    fi
  fi

  echo -e "${GREEN}Cleaned up $count experiment workspace(s) for $spec_name${NC}" >&2
}

# Count experiment workspaces under .worktrees (for budget check)
count_worktrees() {
  local count=0
  local names name root
  names=$(jj_at "$JJ_ROOT" workspace list -T 'name ++ "\n"' 2>/dev/null || true)
  while IFS= read -r name; do
    [[ -z "$name" ]] && continue
    root=$(jj_at "$JJ_ROOT" workspace root --name "$name" 2>/dev/null || true)
    [[ -n "$root" ]] || continue
    case "$root" in
      "$WORKTREE_DIR"/*)
        count=$((count + 1))
        ;;
    esac
  done <<< "$names"
  echo "$count"
}

# Main
main() {
  local command="${1:-help}"

  case "$command" in
    create)
      shift
      create_worktree "$@"
      ;;
    cleanup)
      shift
      cleanup_worktree "$@"
      ;;
    cleanup-all)
      shift
      cleanup_all "$@"
      ;;
    count)
      count_worktrees
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
