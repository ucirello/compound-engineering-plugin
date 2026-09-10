#!/bin/bash

# Experiment Workspace Manager
# Creates, cleans up, and manages jj workspaces for optimization experiments.
# Each experiment gets an isolated workspace with copied shared resources.
#
# Usage:
#   experiment-worktree.sh create <spec_name> <exp_index> <base_bookmark> [shared_file ...]
#   experiment-worktree.sh cleanup <spec_name> <exp_index>
#   experiment-worktree.sh cleanup-all <spec_name>
#   experiment-worktree.sh count
#
# Workspaces are created at: .tmp/worktrees/optimize-<spec>-exp-<NNN>/
# Bookmarks are named: optimize-exp/<spec>/exp-<NNN>

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

WS_ROOT=$(jj workspace root 2>/dev/null) || {
  echo -e "${RED}Error: Not in a jj workspace${NC}" >&2
  exit 1
}

WORKTREE_DIR="$WS_ROOT/.tmp/worktrees"

experiment_bookmark_name() {
  local spec_name="${1:?Error: spec_name required}"
  local padded_index="${2:?Error: padded_index required}"

  # Keep experiment refs outside optimize/<spec> so they do not collide
  # with the long-lived optimization bookmark namespace.
  echo "optimize-exp/${spec_name}/exp-${padded_index}"
}

is_registered_workspace() {
  local workspace_name="${1:?Error: workspace_name required}"
  local workspace_path="${2:?Error: workspace_path required}"
  local registered

  registered=$( (cd "$WS_ROOT" && jj workspace root --name "$workspace_name") 2>/dev/null ) || return 1
  local a b
  a=$(cd "$workspace_path" && pwd -P)
  b=$(cd "$registered" && pwd -P)
  [[ "$a" == "$b" ]]
}

is_bookmark_in_a_workspace() {
  local bookmark_name="${1:?Error: bookmark_name required}"
  local name root marks

  while IFS=$'\t' read -r name root; do
    [[ -z "${name:-}" || -z "${root:-}" ]] && continue
    [[ -d "$root" ]] || continue
    marks=$( (cd "$root" && jj log -r @ -T 'bookmarks.join("\n")' --no-graph) 2>/dev/null || true )
    if printf '%s\n' "$marks" | grep -qx "$bookmark_name"; then
      return 0
    fi
  done < <( (cd "$WS_ROOT" && jj workspace list -T 'name ++ "\t" ++ root ++ "\n"') )
  return 1
}

reset_workspace_to_base() {
  local workspace_path="${1:?Error: workspace_path required}"
  local bookmark_name="${2:?Error: bookmark_name required}"
  local base_bookmark="${3:?Error: base_bookmark required}"
  local current_bookmarks

  current_bookmarks=$( (cd "$workspace_path" && jj log -r @ -T 'bookmarks.join("\n")' --no-graph) 2>/dev/null || true )
  if ! printf '%s\n' "$current_bookmarks" | grep -qx "$bookmark_name"; then
    echo -e "${RED}Error: Existing workspace is on unexpected bookmark: ${current_bookmarks:-none} (expected $bookmark_name)${NC}" >&2
    echo -e "${RED}Clean up the stale workspace before rerunning this experiment.${NC}" >&2
    return 1
  fi

  echo -e "${YELLOW}Resetting existing experiment workspace to base: $bookmark_name -> $base_bookmark${NC}" >&2
  (cd "$workspace_path" && jj new "$base_bookmark")
  (cd "$workspace_path" && jj bookmark set "$bookmark_name" -r @ --allow-backwards)
}

forget_workspace_and_dir() {
  local workspace_name="${1:?Error: workspace_name required}"
  local workspace_path="${2:?Error: workspace_path required}"

  (cd "$WS_ROOT" && jj workspace forget "$workspace_name") 2>/dev/null || true
  if [[ -d "$workspace_path" ]]; then
    rm -rf "$workspace_path" 2>/dev/null || true
  fi
}

# Create an experiment workspace
create_worktree() {
  local spec_name="${1:?Error: spec_name required}"
  local exp_index="${2:?Error: exp_index required}"
  local base_bookmark="${3:?Error: base_bookmark required}"
  shift 3

  local padded_index
  padded_index=$(printf "%03d" "$exp_index")
  local workspace_name="optimize-${spec_name}-exp-${padded_index}"
  local bookmark_name
  bookmark_name=$(experiment_bookmark_name "$spec_name" "$padded_index")
  local workspace_path="$WORKTREE_DIR/$workspace_name"

  # Check if workspace already exists
  if [[ -d "$workspace_path" ]]; then
    if ! is_registered_workspace "$workspace_name" "$workspace_path"; then
      echo -e "${RED}Error: Existing path is not a valid registered jj workspace: $workspace_path${NC}" >&2
      echo -e "${RED}Remove or repair that directory before rerunning the experiment.${NC}" >&2
      return 1
    fi

    echo -e "${YELLOW}Workspace already exists: $workspace_path${NC}" >&2
    reset_workspace_to_base "$workspace_path" "$bookmark_name" "$base_bookmark"
  else
    mkdir -p "$WORKTREE_DIR"

    # Create workspace from the base bookmark
    if ! (cd "$WS_ROOT" && jj workspace add --name "$workspace_name" -r "$base_bookmark" "$workspace_path"); then
      if (cd "$WS_ROOT" && jj log -r "$bookmark_name" -n 1 --no-graph >/dev/null 2>&1); then
        if is_bookmark_in_a_workspace "$bookmark_name"; then
          echo -e "${RED}Error: Existing experiment bookmark is already checked out: $bookmark_name${NC}" >&2
          echo -e "${RED}Clean up the stale workspace before rerunning this experiment.${NC}" >&2
          return 1
        fi

        echo -e "${YELLOW}Resetting existing experiment bookmark to base: $bookmark_name -> $base_bookmark${NC}" >&2
        (cd "$WS_ROOT" && jj bookmark set "$bookmark_name" -r "$base_bookmark" --allow-backwards)
        (cd "$WS_ROOT" && jj workspace add --name "$workspace_name" -r "$bookmark_name" "$workspace_path")
      else
        echo -e "${RED}Error: Failed to create workspace for $bookmark_name from $base_bookmark${NC}" >&2
        return 1
      fi
    fi

    (cd "$workspace_path" && jj bookmark set "$bookmark_name" -r @ --allow-backwards)
  fi

  # Copy .env files from main workspace
  for f in "$WS_ROOT"/.env*; do
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
    if [[ -f "$WS_ROOT/$shared_file" ]]; then
      local dir
      dir=$(dirname "$workspace_path/$shared_file")
      mkdir -p "$dir"
      cp "$WS_ROOT/$shared_file" "$workspace_path/$shared_file"
    elif [[ -d "$WS_ROOT/$shared_file" ]]; then
      local dir
      dir=$(dirname "$workspace_path/$shared_file")
      mkdir -p "$dir"
      rm -rf "$workspace_path/$shared_file"
      cp -R "$WS_ROOT/$shared_file" "$workspace_path/$shared_file"
    fi
  done

  echo "$workspace_path"
}

# Clean up a single experiment workspace
cleanup_worktree() {
  local spec_name="${1:?Error: spec_name required}"
  local exp_index="${2:?Error: exp_index required}"

  local padded_index
  padded_index=$(printf "%03d" "$exp_index")
  local workspace_name="optimize-${spec_name}-exp-${padded_index}"
  local bookmark_name
  bookmark_name=$(experiment_bookmark_name "$spec_name" "$padded_index")
  local workspace_path="$WORKTREE_DIR/$workspace_name"

  forget_workspace_and_dir "$workspace_name" "$workspace_path"

  # Forget the experiment bookmark (local-only; do not propagate a deletion)
  (cd "$WS_ROOT" && jj bookmark forget "$bookmark_name") 2>/dev/null || true

  echo -e "${GREEN}Cleaned up: $workspace_name${NC}" >&2
}

# Clean up all experiment workspaces for a spec
cleanup_all() {
  local spec_name="${1:?Error: spec_name required}"
  local prefix="optimize-${spec_name}-exp-"
  local count=0

  if [[ ! -d "$WORKTREE_DIR" ]]; then
    echo -e "${YELLOW}No workspaces directory found${NC}" >&2
    return 0
  fi

  for workspace_path in "$WORKTREE_DIR"/${prefix}*; do
    if [[ -d "$workspace_path" ]]; then
      local workspace_name
      workspace_name=$(basename "$workspace_path")
      # Extract index from name
      local index_str="${workspace_name#$prefix}"

      forget_workspace_and_dir "$workspace_name" "$workspace_path"

      # Forget the bookmark
      local bookmark_name
      bookmark_name=$(experiment_bookmark_name "$spec_name" "$index_str")
      (cd "$WS_ROOT" && jj bookmark forget "$bookmark_name") 2>/dev/null || true

      count=$((count + 1))
    fi
  done

  # Clean up empty workspace directory
  if [[ -d "$WORKTREE_DIR" ]] && [[ -z "$(ls -A "$WORKTREE_DIR" 2>/dev/null)" ]]; then
    rmdir "$WORKTREE_DIR" 2>/dev/null || true
  fi

  echo -e "${GREEN}Cleaned up $count experiment workspace(s) for $spec_name${NC}" >&2
}

# Count total experiment workspaces (for budget check)
count_worktrees() {
  local count=0
  local name root

  while IFS=$'\t' read -r name root; do
    [[ -z "${name:-}" || -z "${root:-}" ]] && continue
    case "$root" in
      "$WORKTREE_DIR"/*) count=$((count + 1)) ;;
    esac
  done < <( (cd "$WS_ROOT" && jj workspace list -T 'name ++ "\t" ++ root ++ "\n"') )
  echo "$count"
}

# Main
main() {
  local command="${1:-help}"

  case "$command" in
    create)
      shift
      create_worktree "$@"
      ;;
    cleanup)
      shift
      cleanup_worktree "$@"
      ;;
    cleanup-all)
      shift
      cleanup_all "$@"
      ;;
    count)
      count_worktrees
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
  cleanup      Remove a single experiment workspace and its bookmark
  cleanup-all  Remove all experiment workspaces for a spec
  count        Count total active experiment workspaces (for budget checking)

Workspaces: .tmp/worktrees/optimize-<spec>-exp-<NNN>/
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
