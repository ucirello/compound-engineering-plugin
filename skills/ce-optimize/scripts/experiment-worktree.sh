#!/bin/bash

# Experiment workspace manager. The historical filename/backend token stays
# compatible with optimization specs; isolation is implemented with JJ.
# Usage: create <spec_name> <exp_index> <base_revision> [shared_file ...]
#        cleanup <spec_name> <exp_index> | cleanup-all <spec_name> | count
set -euo pipefail

# Bootstrap from an absolute cwd, then run every JJ operation at this root.
cd "$PWD"
WORKSPACE_ROOT=$(jj workspace root 2>/dev/null) || {
  echo "Error: Not in a JJ workspace" >&2
  exit 1
}
cd "$WORKSPACE_ROOT"
WORKTREE_DIR="$WORKSPACE_ROOT/.tmp/optimize/workspaces"

validate_spec() {
  [[ "$1" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]] || {
    echo "Error: spec_name must be lowercase kebab-case" >&2
    return 1
  }
}

experiment_name() {
  validate_spec "$1" || return 1
  [[ "$2" =~ ^[0-9]+$ ]] || { echo "Error: invalid experiment index" >&2; return 1; }
  printf 'optimize-%s-exp-%03d\n' "$1" "$((10#$2))"
}

workspace_names() {
  jj workspace list --template 'name ++ "\n"'
}

# A name alone is not ownership. Public membership and registered root must
# both match our exact experiment destination before resetting or deleting it.
verify_workspace() {
  local name="$1" expected="$2" actual names
  names=$(workspace_names) || return 1
  grep -Fxq -- "$name" <<< "$names" || return 1
  actual=$(jj workspace root --name "$name") || return 1
  [[ "$actual" == "$expected" && "$actual" != "$WORKSPACE_ROOT" ]] || {
    echo "Error: workspace $name has unexpected root: $actual" >&2
    return 1
  }
}

remove_workspace() {
  local name="$1" destination="$2" names
  names=$(workspace_names) || return 1
  if grep -Fxq -- "$name" <<< "$names"; then
    verify_workspace "$name" "$destination" || return 1
    jj workspace forget "$name"
    rm -rf -- "$destination"
  elif [[ -e "$destination" || -L "$destination" ]]; then
    echo "Error: refusing to remove unregistered path: $destination" >&2
    return 1
  fi
}

create_worktree() {
  local spec_name="${1:?spec_name required}" exp_index="${2:?exp_index required}"
  local base_revision="${3:?base_revision required}"
  shift 3
  local name destination shared_file dir f filename names base_commit
  name=$(experiment_name "$spec_name" "$exp_index")
  destination="$WORKTREE_DIR/$name"

  # Validate the base before resetting an existing experiment.
  base_commit=$(jj log --no-graph -r "$base_revision" --template 'commit_id ++ "\n"')
  [[ "$base_commit" =~ ^[0-9a-f]{40}$ ]] || {
    echo "Error: base_revision must resolve to exactly one commit: $base_revision" >&2
    return 1
  }
  names=$(workspace_names)
  if grep -Fxq -- "$name" <<< "$names"; then
    verify_workspace "$name" "$destination" || return 1
    echo "Resetting existing experiment workspace: $name -> $base_revision" >&2
    remove_workspace "$name" "$destination"
  elif [[ -e "$destination" || -L "$destination" ]]; then
    echo "Error: existing path is not a registered experiment workspace: $destination" >&2
    return 1
  fi

  mkdir -p "$WORKTREE_DIR"
  jj workspace add --name "$name" -r "$base_commit" "$destination" >&2

  # Copy .env files and declared shared resources as before.
  for f in "$WORKSPACE_ROOT"/.env*; do
    if [[ -f "$f" ]]; then
      filename=$(basename "$f")
      [[ "$filename" == .env.example ]] || cp "$f" "$destination/$filename"
    fi
  done
  for shared_file in "$@"; do
    case "$shared_file" in
      ''|.|/*|..|../*|*/../*|*/..|.jj|.jj/*|.git|.git/*)
        echo "Error: shared_file must be a workspace-relative data path: $shared_file" >&2
        return 1 ;;
    esac
    if [[ -f "$WORKSPACE_ROOT/$shared_file" ]]; then
      dir=$(dirname "$destination/$shared_file")
      mkdir -p "$dir"
      cp "$WORKSPACE_ROOT/$shared_file" "$destination/$shared_file"
    elif [[ -d "$WORKSPACE_ROOT/$shared_file" ]]; then
      dir=$(dirname "$destination/$shared_file")
      mkdir -p "$dir"
      rm -rf -- "$destination/$shared_file"
      cp -R "$WORKSPACE_ROOT/$shared_file" "$destination/$shared_file"
    fi
  done
  echo "$destination"
}

cleanup_worktree() {
  local name
  name=$(experiment_name "${1:?spec_name required}" "${2:?exp_index required}")
  remove_workspace "$name" "$WORKTREE_DIR/$name"
  echo "Cleaned up: $name" >&2
}

cleanup_all() {
  local spec_name="${1:?spec_name required}" name names count=0 suffix
  validate_spec "$spec_name"
  names=$(workspace_names)
  while IFS= read -r name; do
    [[ "$name" == "optimize-$spec_name-exp-"* ]] || continue
    suffix="${name#optimize-$spec_name-exp-}"
    [[ "$suffix" =~ ^[0-9]+$ ]] || continue
    remove_workspace "$name" "$WORKTREE_DIR/$name"
    count=$((count + 1))
  done <<< "$names"
  echo "Cleaned up $count experiment workspace(s) for $spec_name" >&2
}

count_worktrees() {
  local names name root count=0
  names=$(workspace_names)
  while IFS= read -r name; do
    [[ -n "$name" ]] || continue
    root=$(jj workspace root --name "$name")
    [[ "$root" == "$WORKSPACE_ROOT" ]] || count=$((count + 1))
  done <<< "$names"
  echo "$count"
}

case "${1:-help}" in
  create) shift; create_worktree "$@" ;;
  cleanup) shift; cleanup_worktree "$@" ;;
  cleanup-all) shift; cleanup_all "$@" ;;
  count) count_worktrees ;;
  help)
    cat <<'EOF'
Experiment Workspace Manager (JJ)
Usage:
  experiment-worktree.sh create <spec_name> <exp_index> <base_revision> [shared_file ...]
  experiment-worktree.sh cleanup <spec_name> <exp_index>
  experiment-worktree.sh cleanup-all <spec_name>
  experiment-worktree.sh count

Workspaces: <workspace-root>/.tmp/optimize/workspaces/optimize-<spec>-exp-<NNN>/
Create resets a registered experiment at its verified root; cleanup forgets
and removes only that workspace. Count includes other registered workspaces.
EOF
    ;;
  *) echo "Unknown command: $1" >&2; exit 1 ;;
esac
