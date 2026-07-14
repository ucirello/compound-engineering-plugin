#!/bin/bash

# Experiment Workspace Manager
# Creates, cleans up, and manages JJ workspaces for optimization experiments.
# Each experiment gets an isolated workspace with copied shared resources.

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

JJ_ROOT=$(jj workspace root 2>/dev/null) || {
  echo -e "${RED}Error: Not in a JJ repository${NC}" >&2
  exit 1
}

WORKSPACE_DIR="$JJ_ROOT/.tmp/optimize-workspaces"

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
  local workspace_name="${1:?Error: workspace_name required}"
  jj workspace list -T 'name ++ "\n"' | grep -Fxq "$workspace_name"
}

remove_workspace() {
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

  if [[ -d "$workspace_path" ]] || is_registered_workspace "$workspace_name"; then
    echo -e "${YELLOW}Recreating existing experiment workspace: $workspace_name${NC}" >&2
    remove_workspace "$workspace_name" "$workspace_path"
  fi

  mkdir -p "$WORKSPACE_DIR"
  jj workspace add --name "$workspace_name" -r "$base_bookmark" "$workspace_path" >/dev/null
  jj -R "$workspace_path" bookmark create "$bookmark_name" -r @ >/dev/null 2>&1 || \
    jj -R "$workspace_path" bookmark set "$bookmark_name" -r @ >/dev/null

  for f in "$JJ_ROOT"/.env*; do
    if [[ -f "$f" ]]; then
      local basename
      basename=$(basename "$f")
      if [[ "$basename" != ".env.example" ]]; then
        cp "$f" "$workspace_path/$basename"
      fi
    fi
  done

  for shared_file in "$@"; do
    if [[ -f "$JJ_ROOT/$shared_file" ]]; then
      mkdir -p "$(dirname "$workspace_path/$shared_file")"
      cp "$JJ_ROOT/$shared_file" "$workspace_path/$shared_file"
    elif [[ -d "$JJ_ROOT/$shared_file" ]]; then
      mkdir -p "$(dirname "$workspace_path/$shared_file")"
      rm -rf "$workspace_path/$shared_file"
      cp -R "$JJ_ROOT/$shared_file" "$workspace_path/$shared_file"
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

  remove_workspace "$workspace_name" "$WORKSPACE_DIR/$workspace_name"
  jj bookmark delete "$bookmark_name" >/dev/null 2>&1 || true
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
        remove_workspace "$workspace_name" "$workspace_path"
        jj bookmark delete "$(experiment_bookmark_name "$spec_name" "$index_str")" >/dev/null 2>&1 || true
        count=$((count + 1))
      fi
    done
  fi

  echo -e "${GREEN}Cleaned up $count experiment workspace(s) for $spec_name${NC}" >&2
}

count_workspaces() {
  jj workspace list -T 'name ++ "\n"' | wc -l | tr -d ' '
}

case "${1:-help}" in
  create) shift; create_workspace "$@" ;;
  cleanup) shift; cleanup_workspace "$@" ;;
  cleanup-all) shift; cleanup_all "$@" ;;
  count) count_workspaces ;;
  help)
    printf '%s\n' \
      'Experiment Workspace Manager' \
      'Usage: experiment-workspace.sh create <spec_name> <exp_index> <base_bookmark> [shared_file ...]' \
      '       experiment-workspace.sh cleanup <spec_name> <exp_index>' \
      '       experiment-workspace.sh cleanup-all <spec_name>' \
      '       experiment-workspace.sh count'
    ;;
  *) echo -e "${RED}Unknown command: $1${NC}" >&2; exit 1 ;;
esac
