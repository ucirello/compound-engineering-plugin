#!/bin/bash

# Experiment Workspace Manager
# Creates, cleans up, and counts isolated JJ workspaces for optimization experiments.
#
# Usage:
#   experiment-workspace.sh create <spec_name> <exp_index> <base_revision> [shared_file ...]
#   experiment-workspace.sh cleanup <spec_name> <exp_index>
#   experiment-workspace.sh cleanup-all <spec_name>
#   experiment-workspace.sh count

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

REPO_ROOT=$(jj workspace root 2>/dev/null) || {
  echo -e "${RED}Error: Not in a Jujutsu repository${NC}" >&2
  exit 1
}

WORKSPACE_DIR="$REPO_ROOT/.tmp/rocketclaw/ce-optimize/workspaces"

workspace_name() {
  local spec_name="${1:?Error: spec_name required}"
  local padded_index="${2:?Error: padded_index required}"
  printf 'optimize-%s-exp-%s' "$spec_name" "$padded_index"
}

workspace_is_registered() {
  local name="${1:?Error: workspace name required}"
  jj workspace list -T 'name ++ "\n"' | while IFS= read -r registered; do
    [[ "$registered" == "$name" ]] && exit 0
  done
}

remove_workspace() {
  local name="${1:?Error: workspace name required}"
  local path="${2:?Error: workspace path required}"

  if workspace_is_registered "$name"; then
    jj workspace forget "$name" >/dev/null
  fi
  if [[ -d "$path" ]]; then
    rm -rf "$path"
  fi
}

create_workspace() {
  local spec_name="${1:?Error: spec_name required}"
  local exp_index="${2:?Error: exp_index required}"
  local base_revision="${3:?Error: base_revision required}"
  shift 3

  local padded_index
  padded_index=$(printf '%03d' "$exp_index")
  local name
  name=$(workspace_name "$spec_name" "$padded_index")
  local path="$WORKSPACE_DIR/$name"

  mkdir -p "$WORKSPACE_DIR"
  if workspace_is_registered "$name" || [[ -e "$path" ]]; then
    echo -e "${YELLOW}Recreating existing experiment workspace: $name${NC}" >&2
    remove_workspace "$name" "$path"
  fi

  jj workspace add --name "$name" -r "$base_revision" "$path" >/dev/null

  for file in "$REPO_ROOT"/.env*; do
    if [[ -f "$file" ]]; then
      local basename
      basename=$(basename "$file")
      if [[ "$basename" != '.env.example' ]]; then
        cp "$file" "$path/$basename"
      fi
    fi
  done

  for shared_file in "$@"; do
    if [[ -f "$REPO_ROOT/$shared_file" ]]; then
      mkdir -p "$(dirname "$path/$shared_file")"
      cp "$REPO_ROOT/$shared_file" "$path/$shared_file"
    elif [[ -d "$REPO_ROOT/$shared_file" ]]; then
      mkdir -p "$(dirname "$path/$shared_file")"
      rm -rf "$path/$shared_file"
      cp -R "$REPO_ROOT/$shared_file" "$path/$shared_file"
    fi
  done

  printf '%s\n' "$path"
}

cleanup_workspace() {
  local spec_name="${1:?Error: spec_name required}"
  local exp_index="${2:?Error: exp_index required}"
  local padded_index
  padded_index=$(printf '%03d' "$exp_index")
  local name
  name=$(workspace_name "$spec_name" "$padded_index")

  remove_workspace "$name" "$WORKSPACE_DIR/$name"
  echo -e "${GREEN}Cleaned up: $name${NC}" >&2
}

cleanup_all() {
  local spec_name="${1:?Error: spec_name required}"
  local prefix="optimize-${spec_name}-exp-"
  local count=0

  if [[ -d "$WORKSPACE_DIR" ]]; then
    for path in "$WORKSPACE_DIR"/${prefix}*; do
      if [[ -d "$path" ]]; then
        remove_workspace "$(basename "$path")" "$path"
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
  jj workspace list -T 'name ++ "\n"' | wc -l | tr -d ' '
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
  experiment-workspace.sh create <spec_name> <exp_index> <base_revision> [shared_file ...]
  experiment-workspace.sh cleanup <spec_name> <exp_index>
  experiment-workspace.sh cleanup-all <spec_name>
  experiment-workspace.sh count

Commands:
  create       Create an experiment JJ workspace with copied shared files
  cleanup      Forget and remove one experiment workspace
  cleanup-all  Forget and remove all experiment workspaces for a spec
  count        Count active JJ workspaces
EOF
      ;;
    *)
      echo -e "${RED}Unknown command: $command${NC}" >&2
      exit 1
      ;;
  esac
}

main "$@"
