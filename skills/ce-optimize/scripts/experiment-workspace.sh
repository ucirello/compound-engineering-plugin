#!/bin/bash

# Experiment Workspace Manager
# Creates, cleans up, and manages JJ workspaces for optimization experiments.
# Each experiment gets an isolated workspace with copied shared resources.
#
# Usage:
#   experiment-workspace.sh create <spec_name> <exp_index> <base_rev> [shared_file ...]
#   experiment-workspace.sh cleanup <spec_name> <exp_index>
#   experiment-workspace.sh cleanup-all <spec_name>
#   experiment-workspace.sh count
#
# Workspaces are created at: .workspaces/optimize-<spec>-exp-<NNN>/
# Bookmarks are named: optimize-exp/<spec>/exp-<NNN>

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

REPO_ROOT=$(jj workspace root 2>/dev/null) || {
  echo -e "${RED}Error: Not in a JJ repository${NC}" >&2
  exit 1
}

WORKSPACE_DIR="$REPO_ROOT/.workspaces"

experiment_bookmark_name() {
  local spec_name="${1:?Error: spec_name required}"
  local padded_index="${2:?Error: padded_index required}"

  # Keep experiment refs outside optimize/<spec> so they do not collide
  # with the long-lived optimization bookmark namespace.
  echo "optimize-exp/${spec_name}/exp-${padded_index}"
}

ensure_workspace_ignore() {
  local ignore_file="$REPO_ROOT/.ignore"

  if [[ -f "$ignore_file" ]] && grep -q "^\.workspaces$" "$ignore_file" 2>/dev/null; then
    return 0
  fi

  # JJ uses the colocated ignore rules for ordinary repo ignores.
  printf "\n.workspaces\n" >> "$ignore_file"
}

workspace_name_from_path() {
  basename "$1"
}

workspace_exists() {
  local workspace_name="${1:?Error: workspace_name required}"

  jj workspace list 2>/dev/null | grep -q "^${workspace_name}:"
}

remove_workspace() {
  local workspace_path="${1:?Error: workspace_path required}"
  local workspace_name
  workspace_name=$(workspace_name_from_path "$workspace_path")

  if workspace_exists "$workspace_name"; then
    jj workspace forget "$workspace_name" >/dev/null 2>&1 || true
  fi

  rm -rf "$workspace_path" 2>/dev/null || true
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

  if [[ -d "$workspace_path" ]]; then
    echo -e "${YELLOW}Workspace already exists, recreating: $workspace_path${NC}" >&2
    remove_workspace "$workspace_path"
  fi

  mkdir -p "$WORKSPACE_DIR"
  ensure_workspace_ignore

  jj workspace add --name "$workspace_name" "$workspace_path" "$base_rev" >/dev/null
  jj -R "$workspace_path" bookmark set "$bookmark_name" -r @ >/dev/null

  # Copy .env files from main repo.
  for f in "$REPO_ROOT"/.env*; do
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
    if [[ -f "$REPO_ROOT/$shared_file" ]]; then
      local dir
      dir=$(dirname "$workspace_path/$shared_file")
      mkdir -p "$dir"
      cp "$REPO_ROOT/$shared_file" "$workspace_path/$shared_file"
    elif [[ -d "$REPO_ROOT/$shared_file" ]]; then
      local dir
      dir=$(dirname "$workspace_path/$shared_file")
      mkdir -p "$dir"
      rm -rf "$workspace_path/$shared_file"
      cp -R "$REPO_ROOT/$shared_file" "$workspace_path/$shared_file"
    fi
  done

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

  remove_workspace "$workspace_path"
  jj bookmark delete "$bookmark_name" >/dev/null 2>&1 || true

  echo -e "${GREEN}Cleaned up: $workspace_name${NC}" >&2
}

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

      remove_workspace "$workspace_path"
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
      if [[ -d "$workspace_path" ]] && [[ -e "$workspace_path/.jj" ]]; then
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
  experiment-workspace.sh create <spec_name> <exp_index> <base_rev> [shared_file ...]
  experiment-workspace.sh cleanup <spec_name> <exp_index>
  experiment-workspace.sh cleanup-all <spec_name>
  experiment-workspace.sh count

Commands:
  create       Create an experiment workspace with copied shared files
  cleanup      Remove a single experiment workspace and its bookmark
  cleanup-all  Remove all experiment workspaces for a spec
  count        Count total active workspaces (for budget checking)
EOF
      ;;
    *)
      echo "Unknown command: $command" >&2
      exit 1
      ;;
  esac
}

main "$@"
