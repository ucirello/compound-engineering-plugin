#!/bin/bash

# JJ Experiment Workspace Manager
# Creates, cleans up, and manages isolated workspaces for optimization experiments.
#
# Usage:
#   experiment-worktree.sh create <spec_name> <exp_index> <base_bookmark> [shared_file ...]
#   experiment-worktree.sh cleanup <spec_name> <exp_index>
#   experiment-worktree.sh cleanup-all <spec_name>
#   experiment-worktree.sh count
#
# Workspaces are created under: .tmp/rocketclaw/ce-optimize/workspaces/
# Temporary bookmarks are named: optimize-exp/<spec>/exp-<NNN>

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

WORKSPACE_ROOT=$(jj workspace root 2>/dev/null) || {
  echo -e "${RED}Error: Not in a JJ workspace${NC}" >&2
  exit 1
}

CANONICAL_ROOT=$(cd "$WORKSPACE_ROOT" && pwd -P)
REPO_KEY=$(printf '%s' "$CANONICAL_ROOT" | cksum | cut -d ' ' -f 1)
MANAGED_DIR="$CANONICAL_ROOT/.tmp/rocketclaw/ce-optimize/workspaces/$REPO_KEY"

ensure_managed_dir() {
  local path="$CANONICAL_ROOT"
  local component
  for component in .tmp rocketclaw ce-optimize workspaces "$REPO_KEY"; do
    path="$path/$component"
    if [[ -L "$path" ]]; then
      echo -e "${RED}Error: Refusing symlinked scratch path component: $path${NC}" >&2
      return 1
    fi
    mkdir -p "$path"
  done
}

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

workspace_name() {
  local spec_name="${1:?Error: spec_name required}"
  local padded_index="${2:?Error: padded_index required}"
  printf 'optimize-%s-exp-%s\n' "$spec_name" "$padded_index"
}

experiment_bookmark() {
  local spec_name="${1:?Error: spec_name required}"
  local padded_index="${2:?Error: padded_index required}"
  printf 'optimize-exp/%s/exp-%s\n' "$spec_name" "$padded_index"
}

# Create an isolated experiment workspace and change.
create_workspace() {
  local spec_name="${1:?Error: spec_name required}"
  local exp_index="${2:?Error: exp_index required}"
  local base_bookmark="${3:?Error: base_bookmark required}"
  shift 3
  validate_spec_name "$spec_name"

  local padded_index
  padded_index=$(printf "%03d" "$exp_index")
  local name
  name=$(workspace_name "$spec_name" "$padded_index")
  local bookmark
  bookmark=$(experiment_bookmark "$spec_name" "$padded_index")
  local workspace_path="$MANAGED_DIR/$name"

  local registered_path
  if registered_path=$(registered_workspace_path "$name"); then
    echo -e "${RED}Error: Experiment workspace is already registered: $registered_path${NC}" >&2
    echo -e "${RED}Resume it or explicitly clean it up before rerunning this experiment.${NC}" >&2
    return 1
  elif [[ -e "$workspace_path" ]]; then
    echo -e "${RED}Error: Managed experiment workspace already exists: $workspace_path${NC}" >&2
    echo -e "${RED}Clean it up before rerunning this experiment.${NC}" >&2
    return 1
  fi

  if jj bookmark list "$bookmark" -T 'name ++ "\n"' 2>/dev/null | grep -Fxq "$bookmark"; then
    echo -e "${RED}Error: Temporary experiment bookmark already exists: $bookmark${NC}" >&2
    echo -e "${RED}Clean up or preserve that change explicitly before rerunning this experiment.${NC}" >&2
    return 1
  fi

  ensure_managed_dir
  jj workspace add --name "$name" -r "$base_bookmark" "$workspace_path" >/dev/null
  jj -R "$workspace_path" bookmark create "$bookmark" -r @ >/dev/null

  for f in "$WORKSPACE_ROOT"/.env*; do
    if [[ -f "$f" ]]; then
      local basename
      basename=$(basename "$f")
      if [[ "$basename" != ".env.example" ]]; then
        cp "$f" "$workspace_path/$basename"
      fi
    fi
  done

  for shared_file in "$@"; do
    if [[ -f "$WORKSPACE_ROOT/$shared_file" ]]; then
      mkdir -p "$(dirname "$workspace_path/$shared_file")"
      cp "$WORKSPACE_ROOT/$shared_file" "$workspace_path/$shared_file"
    elif [[ -d "$WORKSPACE_ROOT/$shared_file" ]]; then
      mkdir -p "$(dirname "$workspace_path/$shared_file")"
      cp -R "$WORKSPACE_ROOT/$shared_file" "$workspace_path/$shared_file"
    fi
  done

  printf '%s\n' "$workspace_path"
}

cleanup_workspace() {
  local spec_name="${1:?Error: spec_name required}"
  local exp_index="${2:?Error: exp_index required}"
  validate_spec_name "$spec_name"

  local padded_index
  padded_index=$(printf "%03d" "$exp_index")
  local name
  name=$(workspace_name "$spec_name" "$padded_index")
  local bookmark
  bookmark=$(experiment_bookmark "$spec_name" "$padded_index")
  local workspace_path="$MANAGED_DIR/$name"

  local registered_path registered_canonical expected_canonical change_id=""
  if registered_path=$(registered_workspace_path "$name"); then
    registered_canonical=$(canonical_path "$registered_path") || return 1
    expected_canonical=$(canonical_path "$workspace_path") || return 1
    if [[ "$registered_canonical" != "$expected_canonical" ]]; then
      echo -e "${RED}Error: Refusing cleanup because the registered workspace path differs from the managed path${NC}" >&2
      return 1
    fi
    change_id=$(jj -R "$registered_canonical" log -r @ --no-graph -T 'change_id ++ "\n"' 2>/dev/null || true)
    jj bookmark delete "$bookmark" >/dev/null 2>&1 || true
    jj workspace forget "$name" >/dev/null
    rm -rf -- "$registered_canonical"
    if [[ -n "$change_id" ]] && [[ -z "$(jj bookmark list -r "$change_id" -T 'name ++ "\n"' 2>/dev/null)" ]]; then
      jj abandon "$change_id" >/dev/null 2>&1 || true
    fi
  elif [[ -e "$workspace_path" ]]; then
    echo -e "${RED}Error: Refusing to remove an unregistered path: $workspace_path${NC}" >&2
    return 1
  fi

  echo -e "${GREEN}Cleaned up: $name${NC}" >&2
}

cleanup_all() {
  local spec_name="${1:?Error: spec_name required}"
  validate_spec_name "$spec_name"
  local prefix="optimize-${spec_name}-exp-"
  local count=0

  if [[ ! -d "$MANAGED_DIR" ]]; then
    echo -e "${YELLOW}No managed experiment workspaces found${NC}" >&2
    return 0
  fi

  for workspace_path in "$MANAGED_DIR"/${prefix}*; do
    if [[ -d "$workspace_path" ]]; then
      local name
      name=$(basename "$workspace_path")
      local index="${name#$prefix}"
      cleanup_workspace "$spec_name" "$((10#$index))"
      count=$((count + 1))
    fi
  done

  rmdir "$MANAGED_DIR" 2>/dev/null || true
  echo -e "${GREEN}Cleaned up $count experiment workspace(s) for $spec_name${NC}" >&2
}

count_workspaces() {
  local count=0
  if [[ -d "$MANAGED_DIR" ]]; then
    for workspace_path in "$MANAGED_DIR"/*; do
      if [[ -d "$workspace_path" ]] && [[ -e "$workspace_path/.jj" ]]; then
        count=$((count + 1))
      fi
    done
  fi
  printf '%s\n' "$count"
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
JJ Experiment Workspace Manager

Usage:
  experiment-worktree.sh create <spec_name> <exp_index> <base_bookmark> [shared_file ...]
  experiment-worktree.sh cleanup <spec_name> <exp_index>
  experiment-worktree.sh cleanup-all <spec_name>
  experiment-worktree.sh count

Commands:
  create       Create an isolated experiment workspace and change
  cleanup      Forget and remove one managed experiment workspace
  cleanup-all  Forget and remove all managed experiment workspaces for a spec
  count        Count managed experiment workspaces
EOF
      ;;
    *)
      echo -e "${RED}Unknown command: $command${NC}" >&2
      exit 1
      ;;
  esac
}

main "$@"
