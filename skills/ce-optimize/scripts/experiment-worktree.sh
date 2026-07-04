#!/bin/bash

# Experiment Worktree Manager
# Creates, cleans up, and manages worktrees for optimization experiments.
# Each experiment gets an isolated worktree with copied shared resources.
#
# Usage:
#   experiment-worktree.sh create <spec_name> <exp_index> <base_bookmark> [shared_file ...]
#   experiment-worktree.sh cleanup <spec_name> <exp_index>
#   experiment-worktree.sh cleanup-all <spec_name>
#   experiment-worktree.sh count
#
# Worktrees are created at: .worktrees/optimize-<spec>-exp-<NNN>/
# Bookmarks are named: optimize-exp/<spec>/exp-<NNN>

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

REPO_ROOT=$(jj workspace root 2>/dev/null) || {
  echo -e "${RED}Error: Not in a jj workspace${NC}" >&2
  exit 1
}

WORKTREE_DIR="$REPO_ROOT/.worktrees"

experiment_bookmark_name() {
  local spec_name="${1:?Error: spec_name required}"
  local padded_index="${2:?Error: padded_index required}"

  # Keep experiment refs outside optimize/<spec> so they do not collide
  # with the long-lived optimization bookmark namespace.
  echo "optimize-exp/${spec_name}/exp-${padded_index}"
}

ensure_worktree_exclude() {
  # Repository ignore configuration is project-owned; do not mutate it here.
  return 0
}

is_registered_worktree() {
  local worktree_path="${1:?Error: worktree_path required}"

  jj workspace list --template 'root ++ "\n"' | awk -v target="$worktree_path" '
    $0 == target { found = 1 }
    END { exit(found ? 0 : 1) }
  '
}

remove_existing_workspace() {
  local worktree_path="${1:?Error: worktree_path required}"
  local workspace_name="${2:?Error: workspace_name required}"

  echo -e "${YELLOW}Removing existing experiment workspace: $worktree_path${NC}" >&2
  jj workspace forget "$workspace_name" >/dev/null 2>&1 || true
  rm -rf "$worktree_path"
}

# Create an experiment worktree
create_worktree() {
  local spec_name="${1:?Error: spec_name required}"
  local exp_index="${2:?Error: exp_index required}"
  local base_bookmark="${3:?Error: base_bookmark required}"
  shift 3

  local padded_index
  padded_index=$(printf "%03d" "$exp_index")
  local worktree_name="optimize-${spec_name}-exp-${padded_index}"
  local workspace_name="optimize-${spec_name}-exp-${padded_index}"
  local bookmark_name
  bookmark_name=$(experiment_bookmark_name "$spec_name" "$padded_index")
  local worktree_path="$WORKTREE_DIR/$worktree_name"

  # Check if worktree already exists
  if [[ -d "$worktree_path" ]]; then
    if ! jj -R "$worktree_path" workspace root >/dev/null 2>&1 || \
       ! is_registered_worktree "$worktree_path"; then
      echo -e "${RED}Error: Existing path is not a valid registered jj workspace: $worktree_path${NC}" >&2
      echo -e "${RED}Remove or repair that directory before rerunning the experiment.${NC}" >&2
      return 1
    fi

    echo -e "${YELLOW}Worktree already exists: $worktree_path${NC}" >&2
    remove_existing_workspace "$worktree_path" "$workspace_name"
  fi

  mkdir -p "$WORKTREE_DIR"
  ensure_worktree_exclude

  if jj workspace list --template 'name ++ "\n"' | grep -qx "$workspace_name"; then
    jj workspace forget "$workspace_name" >/dev/null 2>&1 || true
  fi
  jj bookmark delete "$bookmark_name" >/dev/null 2>&1 || true

  if ! jj workspace add --name "$workspace_name" "$worktree_path" -r "$base_bookmark" >/dev/null 2>&1; then
    echo -e "${RED}Error: Failed to create workspace $workspace_name from $base_bookmark${NC}" >&2
    return 1
  fi
  jj -R "$worktree_path" bookmark set "$bookmark_name" -r @ >/dev/null

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

# Clean up a single experiment worktree
cleanup_worktree() {
  local spec_name="${1:?Error: spec_name required}"
  local exp_index="${2:?Error: exp_index required}"

  local padded_index
  padded_index=$(printf "%03d" "$exp_index")
  local worktree_name="optimize-${spec_name}-exp-${padded_index}"
  local workspace_name="optimize-${spec_name}-exp-${padded_index}"
  local bookmark_name
  bookmark_name=$(experiment_bookmark_name "$spec_name" "$padded_index")
  local worktree_path="$WORKTREE_DIR/$worktree_name"

  if [[ -d "$worktree_path" ]]; then
    jj workspace forget "$workspace_name" >/dev/null 2>&1 || true
    rm -rf "$worktree_path" 2>/dev/null || true
  fi

  # Delete the experiment bookmark.
  jj bookmark delete "$bookmark_name" >/dev/null 2>&1 || true

  echo -e "${GREEN}Cleaned up: $worktree_name${NC}" >&2
}

# Clean up all experiment worktrees for a spec
cleanup_all() {
  local spec_name="${1:?Error: spec_name required}"
  local prefix="optimize-${spec_name}-exp-"
  local count=0

  if [[ ! -d "$WORKTREE_DIR" ]]; then
    echo -e "${YELLOW}No worktrees directory found${NC}" >&2
    return 0
  fi

  for worktree_path in "$WORKTREE_DIR"/${prefix}*; do
    if [[ -d "$worktree_path" ]]; then
      local worktree_name
      worktree_name=$(basename "$worktree_path")
      # Extract index from name
      local index_str="${worktree_name#$prefix}"

      jj workspace forget "$worktree_name" >/dev/null 2>&1 || true
      rm -rf "$worktree_path" 2>/dev/null || true

      # Delete the bookmark.
      local bookmark_name
      bookmark_name=$(experiment_bookmark_name "$spec_name" "$index_str")
      jj bookmark delete "$bookmark_name" >/dev/null 2>&1 || true

      count=$((count + 1))
    fi
  done

  # Clean up empty worktree directory
  if [[ -d "$WORKTREE_DIR" ]] && [[ -z "$(ls -A "$WORKTREE_DIR" 2>/dev/null)" ]]; then
    rmdir "$WORKTREE_DIR" 2>/dev/null || true
  fi

  echo -e "${GREEN}Cleaned up $count experiment worktree(s) for $spec_name${NC}" >&2
}

# Count total worktrees (for budget check)
count_worktrees() {
  local count=0
  if [[ -d "$WORKTREE_DIR" ]]; then
    for worktree_path in "$WORKTREE_DIR"/*; do
      if [[ -d "$worktree_path" ]] && jj -R "$worktree_path" workspace root >/dev/null 2>&1; then
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
Experiment Worktree Manager

Usage:
  experiment-worktree.sh create <spec_name> <exp_index> <base_bookmark> [shared_file ...]
  experiment-worktree.sh cleanup <spec_name> <exp_index>
  experiment-worktree.sh cleanup-all <spec_name>
  experiment-worktree.sh count

Commands:
  create       Create an experiment worktree with copied shared files
  cleanup      Remove a single experiment workspace and its bookmark
  cleanup-all  Remove all experiment workspaces for a spec
  count        Count total active worktrees (for budget checking)

Worktrees:  .worktrees/optimize-<spec>-exp-<NNN>/
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
