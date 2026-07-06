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
# Workspaces are created at: .workspaces/optimize-<spec>-exp-<NNN>/
# Bookmarks are named: optimize-exp/<spec>/exp-<NNN>

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

WORKSPACE_ROOT=$(jj workspace root 2>/dev/null) || {
  echo -e "${RED}Error: Not in a JJ workspace${NC}" >&2
  exit 1
}

WORKSPACE_DIR="$WORKSPACE_ROOT/.workspaces"

experiment_bookmark_name() {
  local spec_name="${1:?Error: spec_name required}"
  local padded_index="${2:?Error: padded_index required}"

  # Keep experiment refs outside optimize/<spec> so they do not collide
  # with the long-lived optimization bookmark namespace.
  echo "optimize-exp/${spec_name}/exp-${padded_index}"
}

ensure_workspace_ignore() {
  local ignore_file="$WORKSPACE_ROOT/.ignore"
  if ! grep -q '^\.workspaces/$' "$ignore_file" 2>/dev/null; then
    printf '\n.workspaces/\n' >> "$ignore_file"
  fi
}

workspace_exists() {
  local workspace_name="${1:?Error: workspace_name required}"
  jj workspace list | awk -v target="$workspace_name" '$1 == target { found = 1 } END { exit(found ? 0 : 1) }'
}

copy_shared_resources() {
  local workspace_path="${1:?Error: workspace_path required}"
  shift

  for f in "$WORKSPACE_ROOT"/.env*; do
    if [[ -f "$f" ]]; then
      local basename
      basename=$(basename "$f")
      if [[ "$basename" != ".env.example" ]]; then
        cp "$f" "$workspace_path/$basename"
      fi
    fi
  done

  for shared_file in "$@"; do
    if [[ -f "$WORKSPACE_ROOT/$shared_file" ]]; then
      local dir
      dir=$(dirname "$workspace_path/$shared_file")
      mkdir -p "$dir"
      cp "$WORKSPACE_ROOT/$shared_file" "$workspace_path/$shared_file"
    elif [[ -d "$WORKSPACE_ROOT/$shared_file" ]]; then
      local dir
      dir=$(dirname "$workspace_path/$shared_file")
      mkdir -p "$dir"
      rm -rf "$workspace_path/$shared_file"
      cp -R "$WORKSPACE_ROOT/$shared_file" "$workspace_path/$shared_file"
    fi
  done
}

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

  if [[ -d "$workspace_path" ]] || workspace_exists "$workspace_name"; then
    echo -e "${RED}Error: Experiment workspace already exists: $workspace_name${NC}" >&2
    echo -e "${RED}Clean it up before rerunning this experiment.${NC}" >&2
    return 1
  fi

  mkdir -p "$WORKSPACE_DIR"
  ensure_workspace_ignore

  jj workspace add --name "$workspace_name" --revision "$base_rev" "$workspace_path" >/dev/null
  jj --repository "$workspace_path" bookmark create "$bookmark_name" -r @ >/dev/null

  copy_shared_resources "$workspace_path" "$@"
  echo "$workspace_path"
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

  jj workspace forget "$workspace_name" 2>/dev/null || true
  jj bookmark delete "$bookmark_name" 2>/dev/null || true
  rm -rf "$workspace_path" 2>/dev/null || true

  echo -e "${GREEN}Cleaned up: $workspace_name${NC}" >&2
}

cleanup_all() {
  local spec_name="${1:?Error: spec_name required}"
  local prefix="optimize-${spec_name}-exp-"
  local count=0

  if [[ -d "$WORKSPACE_DIR" ]]; then
    for workspace_path in "$WORKSPACE_DIR"/${prefix}*; do
      if [[ -d "$workspace_path" ]]; then
        local workspace_name
        workspace_name=$(basename "$workspace_path")
        local index_str="${workspace_name#$prefix}"
        cleanup_workspace "$spec_name" "$((10#$index_str))" >/dev/null || true
        count=$((count + 1))
      fi
    done
  fi

  if [[ -d "$WORKSPACE_DIR" ]] && [[ -z "$(ls -A "$WORKSPACE_DIR" 2>/dev/null)" ]]; then
    rmdir "$WORKSPACE_DIR" 2>/dev/null || true
  fi

  echo -e "${GREEN}Cleaned up $count experiment workspace(s) for $spec_name${NC}" >&2
}

count_workspaces() {
  local count=0
  if [[ -d "$WORKSPACE_DIR" ]]; then
    for workspace_path in "$WORKSPACE_DIR"/*; do
      if [[ -d "$workspace_path" ]] && [[ -d "$workspace_path/.jj" ]]; then
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
  create       Create an experiment JJ workspace with copied shared files
  cleanup      Remove a single experiment JJ workspace and bookmark
  cleanup-all  Remove all experiment JJ workspaces for a spec
  count        Count total active JJ workspaces (for budget checking)

Workspaces:  .workspaces/optimize-<spec>-exp-<NNN>/
Bookmarks:   optimize-exp/<spec>/exp-<NNN>
EOF
      ;;
    *)
      echo -e "${RED}Unknown command: $command${NC}" >&2
      exit 1
      ;;
  esac
}

main "$@"
