#!/bin/bash

# Experiment Workspace Manager
# Creates, cleans up, and manages Jujutsu workspaces for optimization experiments.
# Each experiment gets an isolated workspace with copied shared resources.
#
# Usage:
#   experiment-worktree.sh create <spec_name> <exp_index> <base_revision> [shared_file ...]
#   experiment-worktree.sh cleanup <spec_name> <exp_index>
#   experiment-worktree.sh cleanup-all <spec_name>
#   experiment-worktree.sh count
#
# Workspaces are created at: .tmp/rocketclaw/ce-optimize/workspaces/optimize-<spec>-exp-<NNN>/

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

WORKSPACE_ROOT=$(jj workspace root 2>/dev/null) || {
  echo -e "${RED}Error: Not in a Jujutsu workspace${NC}" >&2
  exit 1
}

WORKSPACE_DIR="$WORKSPACE_ROOT/.tmp/rocketclaw/ce-optimize/workspaces"

experiment_workspace_name() {
  local spec_name="${1:?Error: spec_name required}"
  local padded_index="${2:?Error: padded_index required}"

  echo "optimize-${spec_name}-exp-${padded_index}"
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
  local workspace_path="$WORKSPACE_DIR/$workspace_name"

  if [[ -e "$workspace_path" ]]; then
    if ! jj -R "$workspace_path" workspace root >/dev/null 2>&1; then
      echo -e "${RED}Error: Existing path is not a valid Jujutsu workspace: $workspace_path${NC}" >&2
      return 1
    fi
    echo -e "${YELLOW}Replacing stale experiment workspace: $workspace_name${NC}" >&2
    if ! jj -R "$WORKSPACE_ROOT" log -r "bookmarks() & $workspace_name@" --no-graph -T 'change_id' 2>/dev/null | grep -q .; then
      jj -R "$WORKSPACE_ROOT" abandon "$workspace_name@" >/dev/null 2>&1 || true
    fi
    jj -R "$WORKSPACE_ROOT" workspace forget "$workspace_name" >/dev/null 2>&1 || true
    rm -rf "$workspace_path"
  fi

  mkdir -p "$WORKSPACE_DIR"
  jj -R "$WORKSPACE_ROOT" workspace add --name "$workspace_name" -r "$base_revision" "$workspace_path" >/dev/null

  # Copy local environment files from the source workspace.
  for f in "$WORKSPACE_ROOT"/.env*; do
    if [[ -f "$f" ]]; then
      local basename
      basename=$(basename "$f")
      if [[ "$basename" != ".env.example" ]]; then
        cp "$f" "$workspace_path/$basename"
      fi
    fi
  done

  # Copy shared files
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
  local workspace_path="$WORKSPACE_DIR/$workspace_name"

  if ! jj -R "$WORKSPACE_ROOT" log -r "bookmarks() & $workspace_name@" --no-graph -T 'change_id' 2>/dev/null | grep -q .; then
    jj -R "$WORKSPACE_ROOT" abandon "$workspace_name@" >/dev/null 2>&1 || true
  fi
  jj -R "$WORKSPACE_ROOT" workspace forget "$workspace_name" >/dev/null 2>&1 || true
  rm -rf "$workspace_path"

  echo -e "${GREEN}Cleaned up: $workspace_name${NC}" >&2
}

# Clean up all experiment workspaces for a spec
cleanup_all() {
  local spec_name="${1:?Error: spec_name required}"
  local prefix="optimize-${spec_name}-exp-"
  local count=0

  if [[ ! -d "$WORKSPACE_DIR" ]]; then
    echo -e "${YELLOW}No experiment workspace directory found${NC}" >&2
    return 0
  fi

  for workspace_path in "$WORKSPACE_DIR"/${prefix}*; do
    if [[ -d "$workspace_path" ]]; then
      local workspace_name
      workspace_name=$(basename "$workspace_path")

      if ! jj -R "$WORKSPACE_ROOT" log -r "bookmarks() & $workspace_name@" --no-graph -T 'change_id' 2>/dev/null | grep -q .; then
        jj -R "$WORKSPACE_ROOT" abandon "$workspace_name@" >/dev/null 2>&1 || true
      fi
      jj -R "$WORKSPACE_ROOT" workspace forget "$workspace_name" >/dev/null 2>&1 || true
      rm -rf "$workspace_path"

      count=$((count + 1))
    fi
  done

  if [[ -d "$WORKSPACE_DIR" ]] && [[ -z "$(ls -A "$WORKSPACE_DIR" 2>/dev/null)" ]]; then
    rmdir "$WORKSPACE_DIR" 2>/dev/null || true
  fi

  echo -e "${GREEN}Cleaned up $count experiment workspace(s) for $spec_name${NC}" >&2
}

# Count total experiment workspaces (for budget check)
count_workspaces() {
  local count=0
  if [[ -d "$WORKSPACE_DIR" ]]; then
    for workspace_path in "$WORKSPACE_DIR"/*; do
      if [[ -d "$workspace_path" ]] && jj -R "$workspace_path" workspace root >/dev/null 2>&1; then
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
  create       Create an experiment workspace with copied shared files
  cleanup      Safely remove a single experiment workspace
  cleanup-all  Safely remove all experiment workspaces for a spec
  count        Count total active experiment workspaces

Workspaces: .tmp/rocketclaw/ce-optimize/workspaces/optimize-<spec>-exp-<NNN>/
EOF
      ;;
    *)
      echo -e "${RED}Unknown command: $command${NC}" >&2
      exit 1
      ;;
  esac
}

main "$@"
