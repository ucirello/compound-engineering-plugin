#!/bin/bash

# Experiment Workspace Manager
# Creates, cleans up, and counts isolated JJ workspaces for optimization experiments.
# Each experiment gets its own workspace, bookmark, change, and copied resources.
#
# Usage:
#   experiment-worktree.sh create <spec_name> <exp_index> <base_bookmark> [shared_file ...]
#   experiment-worktree.sh cleanup <spec_name> <exp_index>
#   experiment-worktree.sh cleanup-all <spec_name>
#   experiment-worktree.sh count
#
# Workspaces are created at: .tmp/rocketclaw/ce-optimize/workspaces/optimize-<spec>-exp-<NNN>/
# Bookmarks are named: optimize-exp/<spec>/exp-<NNN>

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

workspace_root=$(jj workspace root 2>/dev/null || pwd -P)
if ! jj root >/dev/null 2>&1; then
  echo -e "${RED}Error: Not in a JJ repository${NC}" >&2
  exit 1
fi

WORKSPACE_DIR="$workspace_root/.tmp/rocketclaw/ce-optimize/workspaces"

experiment_bookmark_name() {
  local spec_name="${1:?Error: spec_name required}"
  local padded_index="${2:?Error: padded_index required}"
  echo "optimize-exp/${spec_name}/exp-${padded_index}"
}

experiment_workspace_name() {
  local spec_name="${1:?Error: spec_name required}"
  local padded_index="${2:?Error: padded_index required}"
  echo "optimize-${spec_name}-exp-${padded_index}"
}

forget_workspace() {
  local workspace_name="${1:?Error: workspace_name required}"
  local workspace_path="${2:?Error: workspace_path required}"

  jj workspace forget "$workspace_name" >/dev/null 2>&1 || true
  rm -rf "$workspace_path"
}

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

  if ! jj log -r "$base_bookmark" --no-graph -T 'commit_id ++ "\n"' >/dev/null 2>&1; then
    echo -e "${RED}Error: Base bookmark does not resolve: $base_bookmark${NC}" >&2
    return 1
  fi

  if [[ -d "$workspace_path" ]]; then
    echo -e "${YELLOW}Resetting existing experiment workspace: $workspace_name${NC}" >&2
    forget_workspace "$workspace_name" "$workspace_path"
  else
    jj workspace forget "$workspace_name" >/dev/null 2>&1 || true
  fi
  jj bookmark delete "$bookmark_name" >/dev/null 2>&1 || true

  mkdir -p "$WORKSPACE_DIR"
  jj workspace add --name "$workspace_name" -r "$base_bookmark" "$workspace_path" >/dev/null
  jj -R "$workspace_path" bookmark create "$bookmark_name" -r @ >/dev/null

  for f in "$workspace_root"/.env*; do
    if [[ -f "$f" ]]; then
      local basename
      basename=$(basename "$f")
      if [[ "$basename" != ".env.example" ]]; then
        cp "$f" "$workspace_path/$basename"
      fi
    fi
  done

  for shared_file in "$@"; do
    if [[ -f "$workspace_root/$shared_file" ]]; then
      local dir
      dir=$(dirname "$workspace_path/$shared_file")
      mkdir -p "$dir"
      cp "$workspace_root/$shared_file" "$workspace_path/$shared_file"
    elif [[ -d "$workspace_root/$shared_file" ]]; then
      local dir
      dir=$(dirname "$workspace_path/$shared_file")
      mkdir -p "$dir"
      rm -rf "$workspace_path/$shared_file"
      cp -R "$workspace_root/$shared_file" "$workspace_path/$shared_file"
    fi
  done

  echo "$workspace_path"
}

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

  forget_workspace "$workspace_name" "$workspace_path"
  jj bookmark delete "$bookmark_name" >/dev/null 2>&1 || true
  echo -e "${GREEN}Cleaned up: $workspace_name${NC}" >&2
}

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
      local index_str="${workspace_name#$prefix}"
      local bookmark_name
      bookmark_name=$(experiment_bookmark_name "$spec_name" "$index_str")

      forget_workspace "$workspace_name" "$workspace_path"
      jj bookmark delete "$bookmark_name" >/dev/null 2>&1 || true
      count=$((count + 1))
    fi
  done

  if [[ -d "$WORKSPACE_DIR" ]] && [[ -z "$(ls -A "$WORKSPACE_DIR" 2>/dev/null)" ]]; then
    rmdir "$WORKSPACE_DIR" 2>/dev/null || true
  fi

  echo -e "${GREEN}Cleaned up $count experiment workspace(s) for $spec_name${NC}" >&2
}

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
  create       Create an experiment workspace, bookmark, and change
  cleanup      Forget one experiment workspace and delete its bookmark
  cleanup-all  Forget all experiment workspaces for a spec
  count        Count active experiment workspaces

Workspaces: .tmp/rocketclaw/ce-optimize/workspaces/optimize-<spec>-exp-<NNN>/
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
