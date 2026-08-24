#!/bin/bash

# Manages isolated Jujutsu workspaces for optimization experiments.
# Usage:
#   experiment-workspace.sh create <spec_name> <exp_index> <base_revision> [shared_file ...]
#   experiment-workspace.sh cleanup <spec_name> <exp_index>
#   experiment-workspace.sh cleanup-all <spec_name>
#   experiment-workspace.sh count

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

JJ_ROOT=$(jj workspace root 2>/dev/null) || {
  echo -e "${RED}Error: Not in a Jujutsu workspace${NC}" >&2
  exit 1
}
JJ_ROOT=$(cd "$JJ_ROOT" && pwd -P)
REPO_KEY=$(printf '%s' "$JJ_ROOT" | cksum | cut -d ' ' -f 1)
TMP_ROOT="$JJ_ROOT/.tmp"
WORKSPACE_DIR="$TMP_ROOT/rocketclaw/optimize/workspaces/$REPO_KEY"

validate_spec_name() {
  local spec_name="${1:?Error: spec_name required}"
  if [[ ! "$spec_name" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]]; then
    echo -e "${RED}Error: Invalid spec name: $spec_name${NC}" >&2
    return 1
  fi
}

ensure_local_scratch() {
  local path owner current_uid
  current_uid=$(id -u)
  umask 077
  for path in "$TMP_ROOT" "$TMP_ROOT/rocketclaw" "$TMP_ROOT/rocketclaw/optimize" "$TMP_ROOT/rocketclaw/optimize/workspaces" "$WORKSPACE_DIR"; do
    if [[ -L "$path" ]]; then
      echo -e "${RED}Error: Refusing symlinked local scratch path: $path${NC}" >&2
      return 1
    fi
    if [[ ! -e "$path" ]]; then
      mkdir "$path" || return 1
    fi
    if [[ ! -d "$path" || -L "$path" ]]; then
      echo -e "${RED}Error: Local scratch path is not a real directory: $path${NC}" >&2
      return 1
    fi
    owner=$(stat -f '%u' "$path" 2>/dev/null || stat -c '%u' "$path" 2>/dev/null) || return 1
    if [[ "$owner" != "$current_uid" ]]; then
      echo -e "${RED}Error: Local scratch path is not owned by the current user: $path${NC}" >&2
      return 1
    fi
    chmod 700 "$path"
  done
}

workspace_name() {
  local spec_name="${1:?Error: spec_name required}"
  local padded_index="${2:?Error: padded_index required}"
  printf 'optimize-%s-exp-%s\n' "$spec_name" "$padded_index"
}

registered_workspace_path() {
  local wanted_name="${1:?Error: workspace name required}"
  local name path
  while IFS=$'\t' read -r name path; do
    if [[ "$name" == "$wanted_name" ]]; then
      printf '%s\n' "$path"
      return 0
    fi
  done < <(jj workspace list -T 'name ++ "\t" ++ root ++ "\n"')
  return 1
}

canonical_candidate() {
  local candidate="${1:?Error: path required}"
  local parent
  parent=$(cd "$(dirname "$candidate")" 2>/dev/null && pwd -P) || return 1
  printf '%s/%s\n' "$parent" "$(basename "$candidate")"
}

discard_workspace() {
  local name="${1:?Error: workspace name required}"
  local expected="${2:?Error: workspace path required}"
  local registered expected_path registered_path change_id bookmarks

  registered=$(registered_workspace_path "$name") || {
    echo -e "${RED}Error: Refusing cleanup of unregistered workspace: $name${NC}" >&2
    return 1
  }
  expected_path=$(canonical_candidate "$expected") || return 1
  registered_path=$(canonical_candidate "$registered") || return 1
  if [[ "$registered_path" != "$expected_path" || "$expected_path" != "$WORKSPACE_DIR/"* ]]; then
    echo -e "${RED}Error: Refusing cleanup outside the managed workspace root${NC}" >&2
    return 1
  fi

  change_id=""
  if [[ -d "$expected_path" ]]; then
    jj -R "$expected_path" status >/dev/null 2>&1 || true
    change_id=$(jj -R "$expected_path" log -r @ --no-graph -T 'change_id ++ "\n"' 2>/dev/null || true)
  fi

  jj workspace forget "$name" >/dev/null
  if [[ -d "$expected_path" ]]; then
    rm -rf -- "$expected_path"
  fi

  if [[ -n "$change_id" ]]; then
    bookmarks=$(jj bookmark list -r "$change_id" -T 'name ++ "\n"' 2>/dev/null || true)
    if [[ -z "$bookmarks" ]]; then
      jj abandon "$change_id" >/dev/null 2>&1 || true
    fi
  fi
}

create_workspace() {
  local spec_name="${1:?Error: spec_name required}"
  local exp_index="${2:?Error: exp_index required}"
  local base_revision="${3:?Error: base_revision required}"
  shift 3
  validate_spec_name "$spec_name"
  ensure_local_scratch

  local padded_index name path
  padded_index=$(printf '%03d' "$exp_index")
  name=$(workspace_name "$spec_name" "$padded_index")
  path="$WORKSPACE_DIR/$name"

  if registered_workspace_path "$name" >/dev/null 2>&1; then
    echo -e "${YELLOW}Workspace is already registered; recreating: $path${NC}" >&2
    discard_workspace "$name" "$path"
  elif [[ -e "$path" || -L "$path" ]]; then
    echo -e "${RED}Error: Refusing to replace unregistered path: $path${NC}" >&2
    return 1
  fi

  jj workspace add --name "$name" -r "$base_revision" "$path" >/dev/null

  for file in "$JJ_ROOT"/.env*; do
    if [[ -f "$file" && "$(basename "$file")" != ".env.example" ]]; then
      cp "$file" "$path/$(basename "$file")"
    fi
  done

  for shared_file in "$@"; do
    case "$shared_file" in
      /*|*../*|../*|..)
        echo -e "${RED}Error: Shared path must stay relative to the workspace root: $shared_file${NC}" >&2
        discard_workspace "$name" "$path"
        return 1
        ;;
    esac
    if [[ -f "$JJ_ROOT/$shared_file" ]]; then
      mkdir -p "$(dirname "$path/$shared_file")"
      cp "$JJ_ROOT/$shared_file" "$path/$shared_file"
    elif [[ -d "$JJ_ROOT/$shared_file" ]]; then
      mkdir -p "$(dirname "$path/$shared_file")"
      cp -R "$JJ_ROOT/$shared_file" "$path/$shared_file"
    fi
  done

  printf '%s\n' "$path"
}

cleanup_workspace() {
  local spec_name="${1:?Error: spec_name required}"
  local exp_index="${2:?Error: exp_index required}"
  validate_spec_name "$spec_name"
  ensure_local_scratch

  local padded_index name path
  padded_index=$(printf '%03d' "$exp_index")
  name=$(workspace_name "$spec_name" "$padded_index")
  path="$WORKSPACE_DIR/$name"
  if registered_workspace_path "$name" >/dev/null 2>&1; then
    discard_workspace "$name" "$path"
  elif [[ -e "$path" || -L "$path" ]]; then
    echo -e "${RED}Error: Refusing to remove unregistered path: $path${NC}" >&2
    return 1
  fi
  echo -e "${GREEN}Cleaned up: $name${NC}" >&2
}

cleanup_all() {
  local spec_name="${1:?Error: spec_name required}"
  validate_spec_name "$spec_name"
  ensure_local_scratch
  local prefix="optimize-${spec_name}-exp-" count=0 name path
  while IFS=$'\t' read -r name path; do
    if [[ "$name" == "$prefix"* ]]; then
      discard_workspace "$name" "$WORKSPACE_DIR/$name"
      count=$((count + 1))
    fi
  done < <(jj workspace list -T 'name ++ "\t" ++ root ++ "\n"')
  echo -e "${GREEN}Cleaned up $count experiment workspace(s) for $spec_name${NC}" >&2
}

count_workspaces() {
  jj workspace list -T 'name ++ "\n"' | grep -c '^optimize-.*-exp-[0-9][0-9][0-9]$' || true
}

main() {
  local command="${1:-help}"
  case "$command" in
    create) shift; create_workspace "$@" ;;
    cleanup) shift; cleanup_workspace "$@" ;;
    cleanup-all) shift; cleanup_all "$@" ;;
    count) count_workspaces ;;
    help)
      cat <<'EOF'
Experiment Workspace Manager

Usage:
  experiment-workspace.sh create <spec_name> <exp_index> <base_revision> [shared_file ...]
  experiment-workspace.sh cleanup <spec_name> <exp_index>
  experiment-workspace.sh cleanup-all <spec_name>
  experiment-workspace.sh count

Workspaces: <workspace-root>/.tmp/rocketclaw/optimize/workspaces/<repo-key>/optimize-<spec>-exp-<NNN>/
EOF
      ;;
    *) echo -e "${RED}Unknown command: $command${NC}" >&2; exit 1 ;;
  esac
}

main "$@"
