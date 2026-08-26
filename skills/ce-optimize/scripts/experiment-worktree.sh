#!/bin/bash

# JJ experiment workspace manager.
# Each experiment gets an isolated workspace, change, and local bookmark.

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ROOT=$(jj workspace root 2>/dev/null) || {
  echo -e "${RED}Error: Not in a JJ repository${NC}" >&2
  exit 1
}

WORKSPACE_DIR="$ROOT/.tmp/ce-optimize/workspaces"

workspace_name() {
  local spec_name="${1:?Error: spec_name required}"
  local padded_index="${2:?Error: padded_index required}"
  echo "ce-optimize-${spec_name}-exp-${padded_index}"
}

experiment_bookmark_name() {
  local spec_name="${1:?Error: spec_name required}"
  local padded_index="${2:?Error: padded_index required}"
  echo "optimize-exp/${spec_name}/exp-${padded_index}"
}

create_workspace() {
  local spec_name="${1:?Error: spec_name required}"
  local exp_index="${2:?Error: exp_index required}"
  local base_revision="${3:?Error: base_revision required}"
  local change_description="${4:?Error: change_description required}"
  shift 4

  local padded_index
  padded_index=$(printf "%03d" "$exp_index")
  local name
  name=$(workspace_name "$spec_name" "$padded_index")
  local bookmark
  bookmark=$(experiment_bookmark_name "$spec_name" "$padded_index")
  local workspace_path="$WORKSPACE_DIR/$name"

  if [[ -e "$workspace_path" ]] || jj workspace list -T 'name ++ "\n"' | grep -Fxq "$name"; then
    echo -e "${RED}Error: Experiment workspace already exists: $name${NC}" >&2
    echo -e "${RED}Clean up or resume that experiment before rerunning it.${NC}" >&2
    return 1
  fi

  mkdir -p "$WORKSPACE_DIR"
  jj workspace add --name "$name" -r "$base_revision" -m "$change_description" "$workspace_path" >/dev/null
  jj -R "$workspace_path" bookmark create "$bookmark" -r @ >/dev/null

  for f in "$ROOT"/.env*; do
    if [[ -f "$f" ]]; then
      local basename
      basename=$(basename "$f")
      if [[ "$basename" != ".env.example" ]]; then
        cp "$f" "$workspace_path/$basename"
      fi
    fi
  done

  for shared_file in "$@"; do
    if [[ -f "$ROOT/$shared_file" ]]; then
      mkdir -p "$(dirname "$workspace_path/$shared_file")"
      cp "$ROOT/$shared_file" "$workspace_path/$shared_file"
    elif [[ -d "$ROOT/$shared_file" ]]; then
      mkdir -p "$(dirname "$workspace_path/$shared_file")"
      rm -rf "$workspace_path/$shared_file"
      cp -R "$ROOT/$shared_file" "$workspace_path/$shared_file"
    fi
  done

  echo "$workspace_path"
}

cleanup_workspace() {
  local spec_name="${1:?Error: spec_name required}"
  local exp_index="${2:?Error: exp_index required}"

  local padded_index
  padded_index=$(printf "%03d" "$exp_index")
  local name
  name=$(workspace_name "$spec_name" "$padded_index")
  local bookmark
  bookmark=$(experiment_bookmark_name "$spec_name" "$padded_index")
  local workspace_path="$WORKSPACE_DIR/$name"

  if [[ -d "$workspace_path" ]]; then
    jj -R "$workspace_path" abandon @ >/dev/null 2>&1 || true
  fi
  jj workspace forget "$name" >/dev/null 2>&1 || true
  jj bookmark forget "exact:$bookmark" >/dev/null 2>&1 || true
  rm -rf "$workspace_path"
  echo -e "${GREEN}Cleaned up: $name${NC}" >&2
}

release_workspace() {
  local spec_name="${1:?Error: spec_name required}"
  local exp_index="${2:?Error: exp_index required}"

  local padded_index
  padded_index=$(printf "%03d" "$exp_index")
  local name
  name=$(workspace_name "$spec_name" "$padded_index")
  local bookmark
  bookmark=$(experiment_bookmark_name "$spec_name" "$padded_index")
  local workspace_path="$WORKSPACE_DIR/$name"

  jj workspace forget "$name" >/dev/null 2>&1 || true
  jj bookmark forget "exact:$bookmark" >/dev/null 2>&1 || true
  rm -rf "$workspace_path"
  echo -e "${GREEN}Released integrated workspace: $name${NC}" >&2
}

cleanup_all() {
  local spec_name="${1:?Error: spec_name required}"
  local prefix="ce-optimize-${spec_name}-exp-"
  local count=0

  if [[ ! -d "$WORKSPACE_DIR" ]]; then
    echo -e "${YELLOW}No experiment workspace directory found${NC}" >&2
    return 0
  fi

  for workspace_path in "$WORKSPACE_DIR"/${prefix}*; do
    if [[ -d "$workspace_path" ]]; then
      local name
      name=$(basename "$workspace_path")
      local index_str="${name#$prefix}"
      cleanup_workspace "$spec_name" "$((10#$index_str))"
      count=$((count + 1))
    fi
  done

  rmdir "$WORKSPACE_DIR" 2>/dev/null || true
  echo -e "${GREEN}Cleaned up $count experiment workspace(s) for $spec_name${NC}" >&2
}

count_workspaces() {
  jj workspace list -T 'name ++ "\n"' | grep -c '^ce-optimize-.*-exp-[0-9][0-9][0-9]$' || true
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
    release)
      shift
      release_workspace "$@"
      ;;
    count)
      count_workspaces
      ;;
    help)
      cat << 'EOF'
JJ Experiment Workspace Manager

Usage:
  experiment-worktree.sh create <spec_name> <exp_index> <base_revision> <change_description> [shared_file ...]
  experiment-worktree.sh cleanup <spec_name> <exp_index>
  experiment-worktree.sh cleanup-all <spec_name>
  experiment-worktree.sh release <spec_name> <exp_index>
  experiment-worktree.sh count

Workspaces: <workspace-root>/.tmp/ce-optimize/workspaces/ce-optimize-<spec>-exp-<NNN>/
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
