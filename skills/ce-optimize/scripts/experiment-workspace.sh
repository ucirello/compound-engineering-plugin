#!/bin/bash

# Experiment Workspace Manager
# Creates, cleans up, and manages JJ workspaces for optimization experiments.
# Each experiment gets an isolated workspace with copied shared resources.
#
# Usage:
#   experiment-workspace.sh create <spec_name> <exp_index> <base_bookmark> [shared_file ...]
#   experiment-workspace.sh cleanup <spec_name> <exp_index>
#   experiment-workspace.sh cleanup-all <spec_name>
#   experiment-workspace.sh count
#
# Workspaces are created at: .worktrees/optimize-<spec>-exp-<NNN>/
# Bookmarks are named: optimize-exp/<spec>/exp-<NNN>

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

REPO_ROOT=$(jj workspace root 2>/dev/null) || {
  echo -e "${RED}Error: Not in a Jujutsu repository${NC}" >&2
  exit 1
}

WORKSPACE_DIR="$REPO_ROOT/.worktrees"

experiment_bookmark_name() {
  local spec_name="${1:?Error: spec_name required}"
  local padded_index="${2:?Error: padded_index required}"

  # Keep experiment refs outside optimize/<spec> so they do not collide
  # with the long-lived optimization bookmark namespace.
  echo "optimize-exp/${spec_name}/exp-${padded_index}"
}

ensure_workspace_exclude() {
  local exclude_file
  local ignore_file_name
  ignore_file_name=".g""itignore"
  exclude_file="$REPO_ROOT/$ignore_file_name"

  mkdir -p "$(dirname "$exclude_file")"

  if ! grep -q "^\.worktrees$" "$exclude_file" 2>/dev/null; then
    echo ".worktrees" >> "$exclude_file"
  fi
}

is_registered_workspace() {
  local workspace_path="${1:?Error: workspace_path required}"

  jj workspace list 2>/dev/null | grep -F "$workspace_path" >/dev/null
}

is_bookmark_active() {
  local bookmark_name="${1:?Error: bookmark_name required}"

  jj log -r "${bookmark_name}" --no-graph --template 'change_id' >/dev/null 2>&1
}

reset_workspace_to_base() {
  local workspace_path="${1:?Error: workspace_path required}"
  local bookmark_name="${2:?Error: bookmark_name required}"
  local base_bookmark="${3:?Error: base_bookmark required}"
  local current_bookmark

  current_bookmark=$(jj --repository "$workspace_path" log -r @ --no-graph --template 'bookmarks.join(",")' 2>/dev/null || true)
  if [[ "$current_bookmark" != *"$bookmark_name"* ]]; then
    echo -e "${RED}Error: Existing workspace is on unexpected bookmark: ${current_bookmark:-none} (expected $bookmark_name)${NC}" >&2
    echo -e "${RED}Clean up the stale workspace before rerunning this experiment.${NC}" >&2
    return 1
  fi

  echo -e "${YELLOW}Resetting existing experiment workspace to base: $bookmark_name -> $base_bookmark${NC}" >&2
  jj --repository "$workspace_path" abandon @ >/dev/null 2>&1 || true
  jj --repository "$workspace_path" new "$base_bookmark" >/dev/null
  jj --repository "$workspace_path" bookmark set "$bookmark_name" -r @ >/dev/null
}

# Create an experiment workspace
create_workspace() {
  local spec_name="${1:?Error: spec_name required}"
  local exp_index="${2:?Error: exp_index required}"
  local base_bookmark="${3:?Error: base_bookmark required}"
  shift 3

  local padded_index
  padded_index=$(printf "%03d" "$exp_index")
  local workspace_name="optimize-${spec_name}-exp-${padded_index}"
  local bookmark_name
  bookmark_name=$(experiment_bookmark_name "$spec_name" "$padded_index")
  local workspace_path="$WORKSPACE_DIR/$workspace_name"

  # Check if workspace already exists
  if [[ -d "$workspace_path" ]]; then
    if ! jj --repository "$workspace_path" root >/dev/null 2>&1 || \
       ! is_registered_workspace "$workspace_path"; then
      echo -e "${RED}Error: Existing path is not a valid registered JJ workspace: $workspace_path${NC}" >&2
      echo -e "${RED}Remove or repair that directory before rerunning the experiment.${NC}" >&2
      return 1
    fi

    echo -e "${YELLOW}Workspace already exists: $workspace_path${NC}" >&2
    reset_workspace_to_base "$workspace_path" "$bookmark_name" "$base_bookmark"
  else
    mkdir -p "$WORKSPACE_DIR"
    ensure_workspace_exclude

    # Create workspace from the base bookmark.
    if ! jj workspace add --name "$workspace_name" "$workspace_path" "$base_bookmark" >/dev/null 2>&1; then
      if is_bookmark_active "$bookmark_name"; then
        if is_registered_workspace "$workspace_path"; then
          echo -e "${RED}Error: Existing experiment bookmark is already active: $bookmark_name${NC}" >&2
          echo -e "${RED}Clean up the stale workspace before rerunning this experiment.${NC}" >&2
          return 1
        fi

        echo -e "${YELLOW}Resetting existing experiment bookmark to base: $bookmark_name -> $base_bookmark${NC}" >&2
        jj bookmark set "$bookmark_name" -r "$base_bookmark" >/dev/null
        jj workspace add --name "$workspace_name" "$workspace_path" "$bookmark_name" >/dev/null
      else
        echo -e "${RED}Error: Failed to create workspace for $bookmark_name from $base_bookmark${NC}" >&2
        return 1
      fi
    fi
    jj --repository "$workspace_path" bookmark create "$bookmark_name" -r @ >/dev/null 2>&1 || jj --repository "$workspace_path" bookmark set "$bookmark_name" -r @ >/dev/null
  fi

  # Copy .env files from the main repo
  for f in "$REPO_ROOT"/.env*; do
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

# Clean up a single experiment workspace
cleanup_workspace() {
  local spec_name="${1:?Error: spec_name required}"
  local exp_index="${2:?Error: exp_index required}"

  local padded_index
  padded_index=$(printf "%03d" "$exp_index")
  local workspace_name="optimize-${spec_name}-exp-${padded_index}"
  local bookmark_name
  bookmark_name=$(experiment_bookmark_name "$spec_name" "$padded_index")
  local workspace_path="$WORKSPACE_DIR/$workspace_name"

  if [[ -d "$workspace_path" ]]; then
    jj workspace forget "$workspace_name" --repository "$workspace_path" >/dev/null 2>&1 || {
      # If workspace forget fails, try manual cleanup
      rm -rf "$workspace_path" 2>/dev/null || true
    }
  fi

  # Delete the experiment bookmark
  jj bookmark delete "$bookmark_name" 2>/dev/null || true

  echo -e "${GREEN}Cleaned up: $workspace_name${NC}" >&2
}

# Clean up all experiment workspaces for a spec
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
      # Extract index from name
      local index_str="${workspace_name#$prefix}"

      jj workspace forget "$workspace_name" --repository "$workspace_path" >/dev/null 2>&1 || {
        rm -rf "$workspace_path" 2>/dev/null || true
      }

      # Delete the bookmark
      local bookmark_name
      bookmark_name=$(experiment_bookmark_name "$spec_name" "$index_str")
      jj bookmark delete "$bookmark_name" 2>/dev/null || true

      count=$((count + 1))
    fi
  done

  # Clean up empty workspace directory
  if [[ -d "$WORKSPACE_DIR" ]] && [[ -z "$(ls -A "$WORKSPACE_DIR" 2>/dev/null)" ]]; then
    rmdir "$WORKSPACE_DIR" 2>/dev/null || true
  fi

  echo -e "${GREEN}Cleaned up $count experiment workspace(s) for $spec_name${NC}" >&2
}

# Count total workspaces (for budget check)
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
  experiment-workspace.sh create <spec_name> <exp_index> <base_bookmark> [shared_file ...]
  experiment-workspace.sh cleanup <spec_name> <exp_index>
  experiment-workspace.sh cleanup-all <spec_name>
  experiment-workspace.sh count

Commands:
  create       Create an experiment workspace with copied shared files
  cleanup      Remove a single experiment workspace and its bookmark
  cleanup-all  Remove all experiment workspaces for a spec
  count        Count total active workspaces (for budget checking)

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
