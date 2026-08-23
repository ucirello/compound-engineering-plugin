#!/bin/bash

# Experiment Workspace Manager
# Creates, cleans up, and manages Jujutsu workspaces for optimization experiments.
# Each experiment gets an isolated workspace with copied shared resources.
#
# Usage:
#   experiment-workspace.sh create <spec_name> <exp_index> <base_revision> [shared_file ...]
#   experiment-workspace.sh cleanup <spec_name> <exp_index> [keep|abandon]
#   experiment-workspace.sh cleanup-all <spec_name>
#   experiment-workspace.sh count
#
# Workspaces are created at: .tmp/optimize/workspaces/optimize-<spec>-exp-<NNN>/

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

JJ_ROOT=$(jj workspace root 2>/dev/null) || {
  echo -e "${RED}Error: Not in a Jujutsu workspace${NC}" >&2
  exit 1
}

TEMP_ROOT="$JJ_ROOT/.tmp"
WORKSPACE_DIR="$TEMP_ROOT/optimize/workspaces"

experiment_workspace_name() {
  local spec_name="${1:?Error: spec_name required}"
  local padded_index="${2:?Error: padded_index required}"
  echo "optimize-${spec_name}-exp-${padded_index}"
}

ensure_temp_root() {
  local path owner mode current_uid
  current_uid=$(id -u)
  umask 077
  for path in "$TEMP_ROOT" "$TEMP_ROOT/optimize" "$WORKSPACE_DIR"; do
    if [[ -L "$path" ]]; then
      echo -e "${RED}Error: Refusing symlinked managed path: $path${NC}" >&2
      return 1
    fi
    if [[ ! -e "$path" ]]; then
      mkdir "$path" || return 1
    fi
    if [[ ! -d "$path" || -L "$path" ]]; then
      echo -e "${RED}Error: Managed path is not a real directory: $path${NC}" >&2
      return 1
    fi
    owner=$(stat -f '%u' "$path" 2>/dev/null || stat -c '%u' "$path" 2>/dev/null) || {
      echo -e "${RED}Error: Could not verify managed path ownership: $path${NC}" >&2
      return 1
    }
    if [[ "$owner" != "$current_uid" ]]; then
      echo -e "${RED}Error: Managed path is not owned by the current user: $path${NC}" >&2
      return 1
    fi
    chmod 700 "$path" || {
      echo -e "${RED}Error: Could not make managed path private: $path${NC}" >&2
      return 1
    }
    mode=$(stat -f '%Lp' "$path" 2>/dev/null || stat -c '%a' "$path" 2>/dev/null) || {
      echo -e "${RED}Error: Could not verify managed path privacy: $path${NC}" >&2
      return 1
    }
    if [[ "$mode" != "700" ]]; then
      echo -e "${RED}Error: Managed path is not private (mode $mode): $path${NC}" >&2
      return 1
    fi
  done

}

# Create an experiment workspace
create_workspace() {
  local spec_name="${1:?Error: spec_name required}"
  local exp_index="${2:?Error: exp_index required}"
  local base_revision="${3:?Error: base_revision required}"
  shift 3

  local padded_index
  padded_index=$(printf "%03d" "$exp_index")
  local workspace_name
  workspace_name=$(experiment_workspace_name "$spec_name" "$padded_index")
  local workspace_path="$WORKSPACE_DIR/optimize-${spec_name}-exp-${padded_index}"

  ensure_temp_root
  if [[ -e "$workspace_path" || -L "$workspace_path" ]]; then
    echo -e "${RED}Error: Experiment workspace path already exists: $workspace_path${NC}" >&2
    echo -e "${RED}Clean up or recover that workspace before rerunning the experiment.${NC}" >&2
    return 1
  fi

  jj -R "$JJ_ROOT" workspace add --name "$workspace_name" -r "$base_revision" "$workspace_path" >/dev/null

  # Copy .env files from the primary workspace
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
      cp -R "$JJ_ROOT/$shared_file" "$workspace_path/$shared_file"
    fi
  done

  echo "$workspace_path"
}

# Clean up a single experiment workspace
cleanup_workspace() {
  local spec_name="${1:?Error: spec_name required}"
  local exp_index="${2:?Error: exp_index required}"
  local disposition="${3:-abandon}"

  local padded_index
  padded_index=$(printf "%03d" "$exp_index")
  local workspace_name
  workspace_name=$(experiment_workspace_name "$spec_name" "$padded_index")
  local workspace_path="$WORKSPACE_DIR/optimize-${spec_name}-exp-${padded_index}"

  case "$disposition" in
    keep|abandon) ;;
    *)
      echo -e "${RED}Error: cleanup disposition must be keep or abandon${NC}" >&2
      return 1
      ;;
  esac

  if [[ -d "$workspace_path" ]]; then
    if [[ "$disposition" == "abandon" ]]; then
      local change_id
      change_id=$(jj -R "$workspace_path" log -r @ --no-graph -T 'change_id ++ "\n"')
      jj -R "$JJ_ROOT" abandon "$change_id" >/dev/null
    fi
    jj -R "$JJ_ROOT" workspace forget "$workspace_name" >/dev/null
    case "$workspace_path" in
      "$WORKSPACE_DIR"/*) rm -rf "$workspace_path" ;;
      *) echo -e "${RED}Error: Refusing cleanup outside managed workspace root${NC}" >&2; return 1 ;;
    esac
  else
    jj -R "$JJ_ROOT" workspace forget "$workspace_name" >/dev/null 2>&1 || true
  fi

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

  for workspace_path in "$WORKSPACE_DIR"/${prefix}*; do
    if [[ -d "$workspace_path" ]]; then
      local workspace_name_on_disk
      workspace_name_on_disk=$(basename "$workspace_path")
      local index_str="${workspace_name_on_disk#$prefix}"
      cleanup_workspace "$spec_name" "$((10#$index_str))" abandon
      count=$((count + 1))
    fi
  done

  if [[ -d "$WORKSPACE_DIR" ]] && [[ -z "$(ls -A "$WORKSPACE_DIR" 2>/dev/null)" ]]; then
    rmdir "$WORKSPACE_DIR" 2>/dev/null || true
  fi

  echo -e "${GREEN}Cleaned up $count experiment workspace(s) for $spec_name${NC}" >&2
}

# Count total experiment workspaces (for budget check)
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
  experiment-workspace.sh create <spec_name> <exp_index> <base_revision> [shared_file ...]
  experiment-workspace.sh cleanup <spec_name> <exp_index> [keep|abandon]
  experiment-workspace.sh cleanup-all <spec_name>
  experiment-workspace.sh count

Commands:
  create       Create an experiment workspace with copied shared files
  cleanup      Remove a workspace, preserving or abandoning its change
  cleanup-all  Abandon and remove all experiment workspaces for a spec
  count        Count total active experiment workspaces

Workspaces: .tmp/optimize/workspaces/optimize-<spec>-exp-<NNN>/
EOF
      ;;
    *)
      echo -e "${RED}Unknown command: $command${NC}" >&2
      exit 1
      ;;
  esac
}

main "$@"
