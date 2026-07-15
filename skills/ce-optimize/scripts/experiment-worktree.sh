#!/bin/bash

# Experiment Workspace Manager
# Creates, cleans up, and manages JJ workspaces for optimization experiments.
# Each experiment gets an isolated workspace with copied shared resources.
#
# Usage:
#   experiment-worktree.sh create <spec_name> <exp_index> <base_bookmark> [shared_file ...]
#   experiment-worktree.sh cleanup <spec_name> <exp_index>
#   experiment-worktree.sh cleanup-all <spec_name>
#   experiment-worktree.sh count
#
# Workspaces are created at: .worktrees/optimize-<spec>-exp-<NNN>/
# Bookmarks are named: optimize-exp/<spec>/exp-<NNN>

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

JJ_ROOT=$(jj workspace root 2>/dev/null) || {
  echo -e "${RED}Error: Not in a JJ repository${NC}" >&2
  exit 1
}

WORKSPACE_DIR="$JJ_ROOT/.worktrees"

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

ensure_workspace_exclude() {
  local git_root
  git_root=$(jj git root 2>/dev/null || true)
  if [[ -z "$git_root" ]]; then
    return
  fi

  local exclude_file="$git_root/info/exclude"
  mkdir -p "$(dirname "$exclude_file")"
  if ! grep -q '^\.worktrees/$' "$exclude_file" 2>/dev/null; then
    echo '.worktrees/' >> "$exclude_file"
  fi
}

is_registered_workspace() {
  local workspace_name="${1:?Error: workspace_name required}"
  jj -R "$JJ_ROOT" workspace list -T 'name ++ "\n"' |
    grep -Fxq "$workspace_name"
}

registered_workspace_commit() {
  local workspace_name="${1:?Error: workspace_name required}"
  jj -R "$JJ_ROOT" workspace list -T 'name ++ "\t" ++ target.commit_id() ++ "\n"' |
    while IFS=$'\t' read -r name commit_id; do
      if [[ "$name" == "$workspace_name" ]]; then
        echo "$commit_id"
        return 0
      fi
    done
}

bookmark_change_id() {
  local bookmark_name="${1:?Error: bookmark_name required}"
  jj -R "$JJ_ROOT" bookmark list "exact:$bookmark_name" -T 'target.change_id() ++ "\n"' 2>/dev/null
}

create_workspace() {
  local spec_name="${1:?Error: spec_name required}"
  local exp_index="${2:?Error: exp_index required}"
  local base_bookmark="${3:?Error: base_bookmark required}"
  shift 3

  local padded_index
  padded_index=$(printf '%03d' "$exp_index")
  local workspace_name
  workspace_name=$(experiment_workspace_name "$spec_name" "$padded_index")
  local bookmark_name
  bookmark_name=$(experiment_bookmark_name "$spec_name" "$padded_index")
  local workspace_path="$WORKSPACE_DIR/$workspace_name"

  if [[ -d "$workspace_path" ]] && [[ -e "$workspace_path/.jj" ]] && is_registered_workspace "$workspace_name"; then
    local registered_commit
    registered_commit=$(registered_workspace_commit "$workspace_name")
    local workspace_commit
    workspace_commit=$(jj -R "$workspace_path" log -r @ --no-graph -T 'commit_id ++ "\n"' 2>/dev/null || true)
    local workspace_change
    workspace_change=$(jj -R "$workspace_path" log -r @ --no-graph -T 'change_id ++ "\n"' 2>/dev/null || true)
    local existing_bookmark_change
    existing_bookmark_change=$(bookmark_change_id "$bookmark_name" || true)

    if [[ -n "$workspace_commit" ]] && [[ "$workspace_commit" == "$registered_commit" ]] &&
       { [[ -z "$existing_bookmark_change" ]] || [[ "$existing_bookmark_change" == "$workspace_change" ]]; }; then
      if [[ -z "$existing_bookmark_change" ]]; then
        jj -R "$workspace_path" bookmark set "$bookmark_name" -r @ >/dev/null
      fi
      echo "$workspace_path"
      return 0
    fi
  fi

  if [[ -e "$workspace_path" ]] || is_registered_workspace "$workspace_name" || [[ -n "$(bookmark_change_id "$bookmark_name" || true)" ]]; then
    echo -e "${RED}Error: Experiment workspace collision: $workspace_path${NC}" >&2
    echo -e "${RED}The path, registered workspace, or bookmark does not identify one matching resumable experiment.${NC}" >&2
    return 1
  fi

  mkdir -p "$WORKSPACE_DIR"
  ensure_workspace_exclude
  jj -R "$JJ_ROOT" workspace add --name "$workspace_name" -r "$base_bookmark" "$workspace_path" >/dev/null
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

cleanup_workspace() {
  local spec_name="${1:?Error: spec_name required}"
  local exp_index="${2:?Error: exp_index required}"
  local padded_index
  padded_index=$(printf '%03d' "$exp_index")
  local workspace_name
  workspace_name=$(experiment_workspace_name "$spec_name" "$padded_index")
  local bookmark_name
  bookmark_name=$(experiment_bookmark_name "$spec_name" "$padded_index")
  local workspace_path="$WORKSPACE_DIR/$workspace_name"

  jj -R "$JJ_ROOT" bookmark forget "$bookmark_name" >/dev/null 2>&1 || true
  if is_registered_workspace "$workspace_name"; then
    jj -R "$JJ_ROOT" workspace forget "$workspace_name" >/dev/null
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
  experiment-worktree.sh create <spec_name> <exp_index> <base_bookmark> [shared_file ...]
  experiment-worktree.sh cleanup <spec_name> <exp_index>
  experiment-worktree.sh cleanup-all <spec_name>
  experiment-worktree.sh count

Commands:
  create       Create an experiment JJ workspace with copied shared files
  cleanup      Forget and remove one experiment workspace and bookmark
  cleanup-all  Forget and remove all experiment workspaces for a spec
  count        Count active experiment workspaces for budget checking

Workspaces: .worktrees/optimize-<spec>-exp-<NNN>/
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
