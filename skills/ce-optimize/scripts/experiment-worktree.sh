#!/bin/bash

# Experiment Workspace Manager
# Creates, cleans up, and manages JJ workspaces for optimization experiments.
# Each experiment gets an isolated workspace with copied shared resources.
#
# Usage:
#   experiment-worktree.sh create <spec_name> <exp_index> <base_rev> [shared_file ...]
#   experiment-worktree.sh cleanup <spec_name> <exp_index>
#   experiment-worktree.sh cleanup-all <spec_name>
#   experiment-worktree.sh count
#
# Workspaces are created at the legacy path: .worktrees/optimize-<spec>-exp-<NNN>/
# Workspace names are: optimize-<spec>-exp-<NNN>

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

REPO_ROOT=$(jj workspace root 2>/dev/null) || {
  echo -e "${RED}Error: Not in a JJ workspace${NC}" >&2
  exit 1
}

WORKTREE_DIR="$REPO_ROOT/.worktrees"

workspace_name() {
  local spec_name="${1:?Error: spec_name required}"
  local padded_index="${2:?Error: padded_index required}"

  echo "optimize-${spec_name}-exp-${padded_index}"
}

workspace_path_for() {
  local spec_name="${1:?Error: spec_name required}"
  local padded_index="${2:?Error: padded_index required}"

  echo "$WORKTREE_DIR/$(workspace_name "$spec_name" "$padded_index")"
}

forget_workspace() {
  local name="${1:?Error: workspace name required}"

  jj workspace forget "$name" >/dev/null 2>&1 || true
}

# Create an experiment workspace
create_worktree() {
  local spec_name="${1:?Error: spec_name required}"
  local exp_index="${2:?Error: exp_index required}"
  local base_rev="${3:?Error: base_rev required}"
  shift 3

  local padded_index
  padded_index=$(printf "%03d" "$exp_index")
  local name
  name=$(workspace_name "$spec_name" "$padded_index")
  local worktree_path
  worktree_path=$(workspace_path_for "$spec_name" "$padded_index")

  mkdir -p "$WORKTREE_DIR"

  if [[ -d "$worktree_path" ]]; then
    echo -e "${YELLOW}Workspace already exists; recreating from base: $worktree_path${NC}" >&2
    forget_workspace "$name"
    rm -rf "$worktree_path"
  fi

  if ! jj workspace add --name "$name" --revision "$base_rev" "$worktree_path" >/dev/null 2>&1; then
    echo -e "${RED}Error: Failed to create JJ workspace $name from $base_rev${NC}" >&2
    return 1
  fi

  jj -R "$worktree_path" describe -m "optimize experiment $spec_name #$padded_index" >/dev/null 2>&1 || true

  # Copy .env files from main repo
  for f in "$REPO_ROOT"/.env*; do
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
    if [[ -f "$REPO_ROOT/$shared_file" ]]; then
      local dir
      dir=$(dirname "$worktree_path/$shared_file")
      mkdir -p "$dir"
      cp "$REPO_ROOT/$shared_file" "$worktree_path/$shared_file"
    elif [[ -d "$REPO_ROOT/$shared_file" ]]; then
      local dir
      dir=$(dirname "$worktree_path/$shared_file")
      mkdir -p "$dir"
      rm -rf "$worktree_path/$shared_file"
      cp -R "$REPO_ROOT/$shared_file" "$worktree_path/$shared_file"
    fi
  done

  echo "$worktree_path"
}

# Clean up a single experiment workspace
cleanup_worktree() {
  local spec_name="${1:?Error: spec_name required}"
  local exp_index="${2:?Error: exp_index required}"

  local padded_index
  padded_index=$(printf "%03d" "$exp_index")
  local name
  name=$(workspace_name "$spec_name" "$padded_index")
  local worktree_path
  worktree_path=$(workspace_path_for "$spec_name" "$padded_index")

  forget_workspace "$name"
  rm -rf "$worktree_path" 2>/dev/null || true

  echo -e "${GREEN}Cleaned up: $name${NC}" >&2
}

# Clean up all experiment workspaces for a spec
cleanup_all() {
  local spec_name="${1:?Error: spec_name required}"
  local prefix="optimize-${spec_name}-exp-"
  local count=0

  if [[ ! -d "$WORKTREE_DIR" ]]; then
    echo -e "${YELLOW}No workspaces directory found${NC}" >&2
    return 0
  fi

  for worktree_path in "$WORKTREE_DIR"/${prefix}*; do
    if [[ -d "$worktree_path" ]]; then
      local name
      name=$(basename "$worktree_path")
      forget_workspace "$name"
      rm -rf "$worktree_path" 2>/dev/null || true
      count=$((count + 1))
    fi
  done

  if [[ -d "$WORKTREE_DIR" ]] && [[ -z "$(ls -A "$WORKTREE_DIR" 2>/dev/null)" ]]; then
    rmdir "$WORKTREE_DIR" 2>/dev/null || true
  fi

  echo -e "${GREEN}Cleaned up $count experiment workspace(s) for $spec_name${NC}" >&2
}

# Count total workspaces (for budget check)
count_worktrees() {
  local count=0
  if [[ -d "$WORKTREE_DIR" ]]; then
    for worktree_path in "$WORKTREE_DIR"/*; do
      if [[ -d "$worktree_path" ]] && [[ -d "$worktree_path/.jj" ]]; then
        count=$((count + 1))
      fi
    done
  fi
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

Note: the script name and .worktrees directory are legacy compatibility names;
the backend creates JJ workspaces.

Usage:
  experiment-worktree.sh create <spec_name> <exp_index> <base_rev> [shared_file ...]
  experiment-worktree.sh cleanup <spec_name> <exp_index>
  experiment-worktree.sh cleanup-all <spec_name>
  experiment-worktree.sh count

Commands:
  create       Create an experiment JJ workspace with copied shared files
  cleanup      Remove a single experiment workspace
  cleanup-all  Remove all experiment workspaces for a spec
  count        Count total active experiment workspaces (for budget checking)
EOF
      ;;
    *)
      echo -e "${RED}Unknown command: $command${NC}" >&2
      exit 1
      ;;
  esac
}

main "$@"
