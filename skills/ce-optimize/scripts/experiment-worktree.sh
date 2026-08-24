#!/bin/bash

# Experiment Workspace Manager
# The filename is retained for callers; the implementation uses JJ workspaces.
#
# Usage:
#   experiment-worktree.sh create <spec_name> <exp_index> <base_revision> [shared_file ...]
#   experiment-worktree.sh cleanup <spec_name> <exp_index>
#   experiment-worktree.sh cleanup-all <spec_name>
#   experiment-worktree.sh count
#
# Workspaces are created at: <workspace-root>/.tmp/ce-optimize/workspaces/optimize-<spec>-exp-<NNN>/
# Workspace names are: optimize-<spec>-exp-<NNN>

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

WORKSPACE_ROOT=$(jj root 2>/dev/null) || {
  echo -e "${RED}Error: Not in a Jujutsu workspace${NC}" >&2
  exit 1
}

WORKSPACE_DIR="$WORKSPACE_ROOT/.tmp/ce-optimize/workspaces"

ensure_local_tmp_ignored() {
  local git_root
  git_root=$(jj git root 2>/dev/null) || {
    echo -e "${RED}Error: JJ repository has no Git backing store for local ignore rules${NC}" >&2
    exit 1
  }
  local exclude_file="$git_root/info/exclude"
  mkdir -p "$(dirname "$exclude_file")"
  if ! grep -q '^/\.tmp/$' "$exclude_file" 2>/dev/null; then
    printf '/.tmp/\n' >> "$exclude_file"
  fi
}

ensure_local_tmp_ignored

workspace_name() {
  local spec_name="${1:?Error: spec_name required}"
  local padded_index="${2:?Error: padded_index required}"
  echo "optimize-${spec_name}-exp-${padded_index}"
}

registered_workspace_root() {
  local name="${1:?Error: workspace name required}"
  jj workspace root --name "$name" 2>/dev/null
}

forget_workspace() {
  local name="${1:?Error: workspace name required}"
  local path="${2:?Error: workspace path required}"

  if registered_workspace_root "$name" >/dev/null; then
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
  padded_index=$(printf "%03d" "$exp_index")
  local name
  name=$(workspace_name "$spec_name" "$padded_index")
  local path="$WORKSPACE_DIR/$name"
  local registered_root=""

  registered_root=$(registered_workspace_root "$name" || true)
  if [[ -n "$registered_root" && "$registered_root" != "$path" ]]; then
    echo -e "${RED}Error: JJ workspace $name is registered at $registered_root, expected $path${NC}" >&2
    return 1
  fi

  if [[ -n "$registered_root" || -d "$path" ]]; then
    echo -e "${YELLOW}Recreating disposable JJ workspace: $name${NC}" >&2
    forget_workspace "$name" "$path"
  fi

  mkdir -p "$WORKSPACE_DIR"
  jj workspace add --name "$name" --revision "$base_revision" "$path" >/dev/null

  # Copy local environment files and explicitly declared shared resources.
  for f in "$WORKSPACE_ROOT"/.env*; do
    if [[ -f "$f" ]]; then
      local basename
      basename=$(basename "$f")
      if [[ "$basename" != ".env.example" ]]; then
        cp "$f" "$path/$basename"
      fi
    fi
  done

  for shared_file in "$@"; do
    if [[ -f "$WORKSPACE_ROOT/$shared_file" ]]; then
      mkdir -p "$(dirname "$path/$shared_file")"
      cp "$WORKSPACE_ROOT/$shared_file" "$path/$shared_file"
    elif [[ -d "$WORKSPACE_ROOT/$shared_file" ]]; then
      mkdir -p "$(dirname "$path/$shared_file")"
      rm -rf "$path/$shared_file"
      cp -R "$WORKSPACE_ROOT/$shared_file" "$path/$shared_file"
    fi
  done

  echo "$path"
}

cleanup_workspace() {
  local spec_name="${1:?Error: spec_name required}"
  local exp_index="${2:?Error: exp_index required}"
  local padded_index
  padded_index=$(printf "%03d" "$exp_index")
  local name
  name=$(workspace_name "$spec_name" "$padded_index")

  forget_workspace "$name" "$WORKSPACE_DIR/$name"
  echo -e "${GREEN}Cleaned up: $name${NC}" >&2
}

cleanup_all() {
  local spec_name="${1:?Error: spec_name required}"
  local prefix="optimize-${spec_name}-exp-"
  local count=0

  if [[ -d "$WORKSPACE_DIR" ]]; then
    for path in "$WORKSPACE_DIR"/${prefix}*; do
      if [[ -d "$path" ]]; then
        local name
        name=$(basename "$path")
        forget_workspace "$name" "$path"
        count=$((count + 1))
      fi
    done
  fi

  echo -e "${GREEN}Cleaned up $count experiment workspace(s) for $spec_name${NC}" >&2
}

count_workspaces() {
  local count=0
  if [[ -d "$WORKSPACE_DIR" ]]; then
    for path in "$WORKSPACE_DIR"/optimize-*-exp-*; do
      if [[ -d "$path" ]] && jj -R "$path" root >/dev/null 2>&1; then
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
Experiment JJ Workspace Manager

Usage:
  experiment-worktree.sh create <spec_name> <exp_index> <base_revision> [shared_file ...]
  experiment-worktree.sh cleanup <spec_name> <exp_index>
  experiment-worktree.sh cleanup-all <spec_name>
  experiment-worktree.sh count

Commands:
  create       Create a disposable JJ workspace on a base revision
  cleanup      Forget and remove one experiment workspace
  cleanup-all  Forget and remove all experiment workspaces for a spec
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
