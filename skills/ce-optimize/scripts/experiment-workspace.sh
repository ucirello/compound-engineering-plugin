#!/bin/bash

# Experiment Workspace Manager
# Creates, cleans up, and manages JJ workspaces for optimization experiments.
# Each experiment gets an isolated working-copy change and copied resources.
#
# Usage:
#   experiment-workspace.sh create <spec_name> <exp_index> <base_rev> [shared_file ...]
#   experiment-workspace.sh cleanup <spec_name> <exp_index>
#   experiment-workspace.sh cleanup-all <spec_name>
#   experiment-workspace.sh count
#
# Workspaces are created under the repository's ignored local scratch directory.

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

JJ_ROOT=$(jj workspace root 2>/dev/null) || {
  echo -e "${RED}Error: Not in a JJ workspace${NC}" >&2
  exit 1
}

canonical_root=$(cd "$JJ_ROOT" && pwd -P)
repo_key=$(printf '%s' "$canonical_root" | cksum | cut -d ' ' -f 1)
WORKSPACE_DIR="$canonical_root/.tmp/rocketclaw/optimize/workspaces/$repo_key"

validate_spec_name() {
  local spec_name="${1:?Error: spec_name required}"
  if [[ ! "$spec_name" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]]; then
    echo -e "${RED}Error: Invalid spec name: $spec_name${NC}" >&2
    return 1
  fi
}

canonical_path() {
  local path="${1:?Error: path required}"
  local parent
  parent=$(cd "$(dirname "$path")" 2>/dev/null && pwd -P) || return 1
  printf '%s/%s\n' "$parent" "$(basename "$path")"
}

registered_workspace_path() {
  local wanted_name="${1:?Error: workspace_name required}"
  local name path

  while IFS=$'\t' read -r name path; do
    if [[ "$name" == "$wanted_name" ]]; then
      printf '%s\n' "$path"
      return 0
    fi
  done < <(jj workspace list -T 'name ++ "\t" ++ root ++ "\n"')
  return 1
}

# Snapshot, forget, and remove a workspace. Abandon its change unless a
# bookmark preserves it as an accepted result.
discard_workspace() {
  local workspace_name="${1:?Error: workspace_name required}"
  local workspace_path="${2:?Error: workspace_path required}"
  local revision_id=""
  local registered_path expected_path registered_canonical expected_canonical

  if ! registered_path=$(registered_workspace_path "$workspace_name"); then
    echo -e "${RED}Error: Refusing cleanup of unregistered workspace path: $workspace_path${NC}" >&2
    return 1
  fi

  expected_path=$(canonical_path "$workspace_path") || {
    echo -e "${RED}Error: Cannot canonicalize expected workspace path: $workspace_path${NC}" >&2
    return 1
  }
  registered_canonical=$(canonical_path "$registered_path") || {
    echo -e "${RED}Error: Cannot canonicalize registered workspace path: $registered_path${NC}" >&2
    return 1
  }
  expected_canonical=$(canonical_path "$expected_path")

  if [[ "$registered_canonical" != "$expected_canonical" ]]; then
    echo -e "${RED}Error: Refusing cleanup: registered root '$registered_canonical' does not equal expected root '$expected_canonical'${NC}" >&2
    return 1
  fi

  if [[ -d "$expected_canonical" ]]; then
    jj -R "$expected_canonical" status >/dev/null 2>&1 || true
    revision_id=$(jj -R "$expected_canonical" log -r @ --no-graph -T commit_id 2>/dev/null || true)
  fi

  jj workspace forget "$workspace_name"
  if [[ -d "$expected_canonical" ]]; then
    rm -rf -- "$expected_canonical"
  fi

  if [[ -n "$revision_id" ]] && [[ -z "$(jj bookmark list -r "$revision_id" -T 'name ++ "\n"' 2>/dev/null)" ]]; then
    jj abandon "$revision_id" >/dev/null 2>&1 || true
  fi
}

create_workspace() {
  local spec_name="${1:?Error: spec_name required}"
  local exp_index="${2:?Error: exp_index required}"
  local base_rev="${3:?Error: base_rev required}"
  shift 3

  validate_spec_name "$spec_name"

  local padded_index
  padded_index=$(printf "%03d" "$exp_index")
  local workspace_name="optimize-${spec_name}-exp-${padded_index}"
  local workspace_path="$WORKSPACE_DIR/$workspace_name"

  if registered_workspace_path "$workspace_name" >/dev/null 2>&1; then
    echo -e "${YELLOW}Workspace is already registered; recreating: $workspace_path${NC}" >&2
    discard_workspace "$workspace_name" "$workspace_path"
  elif [[ -e "$workspace_path" ]]; then
    echo -e "${RED}Error: Refusing to replace unregistered path: $workspace_path${NC}" >&2
    return 1
  fi

  mkdir -p "$WORKSPACE_DIR"

  if ! jj workspace add --name "$workspace_name" -r "$base_rev" "$workspace_path" >/dev/null; then
    echo -e "${RED}Error: Failed to create workspace $workspace_name from $base_rev${NC}" >&2
    return 1
  fi

  # Copy untracked environment files from the coordinating workspace.
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
  validate_spec_name "$spec_name"

  local padded_index
  padded_index=$(printf "%03d" "$exp_index")
  local workspace_name="optimize-${spec_name}-exp-${padded_index}"
  local workspace_path="$WORKSPACE_DIR/$workspace_name"

  if registered_workspace_path "$workspace_name" >/dev/null 2>&1; then
    discard_workspace "$workspace_name" "$workspace_path"
  elif [[ -e "$workspace_path" ]]; then
    echo -e "${RED}Error: Refusing to remove unregistered path: $workspace_path${NC}" >&2
    return 1
  fi

  echo -e "${GREEN}Cleaned up: $workspace_name${NC}" >&2
}

cleanup_all() {
  local spec_name="${1:?Error: spec_name required}"
  validate_spec_name "$spec_name"
  local prefix="optimize-${spec_name}-exp-"
  local count=0

  local workspace_name registered_path
  while IFS=$'\t' read -r workspace_name registered_path; do
    if [[ "$workspace_name" == "$prefix"* ]]; then
      discard_workspace "$workspace_name" "$WORKSPACE_DIR/$workspace_name"
      count=$((count + 1))
    fi
  done < <(jj workspace list -T 'name ++ "\t" ++ root ++ "\n"')

  if [[ -d "$WORKSPACE_DIR" ]] && [[ -z "$(ls -A "$WORKSPACE_DIR" 2>/dev/null)" ]]; then
    rmdir "$WORKSPACE_DIR" 2>/dev/null || true
  fi

  echo -e "${GREEN}Cleaned up $count experiment workspace(s) for $spec_name${NC}" >&2
}

count_workspaces() {
  jj workspace list -T 'name ++ "\n"' | grep -c '^optimize-.*-exp-[0-9][0-9][0-9]$' || true
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
  experiment-workspace.sh create <spec_name> <exp_index> <base_rev> [shared_file ...]
  experiment-workspace.sh cleanup <spec_name> <exp_index>
  experiment-workspace.sh cleanup-all <spec_name>
  experiment-workspace.sh count

Commands:
  create       Create an isolated experiment workspace and working-copy change
  cleanup      Remove a workspace; abandon its change unless bookmarked
  cleanup-all  Remove all experiment workspaces for a spec
  count        Count active experiment workspaces (for budget checking)

Workspaces: <workspace-root>/.tmp/rocketclaw/optimize/workspaces/<repo-key>/optimize-<spec>-exp-<NNN>/
EOF
      ;;
    *)
      echo -e "${RED}Unknown command: $command${NC}" >&2
      exit 1
      ;;
  esac
}

main "$@"
