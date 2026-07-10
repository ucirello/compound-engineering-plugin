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
# Workspaces are created at: .worktrees/optimize-<spec>-exp-<NNN>/
# Bookmarks are named: optimize-exp/<spec>/exp-<NNN>

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

JJ_ROOT=$(jj root 2>/dev/null) || {
  echo -e "${RED}Error: Not in a JJ repository${NC}" >&2
  exit 1
}

WORKSPACE_DIR="$JJ_ROOT/.worktrees"

experiment_bookmark_name() {
  local spec_name="${1:?Error: spec_name required}"
  local padded_index="${2:?Error: padded_index required}"

  # Keep experiment refs outside optimize/<spec> so they do not collide
  # with the long-lived optimization bookmark namespace.
  echo "optimize-exp/${spec_name}/exp-${padded_index}"
}

ensure_workspace_exclude() {
  local ignore_file="$JJ_ROOT/.gitignore"

  if [[ ! -f "$ignore_file" ]] || ! grep -q "^\.worktrees/$" "$ignore_file" 2>/dev/null; then
    printf '\n.worktrees/\n' >> "$ignore_file"
  fi
}

is_registered_workspace() {
  local workspace_path="${1:?Error: workspace_path required}"

  jj workspace list 2>/dev/null | grep -Fq "$workspace_path"
}

reset_workspace_to_base() {
  local workspace_path="${1:?Error: workspace_path required}"
  local bookmark_name="${2:?Error: bookmark_name required}"
  local base_rev="${3:?Error: base_rev required}"

  echo -e "${YELLOW}Resetting existing experiment workspace to base: $bookmark_name -> $base_rev${NC}" >&2
  jj --repository "$workspace_path" abandon @ >/dev/null 2>&1 || true
  jj --repository "$workspace_path" new "$base_rev" >/dev/null
  jj --repository "$workspace_path" bookmark set "$bookmark_name" -r @ >/dev/null
}

# Create an experiment workspace.
create_workspace() {
  local spec_name="${1:?Error: spec_name required}"
  local exp_index="${2:?Error: exp_index required}"
  local base_rev="${3:?Error: base_rev required}"
  shift 3

  local padded_index
  padded_index=$(printf "%03d" "$exp_index")
  local workspace_name="optimize-${spec_name}-exp-${padded_index}"
  local bookmark_name
  bookmark_name=$(experiment_bookmark_name "$spec_name" "$padded_index")
  local workspace_path="$WORKSPACE_DIR/$workspace_name"

  if [[ -d "$workspace_path" ]]; then
    if ! is_registered_workspace "$workspace_path"; then
      echo -e "${RED}Error: Existing path is not a registered JJ workspace: $workspace_path${NC}" >&2
      echo -e "${RED}Remove or repair that directory before rerunning the experiment.${NC}" >&2
      return 1
    fi

    echo -e "${YELLOW}Workspace already exists: $workspace_path${NC}" >&2
    reset_workspace_to_base "$workspace_path" "$bookmark_name" "$base_rev"
  else
    mkdir -p "$WORKSPACE_DIR"
    ensure_workspace_exclude

    jj workspace add --name "$workspace_name" --revision "$base_rev" "$workspace_path" >/dev/null
    jj --repository "$workspace_path" bookmark set "$bookmark_name" -r @ >/dev/null
  fi

  # Copy .env files from main repo.
  for f in "$JJ_ROOT"/.env*; do
    if [[ -f "$f" ]]; then
      local basename
      basename=$(basename "$f")
      if [[ "$basename" != ".env.example" ]]; then
        cp "$f" "$workspace_path/$basename"
      fi
    fi
  done

  # Copy shared files.
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

  echo "$workspace_path"
}

# Clean up a single experiment workspace.
cleanup_workspace() {
  local spec_name="${1:?Error: spec_name required}"
  local exp_index="${2:?Error: exp_index required}"

  local padded_index
  padded_index=$(printf "%03d" "$exp_index")
  local workspace_name="optimize-${spec_name}-exp-${padded_index}"
  local bookmark_name
  bookmark_name=$(experiment_bookmark_name "$spec_name" "$padded_index")
  local workspace_path="$WORKSPACE_DIR/$workspace_name"

  jj workspace forget "$workspace_name" 2>/dev/null || true
  rm -rf "$workspace_path" 2>/dev/null || true
  jj bookmark delete "$bookmark_name" 2>/dev/null || true

  echo -e "${GREEN}Cleaned up: $workspace_name${NC}" >&2
}

# Clean up all experiment workspaces for a spec.
cleanup_all() {
  local spec_name="${1:?Error: spec_name required}"
  local prefix="optimize-${spec_name}-exp-"
  local count=0

  if [[ ! -d "$WORKSPACE_DIR" ]]; then
    echo -e "${YELLOW}No workspaces directory found${NC}" >&2
    return 0
  fi

  for workspace_path in "$WORKSPACE_DIR"/${prefix}*; do
    if [[ -d "$workspace_path" ]]; then
      local workspace_name
      workspace_name=$(basename "$workspace_path")
      local index_str="${workspace_name#$prefix}"
      local bookmark_name
      bookmark_name=$(experiment_bookmark_name "$spec_name" "$index_str")

      jj workspace forget "$workspace_name" 2>/dev/null || true
      rm -rf "$workspace_path" 2>/dev/null || true
      jj bookmark delete "$bookmark_name" 2>/dev/null || true

      count=$((count + 1))
    fi
  done

  if [[ -d "$WORKSPACE_DIR" ]] && [[ -z "$(ls -A "$WORKSPACE_DIR" 2>/dev/null)" ]]; then
    rmdir "$WORKSPACE_DIR" 2>/dev/null || true
  fi

  echo -e "${GREEN}Cleaned up $count experiment workspace(s) for $spec_name${NC}" >&2
}

# Count total workspaces (for budget check).
count_workspaces() {
  local count=0
  if [[ -d "$WORKSPACE_DIR" ]]; then
    for workspace_path in "$WORKSPACE_DIR"/*; do
      if [[ -d "$workspace_path" ]] && is_registered_workspace "$workspace_path"; then
        count=$((count + 1))
      fi
    done
  fi
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
  experiment-worktree.sh create <spec_name> <exp_index> <base_rev> [shared_file ...]
  experiment-worktree.sh cleanup <spec_name> <exp_index>
  experiment-worktree.sh cleanup-all <spec_name>
  experiment-worktree.sh count

Commands:
  create       Create an experiment workspace with copied shared files
  cleanup      Remove a single experiment workspace and its bookmark
  cleanup-all  Remove all experiment workspaces for a spec
  count        Count total active workspaces (for budget checking)

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
