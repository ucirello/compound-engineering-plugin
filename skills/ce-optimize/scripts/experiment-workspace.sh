#!/bin/bash

# Experiment Workspace Manager
# Creates, cleans up, and counts isolated Jujutsu workspaces for optimization experiments.
# Each experiment gets a new change based on the current optimization bookmark.
#
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

if JJ_ROOT=$(jj workspace root 2>/dev/null); then
  IN_JJ_WORKSPACE=1
else
  JJ_ROOT=$(pwd)
  IN_JJ_WORKSPACE=0
fi

WORKSPACE_DIR="$JJ_ROOT/.tmp/rocketclaw/ce-optimize/workspaces"
VERIFIED_WORKSPACE_REGISTERED=0
VERIFIED_WORKSPACE_TARGET=""

require_jj_workspace() {
  if [[ "$IN_JJ_WORKSPACE" != "1" ]]; then
    echo -e "${RED}Error: This operation requires a Jujutsu workspace${NC}" >&2
    return 1
  fi
}

validate_identity() {
  local spec_name="${1:?Error: spec_name required}"
  local exp_index="${2:?Error: exp_index required}"

  if [[ ! "$spec_name" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]]; then
    echo -e "${RED}Error: spec_name must be lowercase kebab-case${NC}" >&2
    return 1
  fi
  if [[ ! "$exp_index" =~ ^[0-9]+$ ]]; then
    echo -e "${RED}Error: exp_index must be a non-negative integer${NC}" >&2
    return 1
  fi
}

workspace_name() {
  local spec_name="${1:?Error: spec_name required}"
  local padded_index="${2:?Error: padded_index required}"
  echo "optimize-${spec_name}-exp-${padded_index}"
}

experiment_bookmark() {
  local spec_name="${1:?Error: spec_name required}"
  local padded_index="${2:?Error: padded_index required}"
  echo "optimize-exp/${spec_name}/exp-${padded_index}"
}

workspace_registered() {
  local name="${1:?Error: workspace name required}"
  jj workspace list -T 'name ++ "\n"' | grep -Fxq "$name"
}

workspace_absent() {
  local name="${1:?Error: workspace name required}"
  local workspaces

  workspaces=$(jj workspace list -T 'name ++ "\n"') || return 1
  ! grep -Fxq "$name" <<< "$workspaces"
}

workspace_record() {
  local wanted_name="${1:?Error: workspace name required}"
  local name target root

  while IFS=$'\t' read -r name target root; do
    if [[ "$name" == "$wanted_name" ]]; then
      printf '%s\t%s\n' "$target" "$root"
      return 0
    fi
  done < <(jj workspace list -T 'name ++ "\t" ++ target.change_id() ++ "\t" ++ root ++ "\n"')

  return 1
}

directory_empty() {
  local path="${1:?Error: path required}"
  local entries
  shopt -s nullglob dotglob
  entries=("$path"/*)
  shopt -u nullglob dotglob
  [[ ${#entries[@]} -eq 0 ]]
}

verify_disposable_collision() {
  local name="${1:?Error: workspace name required}"
  local bookmark="${2:?Error: bookmark required}"
  local path="${3:?Error: workspace path required}"
  local marker="$path/.tmp/rocketclaw/ce-optimize/result.yaml"
  local record target registered_root metadata actual_target state description
  local bookmark_target local_bookmarks remote_bookmarks

  VERIFIED_WORKSPACE_REGISTERED=0
  VERIFIED_WORKSPACE_TARGET=""

  if ! workspace_registered "$name"; then
    if ! workspace_absent "$name"; then
      echo -e "${RED}Error: refusing to replace workspace $name because its registration state cannot be verified${NC}" >&2
      return 1
    fi
    bookmark_target=$(jj bookmark list "$bookmark" -T 'if(normal_target, normal_target.change_id(), "conflicted") ++ "\n"')
    if [[ -n "$bookmark_target" ]]; then
      echo -e "${RED}Error: refusing to replace unregistered workspace path because $bookmark still targets a change${NC}" >&2
      return 1
    fi
    if [[ -L "$path" || ( -e "$path" && ! -d "$path" ) ]]; then
      echo -e "${RED}Error: refusing to replace unregistered unsafe workspace path: $path${NC}" >&2
      return 1
    fi
    if [[ -d "$path" ]] && ! directory_empty "$path"; then
      echo -e "${RED}Error: refusing to replace unregistered non-empty workspace path: $path${NC}" >&2
      return 1
    fi
    return 0
  fi

  record=$(workspace_record "$name")
  IFS=$'\t' read -r target registered_root <<< "$record"
  if [[ "$registered_root" != "$path" ]]; then
    echo -e "${RED}Error: refusing to replace workspace $name registered at unexpected path: $registered_root${NC}" >&2
    return 1
  fi
  if [[ ! -d "$path" || -L "$path" ]]; then
    echo -e "${RED}Error: refusing to replace workspace $name because its registered path is unavailable or unsafe: $path${NC}" >&2
    return 1
  fi
  if [[ -e "$marker" ]]; then
    echo -e "${RED}Error: refusing to replace workspace $name because it has a recoverable result marker: $marker${NC}" >&2
    return 1
  fi
  if ! jj -R "$path" status >/dev/null; then
    echo -e "${RED}Error: refusing to replace workspace $name because its status cannot be inspected${NC}" >&2
    return 1
  fi

  metadata=$(jj -R "$path" log -r @ --no-graph -T 'change_id ++ "\t" ++ if(empty, "empty", "nonempty") ++ "\t" ++ description.escape_json() ++ "\n"')
  IFS=$'\t' read -r actual_target state description <<< "$metadata"
  if [[ "$actual_target" != "$target" || "$state" != "empty" || "$description" != '""' ]]; then
    echo -e "${RED}Error: refusing to replace workspace $name because its target has unique or unpublished work${NC}" >&2
    return 1
  fi

  bookmark_target=$(jj bookmark list "$bookmark" -T 'if(normal_target, normal_target.change_id(), "conflicted") ++ "\n"')
  if [[ -n "$bookmark_target" && "$bookmark_target" != "$target" ]]; then
    echo -e "${RED}Error: refusing to replace workspace $name because $bookmark targets another change${NC}" >&2
    return 1
  fi
  local_bookmarks=$(jj bookmark list -r "$target" -T 'if(remote, "", name ++ "\n")')
  if [[ -n "$local_bookmarks" && "$local_bookmarks" != "$bookmark" ]]; then
    echo -e "${RED}Error: refusing to replace workspace $name because its target has other local bookmarks${NC}" >&2
    return 1
  fi
  remote_bookmarks=$(jj bookmark list --all-remotes -r "$target" -T 'if(remote, name ++ "@" ++ remote ++ "\n", "")')
  if [[ -n "$remote_bookmarks" ]]; then
    echo -e "${RED}Error: refusing to replace workspace $name because its target is published remotely${NC}" >&2
    return 1
  fi

  VERIFIED_WORKSPACE_REGISTERED=1
  VERIFIED_WORKSPACE_TARGET="$target"
}

cleanup_workspace() {
  local spec_name="${1:?Error: spec_name required}"
  local exp_index="${2:?Error: exp_index required}"
  require_jj_workspace
  validate_identity "$spec_name" "$exp_index"
  local padded_index
  padded_index=$(printf "%03d" "$exp_index")
  local name
  name=$(workspace_name "$spec_name" "$padded_index")
  local bookmark
  bookmark=$(experiment_bookmark "$spec_name" "$padded_index")
  local path="$WORKSPACE_DIR/$name"
  local bookmark_target

  verify_disposable_collision "$name" "$bookmark" "$path"
  if [[ "$VERIFIED_WORKSPACE_REGISTERED" == "1" ]]; then
    jj workspace forget "$name" >/dev/null
    if ! workspace_absent "$name"; then
      echo -e "${RED}Error: refusing to delete workspace $name because its absence could not be verified${NC}" >&2
      return 1
    fi
  elif ! workspace_absent "$name"; then
    echo -e "${RED}Error: refusing to delete workspace $name because its absence could not be verified${NC}" >&2
    return 1
  fi
  bookmark_target=$(jj bookmark list "$bookmark" -T 'if(normal_target, normal_target.change_id(), "conflicted") ++ "\n"')
  if [[ -n "$bookmark_target" && "$bookmark_target" != "$VERIFIED_WORKSPACE_TARGET" ]]; then
    echo -e "${RED}Error: refusing to delete workspace $name because $bookmark no longer matches the verified target${NC}" >&2
    return 1
  fi

  rm -rf "$path"
  if [[ -n "$bookmark_target" ]]; then
    jj bookmark delete "$bookmark" >/dev/null
  fi

  echo -e "${GREEN}Cleaned up: $name${NC}" >&2
}

create_workspace() {
  local spec_name="${1:?Error: spec_name required}"
  local exp_index="${2:?Error: exp_index required}"
  local base_revision="${3:?Error: base_revision required}"
  shift 3
  require_jj_workspace
  validate_identity "$spec_name" "$exp_index"

  local padded_index
  padded_index=$(printf "%03d" "$exp_index")
  local name
  name=$(workspace_name "$spec_name" "$padded_index")
  local bookmark
  bookmark=$(experiment_bookmark "$spec_name" "$padded_index")
  local path="$WORKSPACE_DIR/$name"

  if [[ -e "$path" || -L "$path" ]] || workspace_registered "$name"; then
    verify_disposable_collision "$name" "$bookmark" "$path"
    echo -e "${YELLOW}Replacing verified disposable experiment workspace: $name${NC}" >&2
    cleanup_workspace "$spec_name" "$exp_index"
  fi

  mkdir -p "$WORKSPACE_DIR"
  jj workspace add --name "$name" -r "$base_revision" "$path" >/dev/null
  jj -R "$path" bookmark create "$bookmark" -r @ >/dev/null

  for f in "$JJ_ROOT"/.env*; do
    if [[ -f "$f" ]]; then
      local basename
      basename=$(basename "$f")
      if [[ "$basename" != ".env.example" ]]; then
        cp "$f" "$path/$basename"
      fi
    fi
  done

  for shared_file in "$@"; do
    if [[ "$shared_file" == /* || "$shared_file" == ".." || "$shared_file" == ../* || "$shared_file" == */../* || "$shared_file" == */.. ]]; then
      echo -e "${RED}Error: shared_file must stay within the workspace: $shared_file${NC}" >&2
      return 1
    fi
    if [[ -f "$JJ_ROOT/$shared_file" ]]; then
      local dir
      dir=$(dirname "$path/$shared_file")
      mkdir -p "$dir"
      cp "$JJ_ROOT/$shared_file" "$path/$shared_file"
    elif [[ -d "$JJ_ROOT/$shared_file" ]]; then
      local dir
      dir=$(dirname "$path/$shared_file")
      mkdir -p "$dir"
      rm -rf "$path/$shared_file"
      cp -R "$JJ_ROOT/$shared_file" "$path/$shared_file"
    fi
  done

  echo "$path"
}

cleanup_all() {
  local spec_name="${1:?Error: spec_name required}"
  require_jj_workspace
  validate_identity "$spec_name" 0
  local prefix="optimize-${spec_name}-exp-"
  local count=0

  mkdir -p "$WORKSPACE_DIR"
  while IFS= read -r name; do
    if [[ "$name" == "$prefix"* ]]; then
      local index_str="${name#$prefix}"
      cleanup_workspace "$spec_name" "$((10#$index_str))"
      count=$((count + 1))
    fi
  done < <(jj workspace list -T 'name ++ "\n"')

  echo -e "${GREEN}Cleaned up $count experiment workspace(s) for $spec_name${NC}" >&2
}

count_workspaces() {
  require_jj_workspace
  local count=0
  local name
  while IFS= read -r name; do
    if [[ "$name" == optimize-*-exp-* ]]; then
      count=$((count + 1))
    fi
  done < <(jj workspace list -T 'name ++ "\n"')
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
  experiment-workspace.sh create <spec_name> <exp_index> <base_revision> [shared_file ...]
  experiment-workspace.sh cleanup <spec_name> <exp_index>
  experiment-workspace.sh cleanup-all <spec_name>
  experiment-workspace.sh count

Commands:
  create       Create an isolated experiment workspace and bookmark
  cleanup      Forget one experiment workspace and delete its bookmark
  cleanup-all  Forget all experiment workspaces for a spec
  count        Count active experiment workspaces

Workspaces: .tmp/rocketclaw/ce-optimize/workspaces/optimize-<spec>-exp-<NNN>/
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
