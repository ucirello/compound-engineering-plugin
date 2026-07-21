#!/bin/bash

# Experiment Workspace Manager
# Creates and removes isolated JJ workspaces for optimization experiments.
#
# Usage:
#   experiment-worktree.sh create <spec_name> <exp_index> <base_revision> [shared_file ...]
#   experiment-worktree.sh cleanup <spec_name> <exp_index>
#   experiment-worktree.sh cleanup-all <spec_name>
#   experiment-worktree.sh count

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

ROOT=$(jj workspace root 2>/dev/null) || {
  echo -e "${RED}Error: Not in a JJ workspace${NC}" >&2
  exit 1
}

WORKSPACE_DIR="$ROOT/.tmp/rocketclaw/optimize-workspaces"

workspace_name() {
  printf 'optimize-%s-exp-%s' "${1:?Error: spec_name required}" "${2:?Error: padded_index required}"
}

validate_spec_name() {
  local spec_name="${1:?Error: spec_name required}"
  if [[ ! "$spec_name" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]]; then
    echo -e "${RED}Error: spec_name must be lowercase kebab-case: $spec_name${NC}" >&2
    return 1
  fi
}

registered_workspace_root() {
  local target="${1:?Error: workspace name required}"
  local candidate candidate_root
  while IFS=$'\t' read -r candidate candidate_root; do
    if [[ "$candidate" == "$target" ]]; then
      printf '%s\n' "$candidate_root"
      return 0
    fi
  done < <(jj workspace list -T 'name ++ "\t" ++ root ++ "\n"')
  return 1
}

create_workspace() {
  local spec_name="${1:?Error: spec_name required}"
  local exp_index="${2:?Error: exp_index required}"
  local base_revision="${3:?Error: base_revision required}"
  shift 3
  validate_spec_name "$spec_name"

  local padded_index
  padded_index=$(printf "%03d" "$exp_index")
  local name
  name=$(workspace_name "$spec_name" "$padded_index")
  local path="$WORKSPACE_DIR/$name"

  local shared_file
  for shared_file in "$@"; do
    if [[ "$shared_file" == /* || "$shared_file" == "." || "$shared_file" == ".." ||
          "$shared_file" == ../* || "$shared_file" == */../* || "$shared_file" == */.. ||
          "$shared_file" == ".jj" || "$shared_file" == .jj/* ]]; then
      echo -e "${RED}Error: Shared resource must be a safe workspace-relative path: $shared_file${NC}" >&2
      return 1
    fi
  done

  local registered_path=""
  registered_path=$(registered_workspace_root "$name" || true)
  if [[ -n "$registered_path" && "$registered_path" != "$path" ]]; then
    echo -e "${RED}Error: JJ workspace $name is registered at unexpected path: $registered_path${NC}" >&2
    return 1
  elif [[ -z "$registered_path" && -e "$path" ]]; then
    echo -e "${RED}Error: Existing path is not a registered JJ workspace: $path${NC}" >&2
    return 1
  fi

  local resolved_base
  resolved_base=$(jj --ignore-working-copy log -r "$base_revision" --no-graph -T 'commit_id ++ "\n"')
  if [[ -z "$resolved_base" || "$resolved_base" == *$'\n'* ]]; then
    echo -e "${RED}Error: Base revision must resolve to exactly one commit: $base_revision${NC}" >&2
    return 1
  fi

  if [[ -n "$registered_path" ]]; then
    jj workspace forget "$name" >/dev/null
    rm -rf -- "$path"
  fi

  mkdir -p "$WORKSPACE_DIR"
  jj workspace add --name "$name" -r "$resolved_base" "$path" >/dev/null

  for f in "$ROOT"/.env*; do
    if [[ -f "$f" ]]; then
      local basename
      basename=$(basename "$f")
      if [[ "$basename" != ".env.example" ]]; then
        cp "$f" "$path/$basename"
      fi
    fi
  done

  for shared_file in "$@"; do
    if [[ -f "$ROOT/$shared_file" ]]; then
      mkdir -p "$(dirname "$path/$shared_file")"
      cp "$ROOT/$shared_file" "$path/$shared_file"
    elif [[ -d "$ROOT/$shared_file" ]]; then
      mkdir -p "$(dirname "$path/$shared_file")"
      rm -rf -- "$path/$shared_file"
      cp -R "$ROOT/$shared_file" "$path/$shared_file"
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
  local path="$WORKSPACE_DIR/$name"

  if registered_workspace_root "$name" >/dev/null; then
    jj workspace forget "$name"
  fi
  rm -rf "$path"
  echo -e "${GREEN}Cleaned up: $name${NC}" >&2
}

cleanup_all() {
  local spec_name="${1:?Error: spec_name required}"
  local prefix="optimize-${spec_name}-exp-"
  local count=0

  while IFS= read -r name; do
    if [[ "$name" == "$prefix"* ]]; then
      local suffix="${name#"$prefix"}"
      [[ "$suffix" =~ ^[0-9]{3}$ ]] || continue
      jj workspace forget "$name"
      rm -rf "$WORKSPACE_DIR/$name"
      count=$((count + 1))
    fi
  done < <(jj workspace list -T 'name ++ "\n"')

  # A crash can leave the directory after its JJ registration is gone. Remove
  # only directories matching this manager's exact padded-index name shape.
  if [[ -d "$WORKSPACE_DIR" ]]; then
    for path in "$WORKSPACE_DIR"/*; do
      [[ -d "$path" ]] || continue
      local name="${path##*/}"
      [[ "$name" == "$prefix"* ]] || continue
      local suffix="${name#"$prefix"}"
      [[ "$suffix" =~ ^[0-9]{3}$ ]] || continue
      rm -rf "$path"
      count=$((count + 1))
    done
  fi

  echo -e "${GREEN}Cleaned up $count experiment workspace(s) for $spec_name${NC}" >&2
}

count_workspaces() {
  local count=0
  local name path
  while IFS=$'\t' read -r name path; do
    [[ "$name" =~ ^optimize-[a-z0-9]+(-[a-z0-9]+)*-exp-[0-9]{3}$ ]] || continue
    [[ "$path" == "$WORKSPACE_DIR/$name" ]] || continue
    count=$((count + 1))
  done < <(jj workspace list -T 'name ++ "\t" ++ root ++ "\n"')
  echo "$count"
}

case "${1:-help}" in
  create) shift; create_workspace "$@" ;;
  cleanup) shift; cleanup_workspace "$@" ;;
  cleanup-all) shift; cleanup_all "$@" ;;
  count) count_workspaces ;;
  help)
    printf '%s\n' \
      'Experiment Workspace Manager' \
      'Usage:' \
      '  experiment-worktree.sh create <spec_name> <exp_index> <base_revision> [shared_file ...]' \
      '  experiment-worktree.sh cleanup <spec_name> <exp_index>' \
      '  experiment-worktree.sh cleanup-all <spec_name>' \
      '  experiment-worktree.sh count'
    ;;
  *) echo -e "${RED}Unknown command: $1${NC}" >&2; exit 1 ;;
esac
