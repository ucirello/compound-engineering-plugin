#!/bin/bash

# Experiment Workspace Manager
# Creates, cleans up, and manages JJ workspaces for optimization experiments.
# The historical filename is retained because it is a shipped support-asset path.
# Each experiment gets an isolated workspace with copied shared resources.
#
# Usage:
#   experiment-worktree.sh create <spec_name> <exp_index> <base_revision> [shared_file ...]
#   experiment-worktree.sh cleanup <spec_name> <exp_index>
#   experiment-worktree.sh forget <spec_name> <exp_index>
#   experiment-worktree.sh cleanup-all <spec_name>
#   experiment-worktree.sh count
#
# Workspaces are created at: <workspace-root>/.tmp/rocketclaw/ce-optimize/workspaces/optimize-<spec>-exp-<NNN>/
# Bookmarks are named: optimize-exp/<spec>/exp-<NNN>

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

WORKSPACE_ROOT=$(jj workspace root 2>/dev/null || pwd -P)
if ! jj --repository "$WORKSPACE_ROOT" root >/dev/null 2>&1; then
  echo -e "${RED}Error: Not in a JJ repository${NC}" >&2
  exit 1
fi

WORKSPACE_DIR="$WORKSPACE_ROOT/.tmp/rocketclaw/ce-optimize/workspaces"

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

is_registered_workspace() {
  local workspace_path="${1:?Error: workspace_path required}"
  jj --repository "$workspace_path" workspace root >/dev/null 2>&1
}

reset_workspace_to_base() {
  local workspace_path="${1:?Error: workspace_path required}"
  local base_revision="${2:?Error: base_revision required}"

  echo -e "${YELLOW}Resetting existing experiment workspace to base revision: $base_revision${NC}" >&2
  jj --repository "$workspace_path" abandon @ >/dev/null
  jj --repository "$workspace_path" new "$base_revision" >/dev/null
}

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
    if ! is_registered_workspace "$workspace_path"; then
      echo -e "${RED}Error: Existing path is not a registered JJ workspace: $workspace_path${NC}" >&2
      echo -e "${RED}Remove or repair that directory before rerunning the experiment.${NC}" >&2
      return 1
    fi
    echo -e "${YELLOW}Workspace already exists: $workspace_path${NC}" >&2
    reset_workspace_to_base "$workspace_path" "$base_revision"
  else
    mkdir -p "$WORKSPACE_DIR"
    jj --repository "$WORKSPACE_ROOT" workspace add --name "$workspace_name" --revision "$base_revision" "$workspace_path" >/dev/null
  fi

  jj --repository "$workspace_path" bookmark set "$bookmark_name" --revision @ >/dev/null

  # Copy local environment files without copying the example template.
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

  if [[ -d "$workspace_path" ]] && is_registered_workspace "$workspace_path"; then
    jj --repository "$workspace_path" abandon @ >/dev/null 2>&1 || true
  fi
  jj --repository "$WORKSPACE_ROOT" workspace forget "$workspace_name" >/dev/null 2>&1 || true
  rm -rf "$workspace_path" 2>/dev/null || true
  jj --repository "$WORKSPACE_ROOT" bookmark delete "$bookmark_name" >/dev/null 2>&1 || true

  echo -e "${GREEN}Cleaned up: $workspace_name${NC}" >&2
}

forget_workspace() {
  local spec_name="${1:?Error: spec_name required}"
  local exp_index="${2:?Error: exp_index required}"
  local padded_index
  padded_index=$(printf "%03d" "$exp_index")
  local workspace_name
  workspace_name=$(experiment_workspace_name "$spec_name" "$padded_index")
  local bookmark_name
  bookmark_name=$(experiment_bookmark_name "$spec_name" "$padded_index")
  local workspace_path="$WORKSPACE_DIR/$workspace_name"

  jj --repository "$WORKSPACE_ROOT" workspace forget "$workspace_name" >/dev/null 2>&1 || true
  rm -rf "$workspace_path" 2>/dev/null || true
  jj --repository "$WORKSPACE_ROOT" bookmark delete "$bookmark_name" >/dev/null 2>&1 || true

  echo -e "${GREEN}Forgot accepted workspace: $workspace_name${NC}" >&2
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
      cleanup_workspace "$spec_name" "$((10#$index_str))"
      count=$((count + 1))
    fi
  done

  rmdir "$WORKSPACE_DIR" 2>/dev/null || true
  echo -e "${GREEN}Cleaned up $count experiment workspace(s) for $spec_name${NC}" >&2
}

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
    forget)
      shift
      forget_workspace "$@"
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
  experiment-worktree.sh forget <spec_name> <exp_index>
  experiment-worktree.sh cleanup-all <spec_name>
  experiment-worktree.sh count

Commands:
  create       Create an experiment workspace with copied shared files
  cleanup      Remove one experiment workspace and its bookmark
  forget       Remove one accepted workspace and its experiment bookmark without abandoning the change
  cleanup-all  Remove all experiment workspaces for a spec
  count        Count active experiment workspaces
EOF
      ;;
    *)
      echo -e "${RED}Unknown command: $command${NC}" >&2
      exit 1
      ;;
  esac
}

main "$@"
