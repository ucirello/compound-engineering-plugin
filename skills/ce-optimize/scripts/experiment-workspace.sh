#!/bin/bash

# Experiment Workspace Manager
#
# Usage:
#   experiment-workspace.sh create <spec_name> <exp_index> <base_revision> [shared_file ...]
#   experiment-workspace.sh cleanup <spec_name> <exp_index>
#   experiment-workspace.sh cleanup-all <spec_name>
#   experiment-workspace.sh count

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

JJ_ROOT=$(jj workspace root 2>/dev/null) || {
  echo -e "${RED}Error: Not in a JJ workspace${NC}" >&2
  exit 1
}

WORKSPACE_DIR="$JJ_ROOT/.tmp/optimize-workspaces"

workspace_name() {
  local spec_name="${1:?Error: spec_name required}"
  local padded_index="${2:?Error: padded_index required}"
  printf 'optimize-%s-exp-%s' "$spec_name" "$padded_index"
}

workspace_registered() {
  local name="${1:?Error: workspace name required}"
  jj workspace list -T 'self.name() ++ "\n"' | grep -Fxq "$name"
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
  local workspace_path="$WORKSPACE_DIR/$name"

  # A surviving registration/path may contain interrupted work. Never reuse it.
  if workspace_registered "$name"; then
    if [[ -d "$workspace_path" ]]; then
      echo -e "${RED}Error: Workspace already exists and may contain interrupted experiment work: $workspace_path${NC}" >&2
      echo -e "${RED}Run cleanup after confirming it is no longer needed.${NC}" >&2
      return 1
    fi
    echo -e "${RED}Error: JJ workspace '$name' is registered but its path is missing.${NC}" >&2
    echo -e "${RED}Run cleanup after confirming the interrupted experiment is no longer needed.${NC}" >&2
    return 1
  fi

  if [[ -e "$workspace_path" ]]; then
    echo -e "${RED}Error: Existing path is not a registered JJ workspace: $workspace_path${NC}" >&2
    echo -e "${RED}Remove or repair that directory before rerunning the experiment.${NC}" >&2
    return 1
  fi

  if [[ ! -f "$JJ_ROOT/.gitignore" ]] || ! grep -Eq '^/?\.tmp/?$' "$JJ_ROOT/.gitignore"; then
    echo -e "${RED}Error: .tmp/ must be ignored in $JJ_ROOT/.gitignore before creating experiment workspaces.${NC}" >&2
    return 1
  fi

  mkdir -p "$WORKSPACE_DIR"
  jj workspace add --name "$name" -r "$base_revision" "$workspace_path" >/dev/null

  for file in "$JJ_ROOT"/.env*; do
    if [[ -f "$file" ]]; then
      local basename
      basename=$(basename "$file")
      if [[ "$basename" != ".env.example" ]]; then
        cp "$file" "$workspace_path/$basename"
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

  printf '%s\n' "$workspace_path"
}

cleanup_workspace() {
  local spec_name="${1:?Error: spec_name required}"
  local exp_index="${2:?Error: exp_index required}"
  local padded_index
  padded_index=$(printf '%03d' "$exp_index")
  local name
  name=$(workspace_name "$spec_name" "$padded_index")
  local workspace_path="$WORKSPACE_DIR/$name"

  if workspace_registered "$name"; then
    jj workspace forget "$name"
  fi
  rm -rf "$workspace_path"
  echo -e "${GREEN}Cleaned up: $name${NC}" >&2
}

cleanup_all() {
  local spec_name="${1:?Error: spec_name required}"
  local prefix="optimize-${spec_name}-exp-"
  local count=0
  local names
  names=$(jj workspace list -T 'self.name() ++ "\n"')

  while IFS= read -r name; do
    if [[ "$name" == "$prefix"* ]]; then
      jj workspace forget "$name"
      rm -rf "$WORKSPACE_DIR/$name"
      count=$((count + 1))
    fi
  done <<< "$names"

  echo -e "${GREEN}Cleaned up $count experiment workspace(s) for $spec_name${NC}" >&2
}

count_workspaces() {
  jj workspace list -T 'self.name() ++ "\n"' | grep -c '^optimize-.*-exp-[0-9][0-9][0-9]$' || true
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
      printf '%s\n' \
        'Experiment Workspace Manager' \
        '' \
        'Usage:' \
        '  experiment-workspace.sh create <spec_name> <exp_index> <base_revision> [shared_file ...]' \
        '  experiment-workspace.sh cleanup <spec_name> <exp_index>' \
        '  experiment-workspace.sh cleanup-all <spec_name>' \
        '  experiment-workspace.sh count' \
        '' \
        'Commands:' \
        '  create       Create an experiment workspace with copied shared files' \
        '  cleanup      Remove a single experiment workspace' \
        '  cleanup-all  Remove all experiment workspaces for a spec' \
        '  count        Count total active workspaces (for budget checking)'
      ;;
    *)
      echo -e "${RED}Unknown command: $command${NC}" >&2
      exit 1
      ;;
  esac
}

main "$@"
