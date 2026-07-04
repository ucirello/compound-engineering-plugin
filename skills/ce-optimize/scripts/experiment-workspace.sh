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
# Workspaces are created at: .workspaces/optimize-<spec>-exp-<NNN>/
# Bookmarks are named: optimize-exp/<spec>/exp-<NNN>

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

REPO_ROOT=$(jj workspace root 2>/dev/null) || {
  echo -e "${RED}Error: Not in a jj workspace${NC}" >&2
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

ensure_workspace_exclude() {
  # Repository ignore configuration is project-owned; do not mutate it here.
  return 0
}

is_registered_workspace() {
  local workspace_path="${1:?Error: workspace_path required}"

  jj workspace list --template 'root ++ "\n"' | awk -v target="$workspace_path" '
    $0 == target { found = 1 }
    END { exit(found ? 0 : 1) }
  '
}

remove_existing_workspace() {
  local workspace_path="${1:?Error: workspace_path required}"
  local workspace_name="${2:?Error: workspace_name required}"

  echo -e "${YELLOW}Removing existing experiment workspace: $workspace_path${NC}" >&2
  jj workspace forget "$workspace_name" >/dev/null 2>&1 || true
  rm -rf "$workspace_path"
}

# Create an experiment workspace
create_workspace() {
  local spec_name="${1:?Error: spec_name required}"
  local exp_index="${2:?Error: exp_index required}"
  local base_bookmark="${3:?Error: base_bookmark required}"
  shift 3

  local padded_index
  padded_index=$(printf "%03d" "$exp_index")
  local workspace_dir_name="optimize-${spec_name}-exp-${padded_index}"
  local workspace_name="optimize-${spec_name}-exp-${padded_index}"
  local bookmark_name
  bookmark_name=$(experiment_bookmark_name "$spec_name" "$padded_index")
  local workspace_path="$WORKSPACE_DIR/$workspace_dir_name"

  # Check if workspace already exists
  if [[ -d "$workspace_path" ]]; then
    if ! jj -R "$workspace_path" workspace root >/dev/null 2>&1 || \
       ! is_registered_workspace "$workspace_path"; then
      echo -e "${RED}Error: Existing path is not a valid registered jj workspace: $workspace_path${NC}" >&2
      echo -e "${RED}Remove or repair that directory before rerunning the experiment.${NC}" >&2
      return 1
    fi

    echo -e "${YELLOW}Workspace already exists: $workspace_path${NC}" >&2
    remove_existing_workspace "$workspace_path" "$workspace_name"
  fi

  mkdir -p "$WORKSPACE_DIR"
  ensure_workspace_exclude

  if jj workspace list --template 'name ++ "\n"' | grep -qx "$workspace_name"; then
    jj workspace forget "$workspace_name" >/dev/null 2>&1 || true
  fi
  jj bookmark delete "$bookmark_name" >/dev/null 2>&1 || true

  if ! jj workspace add --name "$workspace_name" "$workspace_path" -r "$base_bookmark" >/dev/null 2>&1; then
    echo -e "${RED}Error: Failed to create workspace $workspace_name from $base_bookmark${NC}" >&2
    return 1
  fi
  jj -R "$workspace_path" bookmark set "$bookmark_name" -r @ >/dev/null

  # Copy .env files from main repo
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
  local workspace_dir_name="optimize-${spec_name}-exp-${padded_index}"
  local workspace_name="optimize-${spec_name}-exp-${padded_index}"
  local bookmark_name
  bookmark_name=$(experiment_bookmark_name "$spec_name" "$padded_index")
  local workspace_path="$WORKSPACE_DIR/$workspace_dir_name"

  if [[ -d "$workspace_path" ]]; then
    jj workspace forget "$workspace_name" >/dev/null 2>&1 || true
    rm -rf "$workspace_path" 2>/dev/null || true
  fi

  # Delete the experiment bookmark.
  jj bookmark delete "$bookmark_name" >/dev/null 2>&1 || true

  echo -e "${GREEN}Cleaned up: $workspace_dir_name${NC}" >&2
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
      local workspace_dir_name
      workspace_dir_name=$(basename "$workspace_path")
      # Extract index from name
      local index_str="${workspace_dir_name#$prefix}"

      jj workspace forget "$workspace_dir_name" >/dev/null 2>&1 || true
      rm -rf "$workspace_path" 2>/dev/null || true

      # Delete the bookmark.
      local bookmark_name
      bookmark_name=$(experiment_bookmark_name "$spec_name" "$index_str")
      jj bookmark delete "$bookmark_name" >/dev/null 2>&1 || true

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
      if [[ -d "$workspace_path" ]] && jj -R "$workspace_path" workspace root >/dev/null 2>&1; then
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
  create       Create an experiment JJ workspace with copied shared files
  cleanup      Remove a single experiment workspace and its bookmark
  cleanup-all  Remove all experiment workspaces for a spec
  count        Count total active workspaces (for budget checking)

Workspaces: .workspaces/optimize-<spec>-exp-<NNN>/
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
