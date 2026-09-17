#!/bin/bash

# Experiment Workspace Manager
# Creates, cleans up, and manages Jujutsu workspaces for optimization experiments.
# Each experiment gets an isolated workspace with copied shared resources.
#
# Usage:
#   experiment-worktree.sh create <spec_name> <exp_index> <base_bookmark> [shared_file ...]
#   experiment-worktree.sh cleanup <spec_name> <exp_index>
#   experiment-worktree.sh cleanup-all <spec_name>
#   experiment-worktree.sh count
#
# Workspaces are created at: .tmp/ce-optimize/workspaces/optimize-<spec>-exp-<NNN>/
# Workspace names: optimize-<spec>-exp-<NNN>
# Working-copy revisions: <workspace-name>@

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

JJ_ROOT=$(jj workspace root 2>/dev/null) || {
  echo -e "${RED}Error: Not in a Jujutsu repository${NC}" >&2
  exit 1
}

WORKSPACE_DIR="$JJ_ROOT/.tmp/ce-optimize/workspaces"

jj_in_root() {
  (cd "$JJ_ROOT" && jj "$@")
}

ensure_scratch_root() {
  mkdir -p "$WORKSPACE_DIR"
  chmod 0700 "$JJ_ROOT/.tmp" 2>/dev/null || true
  chmod 0700 "$JJ_ROOT/.tmp/ce-optimize" 2>/dev/null || true
  chmod 0700 "$WORKSPACE_DIR" 2>/dev/null || true
}

experiment_workspace_name() {
  local spec_name="${1:?Error: spec_name required}"
  local padded_index="${2:?Error: padded_index required}"

  echo "optimize-${spec_name}-exp-${padded_index}"
}

is_registered_workspace() {
  local workspace_name="${1:?Error: workspace_name required}"
  local workspace_path="${2:?Error: workspace_path required}"
  local registered
  local resolved_registered
  local resolved_target

  registered=$(jj_in_root workspace root --name "$workspace_name" 2>/dev/null) || return 1
  resolved_registered=$(cd "$registered" && pwd -P)
  resolved_target=$(cd "$workspace_path" && pwd -P)
  [[ "$resolved_registered" == "$resolved_target" ]]
}

forget_workspace() {
  local workspace_name="${1:?Error: workspace_name required}"
  local workspace_path="${2:?Error: workspace_path required}"

  jj_in_root workspace forget "$workspace_name" >/dev/null 2>&1 || true
  rm -rf "$workspace_path" 2>/dev/null || true
}

# Create an experiment workspace
create_workspace() {
  local spec_name="${1:?Error: spec_name required}"
  local exp_index="${2:?Error: exp_index required}"
  local base_bookmark="${3:?Error: base_bookmark required}"
  shift 3

  local padded_index
  padded_index=$(printf "%03d" "$exp_index")
  local workspace_name
  workspace_name=$(experiment_workspace_name "$spec_name" "$padded_index")
  local workspace_path="$WORKSPACE_DIR/$workspace_name"

  if [[ -d "$workspace_path" ]]; then
    if ! is_registered_workspace "$workspace_name" "$workspace_path"; then
      echo -e "${RED}Error: Existing path is not a valid registered Jujutsu workspace: $workspace_path${NC}" >&2
      echo -e "${RED}Remove or repair that directory before rerunning the experiment.${NC}" >&2
      return 1
    fi

    echo -e "${YELLOW}Resetting existing experiment workspace to base: $workspace_name -> $base_bookmark${NC}" >&2
    forget_workspace "$workspace_name" "$workspace_path"
  fi

  ensure_scratch_root

  if ! jj_in_root workspace add --name "$workspace_name" -r "$base_bookmark" "$workspace_path"; then
    echo -e "${RED}Error: Failed to create workspace $workspace_name from $base_bookmark${NC}" >&2
    return 1
  fi

  # Copy .env files from the default workspace
  for f in "$JJ_ROOT"/.env*; do
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

# Clean up a single experiment workspace
cleanup_workspace() {
  local spec_name="${1:?Error: spec_name required}"
  local exp_index="${2:?Error: exp_index required}"

  local padded_index
  padded_index=$(printf "%03d" "$exp_index")
  local workspace_name
  workspace_name=$(experiment_workspace_name "$spec_name" "$padded_index")
  local workspace_path="$WORKSPACE_DIR/$workspace_name"

  forget_workspace "$workspace_name" "$workspace_path"

  echo -e "${GREEN}Cleaned up: $workspace_name${NC}" >&2
}

# Clean up all experiment workspaces for a spec
cleanup_all() {
  local spec_name="${1:?Error: spec_name required}"
  local prefix="optimize-${spec_name}-exp-"
  local count=0

  if [[ ! -d "$WORKSPACE_DIR" ]]; then
    echo -e "${YELLOW}No experiment workspaces directory found${NC}" >&2
    return 0
  fi

  local workspace_path
  for workspace_path in "$WORKSPACE_DIR"/${prefix}*; do
    if [[ -d "$workspace_path" ]]; then
      local workspace_name
      workspace_name=$(basename "$workspace_path")
      forget_workspace "$workspace_name" "$workspace_path"
      count=$((count + 1))
    fi
  done

  if [[ -d "$WORKSPACE_DIR" ]] && [[ -z "$(ls -A "$WORKSPACE_DIR" 2>/dev/null)" ]]; then
    rmdir "$WORKSPACE_DIR" 2>/dev/null || true
  fi

  echo -e "${GREEN}Cleaned up $count experiment workspace(s) for $spec_name${NC}" >&2
}

# Count experiment workspaces (for budget check)
count_workspaces() {
  local count=0
  local name
  local path

  while IFS= read -r name; do
    [[ -z "$name" || "$name" == "default" ]] && continue
    path=$(jj_in_root workspace root --name "$name" 2>/dev/null) || continue
    if [[ "$path" == "$WORKSPACE_DIR"/* ]]; then
      count=$((count + 1))
    fi
  done < <(jj_in_root workspace list -T 'name ++ "\n"')

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
  experiment-worktree.sh create <spec_name> <exp_index> <base_bookmark> [shared_file ...]
  experiment-worktree.sh cleanup <spec_name> <exp_index>
  experiment-worktree.sh cleanup-all <spec_name>
  experiment-worktree.sh count

Commands:
  create       Create an experiment workspace with copied shared files
  cleanup      Remove a single experiment workspace
  cleanup-all  Remove all experiment workspaces for a spec
  count        Count total active experiment workspaces (for budget checking)

Workspaces: .tmp/ce-optimize/workspaces/optimize-<spec>-exp-<NNN>/
Names:      optimize-<spec>-exp-<NNN>
EOF
      ;;
    *)
      echo -e "${RED}Unknown command: $command${NC}" >&2
      exit 1
      ;;
  esac
}

main "$@"
