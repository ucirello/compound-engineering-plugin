#!/usr/bin/env bash
# Discover session files across Claude Code, Codex, Cursor, Pi, and oh-my-pi (omp).
#
# Usage: discover-sessions.sh <workspace-name> <days> [--cwd /abs/workspace/root] [--platform claude|codex|cursor|pi|omp]
#
# Outputs one file path per line. Safe in both bash and zsh (all globs guarded).
# Pass output to extract-metadata.py:
#   python3 extract-metadata.py --cwd-filter <workspace-root> $(bash discover-sessions.sh <workspace-name> 7)
#
# Arguments:
#   workspace-name  Folder name of the workspace (e.g., "my-project"). Used for directory matching.
#   days       Scan window in days (e.g., 7). Files older than this are skipped.
#   --cwd      Absolute workspace root. Used for exact Pi encoded-CWD discovery
#              and the omp raw-bucket probe. Claude listing is unfiltered;
#              extract-metadata.py --cwd-filter matches recorded cwd.
#   --platform Restrict to a single platform. Omit to search all.

set -euo pipefail

REPO_NAME="${1:?Usage: discover-sessions.sh <workspace-name> <days> [--cwd /abs/workspace/root] [--platform claude|codex|cursor|pi|omp]}"
DAYS="${2:?Usage: discover-sessions.sh <workspace-name> <days> [--cwd /abs/workspace/root] [--platform claude|codex|cursor|pi|omp]}"
PLATFORM="all"
REPO_CWD=""

shift 2
while [ $# -gt 0 ]; do
    case "$1" in
        --cwd) REPO_CWD="$2"; shift 2 ;;
        --platform) PLATFORM="$2"; shift 2 ;;
        *) shift ;;
    esac
done

encode_pi_cwd() {
    local cwd="${1%/}"
    local encoded="${cwd//\//-}"
    encoded="${encoded#-}"
    printf -- "--%s--" "$encoded"
}

discover_claude() {
    local base="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/projects"
    [ -d "$base" ] || return 0
    find "$base" -mindepth 2 -maxdepth 2 -type f -name "*.jsonl" -mtime "-${DAYS}" 2>/dev/null
}

discover_codex() {
    local codex_home="${CODEX_HOME:-$HOME/.codex}"
    for base in "$codex_home/sessions" "$HOME/.agents/sessions"; do
        [ -d "$base" ] || continue
        find "$base" -name "*.jsonl" -mtime "-${DAYS}" 2>/dev/null
    done
}

discover_cursor() {
    local base="$HOME/.cursor/projects"
    [ -d "$base" ] || return 0
    for dir in "$base"/*"$REPO_NAME"*/; do
        [ -d "$dir" ] || continue
        local transcripts="$dir/agent-transcripts"
        [ -d "$transcripts" ] || continue
        find "$transcripts" -name "*.jsonl" -mtime "-${DAYS}" 2>/dev/null
    done
}

discover_pi() {
    local agent_dir="${PI_CODING_AGENT_DIR:-$HOME/.pi/agent}"
    local base="${PI_CODING_AGENT_SESSION_DIR:-$agent_dir/sessions}"
    [ -d "$base" ] || return 0

    if [ -n "${PI_CODING_AGENT_SESSION_DIR:-}" ]; then
        find "$base" -maxdepth 1 -name "*.jsonl" -mtime "-${DAYS}" 2>/dev/null
        if [ -z "$REPO_CWD" ]; then
            for dir in "$base"/*"$REPO_NAME"*/; do
                [ -d "$dir" ] || continue
                find "$dir" -maxdepth 1 -name "*.jsonl" -mtime "-${DAYS}" 2>/dev/null
            done
        fi
        return 0
    fi

    if [ -n "$REPO_CWD" ]; then
        local dir="$base/$(encode_pi_cwd "$REPO_CWD")"
        [ -d "$dir" ] || return 0
        find "$dir" -maxdepth 1 -name "*.jsonl" -mtime "-${DAYS}" 2>/dev/null
        return 0
    fi

    for dir in "$base"/*"$REPO_NAME"*/; do
        [ -d "$dir" ] || continue
        find "$dir" -maxdepth 1 -name "*.jsonl" -mtime "-${DAYS}" 2>/dev/null
    done
}

encode_omp_raw_cwd() {
    local cwd canon_home canon_tmp rel
    cwd="$(cd "$1" 2>/dev/null && pwd -P)" || return 0
    canon_home="$(cd "$HOME" 2>/dev/null && pwd -P)" || canon_home="$HOME"
    case "$cwd" in
        "$canon_home") printf -- '-' ;;
        "$canon_home"/*)
            rel="$(printf '%s' "${cwd#"$canon_home"/}" | sed 's/[/\\:]/-/g')"
            printf -- '-%s' "$rel"
            ;;
        *)
            workspace_root="$(jj workspace root 2>/dev/null)" || workspace_root="$PWD"
            canon_tmp="$(cd "$workspace_root/.tmp" 2>/dev/null && pwd -P)" || canon_tmp=""
            case "$cwd" in
                "$canon_tmp") printf -- '-tmp' ;;
                "$canon_tmp"/*)
                    rel="$(printf '%s' "${cwd#"$canon_tmp"/}" | sed 's/[/\\:]/-/g')"
                    printf -- '-tmp-%s' "$rel"
                    ;;
                *)
                    rel="$(printf '%s' "${cwd#/}" | sed 's/[/\\:]/-/g')"
                    printf -- '--%s--' "$rel"
                    ;;
            esac
            ;;
    esac
}

discover_omp() {
    local config_dir="${PI_CONFIG_DIR:-.omp}"

    if [ -n "${PI_CODING_AGENT_SESSION_DIR:-}" ]; then
        local base="$PI_CODING_AGENT_SESSION_DIR"
        [ -d "$base" ] || return 0
        find "$base" -maxdepth 1 -name "*.jsonl" -mtime "-${DAYS}" 2>/dev/null
        if [ -z "$REPO_CWD" ]; then
            for dir in "$base"/*"$REPO_NAME"*/; do
                [ -d "$dir" ] || continue
                find "$dir" -maxdepth 1 -name "*.jsonl" -mtime "-${DAYS}" 2>/dev/null
            done
        fi
        return 0
    fi

    local sanitized
    sanitized="$(printf '%s' "$REPO_NAME" | sed -E 's/[^a-zA-Z0-9._-]+/-/g; s/^-+//; s/-+$//' | tail -c 80)"
    [ -n "$sanitized" ] || sanitized="project"
    local agent_dir="${PI_CODING_AGENT_DIR:-$HOME/$config_dir/agent}"
    local xdg_omp=""
    if [ -z "${PI_CODING_AGENT_DIR:-}" ] && [ -n "${XDG_DATA_HOME:-}" ]; then
        case "$(uname -s)" in
            Linux|Darwin)
                if [ -d "${XDG_DATA_HOME%/}/omp" ]; then
                    xdg_omp="${XDG_DATA_HOME%/}/omp"
                fi
                ;;
        esac
    fi
    {
        local root dir encoded
        if [ -n "$REPO_CWD" ]; then
            encoded="$(encode_omp_raw_cwd "$REPO_CWD")"
            if [ -n "$encoded" ]; then
                for root in "$agent_dir/sessions" \
                            "$HOME/$config_dir"/profiles/*/agent/sessions \
                            ${xdg_omp:+"$xdg_omp/sessions"} \
                            ${xdg_omp:+"$xdg_omp"/profiles/*/sessions}; do
                    [ -d "$root/$encoded" ] || continue
                    find "$root/$encoded" -maxdepth 1 -name "*.jsonl" -mtime "-${DAYS}" 2>/dev/null
                done
            fi
        fi
        for root in "$agent_dir/sessions" \
                    "$HOME/$config_dir"/profiles/*/agent/sessions \
                    ${xdg_omp:+"$xdg_omp/sessions"} \
                    ${xdg_omp:+"$xdg_omp"/profiles/*/sessions}; do
            [ -d "$root" ] || continue
            for dir in "$root"/*"$sanitized"*/; do
                [ -d "$dir" ] || continue
                find "$dir" -maxdepth 1 -name "*.jsonl" -mtime "-${DAYS}" 2>/dev/null
            done
            if [ "$REPO_NAME" != "$sanitized" ]; then
                for dir in "$root"/*"$REPO_NAME"*/; do
                    [ -d "$dir" ] || continue
                    find "$dir" -maxdepth 1 -name "*.jsonl" -mtime "-${DAYS}" 2>/dev/null
                done
            fi
        done
    } | awk '!seen[$0]++'
}

case "$PLATFORM" in
    claude) discover_claude ;;
    codex) discover_codex ;;
    cursor) discover_cursor ;;
    pi) discover_pi ;;
    omp) discover_omp ;;
    all) { discover_claude; discover_codex; discover_cursor; discover_pi; discover_omp; } | awk '!seen[$0]++' ;;
    *) echo "Unknown platform: $PLATFORM" >&2; exit 1 ;;
esac
