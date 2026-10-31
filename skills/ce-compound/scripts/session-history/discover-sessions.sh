#!/usr/bin/env bash
# Supported OpenCode export boundary; no internal database/storage discovery.
# Usage: discover-sessions.sh ABSOLUTE_WORKSPACE_ROOT SESSION_ID [SESSION_ID...]
# Obtain candidate IDs from supported OpenCode session listing, never guessed paths.
set -euo pipefail
workspace_root="${1:?absolute workspace root required}"
shift
case "$workspace_root" in /*) ;; *) echo 'workspace root must be absolute' >&2; exit 2 ;; esac
[ -d "$workspace_root/.jj" ] || { echo 'not a JJ workspace root' >&2; exit 2; }
[ "$#" -gt 0 ] || { echo 'explicit source/candidate session IDs required' >&2; exit 2; }
scratch="$workspace_root/.tmp/session-history"
[ ! -L "$workspace_root/.tmp" ] && [ ! -L "$scratch" ] || { echo 'unsafe scratch symlink' >&2; exit 2; }
(umask 077; mkdir -p "$scratch")
for session_id in "$@"; do
  case "$session_id" in ses*[!a-zA-Z0-9_-]*|'') echo 'invalid session ID' >&2; exit 2 ;; ses*) ;; *) echo 'invalid session ID' >&2; exit 2 ;; esac
  # noclobber prevents a planted export symlink or replacing existing evidence.
  output="$scratch/$session_id.export.json"
  (set -o noclobber; umask 077; cd "$workspace_root"; opencode session export "$session_id" > "$output")
  printf '%s\n' "$output"
done
# Reduce exported messages to user/assistant text and tool names/short results
# in per-run scratch BEFORE reading. Exclude reasoning and secrets; the caller
# controls redaction because export shapes may vary. Never read the raw export
# into model context or fall back to an internal database on export failure.
