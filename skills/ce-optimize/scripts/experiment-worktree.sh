#!/bin/bash

# Experiment Workspace Manager
# Creates, cleans up, and counts jj workspaces for optimization experiments.
# Each experiment gets an isolated workspace with copied shared resources.
#
# Usage:
#   experiment-worktree.sh create <spec_name> <exp_index> <base_revision> [shared_file ...]
#   experiment-worktree.sh cleanup <spec_name> <exp_index>
#   experiment-worktree.sh cleanup-all <spec_name>
#   experiment-worktree.sh count

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

SOURCE_ROOT=$(jj workspace root 2>/dev/null) || {
  echo -e "${RED}Error: Not in a jj workspace${NC}" >&2
  exit 1
}

STATE_ROOT="$SOURCE_ROOT/.context/ce-optimize"
WORKSPACE_DIR="$STATE_ROOT/workspaces"

experiment_workspace_name() {
  local spec_name="${1:?Error: spec_name required}"
  local padded_index="${2:?Error: padded_index required}"
  printf 'optimize-%s-exp-%s\n' "$spec_name" "$padded_index"
}

workspace_is_registered() {
  local workspace_name="${1:?Error: workspace_name required}"
  while IFS= read -r candidate; do
    [[ "$candidate" == "$workspace_name" ]] && return 0
  done < <(jj workspace list -T 'name ++ "\n"' 2>/dev/null)
  return 1
}

reset_workspace_to_base() {
  local workspace_path="${1:?Error: workspace_path required}"
  local base_revision="${2:?Error: base_revision required}"

  echo -e "${YELLOW}Resetting existing experiment workspace to base revision: $base_revision${NC}" >&2
  jj -R "$workspace_path" restore --from "$base_revision" >/dev/null
  jj -R "$workspace_path" rebase -r '@' -o "$base_revision" >/dev/null
}

create_workspace() {
  local spec_name="${1:?Error: spec_name required}"
  local exp_index="${2:?Error: exp_index required}"
  local base_revision="${3:?Error: base_revision required}"
  shift 3

  local padded_index
  padded_index=$(printf '%03d' "$exp_index")
  local workspace_name
  workspace_name=$(experiment_workspace_name "$spec_name" "$padded_index")
  local workspace_path="$WORKSPACE_DIR/$workspace_name"

  if [[ -d "$workspace_path" ]]; then
    if ! workspace_is_registered "$workspace_name"; then
      echo -e "${RED}Error: Existing path is not a registered jj workspace: $workspace_path${NC}" >&2
      echo -e "${RED}Remove or repair that directory before rerunning the experiment.${NC}" >&2
      return 1
    fi
    reset_workspace_to_base "$workspace_path" "$base_revision"
  else
    mkdir -p "$WORKSPACE_DIR"
    jj workspace add --name "$workspace_name" -r "$base_revision" "$workspace_path" >/dev/null
  fi

  for f in "$SOURCE_ROOT"/.env*; do
    if [[ -f "$f" ]]; then
      local basename
      basename=$(basename "$f")
      if [[ "$basename" != ".env.example" ]]; then
        cp "$f" "$workspace_path/$basename"
      fi
    fi
  done

  for shared_file in "$@"; do
    if [[ -f "$SOURCE_ROOT/$shared_file" ]]; then
      mkdir -p "$(dirname "$workspace_path/$shared_file")"
      cp "$SOURCE_ROOT/$shared_file" "$workspace_path/$shared_file"
    elif [[ -d "$SOURCE_ROOT/$shared_file" ]]; then
      mkdir -p "$(dirname "$workspace_path/$shared_file")"
      rm -rf "$workspace_path/$shared_file"
      cp -R "$SOURCE_ROOT/$shared_file" "$workspace_path/$shared_file"
    fi
  done

  printf '%s\n' "$workspace_path"
}

cleanup_workspace() {
  local spec_name="${1:?Error: spec_name required}"
  local exp_index="${2:?Error: exp_index required}"
  local padded_index
  padded_index=$(printf '%03d' "$exp_index")
  local workspace_name
  workspace_name=$(experiment_workspace_name "$spec_name" "$padded_index")
  local workspace_path="$WORKSPACE_DIR/$workspace_name"

  if workspace_is_registered "$workspace_name"; then
    jj workspace forget "$workspace_name" >/dev/null
  fi
  if [[ -d "$workspace_path" ]]; then
    rm -rf "$workspace_path"
  fi

  echo -e "${GREEN}Cleaned up: $workspace_name${NC}" >&2
}

cleanup_all() {
  local spec_name="${1:?Error: spec_name required}"
  local prefix="optimize-${spec_name}-exp-"
  local count=0

  while IFS= read -r workspace_name; do
    if [[ "$workspace_name" == "$prefix"* ]]; then
      jj workspace forget "$workspace_name" >/dev/null
      rm -rf "$WORKSPACE_DIR/$workspace_name"
      count=$((count + 1))
    fi
  done < <(jj workspace list -T 'name ++ "\n"')

  echo -e "${GREEN}Cleaned up $count experiment workspace(s) for $spec_name${NC}" >&2
}

count_workspaces() {
  local count=0
  while IFS= read -r workspace_name; do
    [[ "$workspace_name" == optimize-*-exp-* ]] && count=$((count + 1))
  done < <(jj workspace list -T 'name ++ "\n"')
  printf '%s\n' "$count"
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
      cat <<'EOF'
Experiment Workspace Manager

Usage:
  experiment-worktree.sh create <spec_name> <exp_index> <base_revision> [shared_file ...]
  experiment-worktree.sh cleanup <spec_name> <exp_index>
  experiment-worktree.sh cleanup-all <spec_name>
  experiment-worktree.sh count
EOF
      ;;
    *)
      echo -e "${RED}Unknown command: $command${NC}" >&2
      exit 1
      ;;
  esac
}

main "$@"
