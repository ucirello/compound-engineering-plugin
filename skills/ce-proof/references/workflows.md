# Proof workflows

Required read before running one of these end to end: reviewing a shared doc, creating and sharing a new one, or pulling a doc down to a local file. Endpoint and operation detail lives in `api.md`.

## Workflow: Review a Shared Document

When given a Proof URL like `https://www.proofeditor.ai/d/abc123?token=xxx`:

1. Extract the slug and token
2. Bind presence with the AI Assistant identity defaults
3. Read via `v3/document`
4. Edit with `v3/edit` (narrow content ops; review ops for comments/suggestions)

```bash
TOKEN="xxx"
SLUG="abc123"
AGENT="ai:assistant"

curl -sS -X POST "https://www.proofeditor.ai/api/agent/$SLUG/presence" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Agent-Id: $AGENT" \
  -d '{"name":"AI Assistant","status":"reading","summary":"Reviewing doc"}'

DOC=$(curl -sS "https://www.proofeditor.ai/api/agent/$SLUG/v3/document" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Agent-Id: $AGENT")
REVISION=$(printf '%s' "$DOC" | jq -r '.revision // empty')

# Comment on visible text
curl -sS -X POST "https://www.proofeditor.ai/api/agent/$SLUG/v3/edit" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Agent-Id: $AGENT" \
  -H "Idempotency-Key: $(uuidgen)" \
  -d "$(jq -n --argjson rev "${REVISION:-null}" '{
    by:"ai:assistant",
    baseRevision: (if $rev == null then null else $rev end),
    operations:[{op:"comment",on:"text to comment on",body:"Your comment here"}]
  } | if .baseRevision == null then del(.baseRevision) else . end')"

# Narrow content edit
curl -sS -X POST "https://www.proofeditor.ai/api/agent/$SLUG/v3/edit" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Agent-Id: $AGENT" \
  -H "Idempotency-Key: $(uuidgen)" \
  -d '{"by":"ai:assistant","operations":[{"op":"replace","find":"old","with":"new"}]}'

# Tracked suggestion
curl -sS -X POST "https://www.proofeditor.ai/api/agent/$SLUG/v3/edit" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Agent-Id: $AGENT" \
  -H "Idempotency-Key: $(uuidgen)" \
  -d '{"by":"ai:assistant","operations":[{"op":"suggest","kind":"replace","find":"old","with":"new"}]}'
```

## Workflow: Create and Share a New Document

**Publishing a local file (the primary case):** read the file and JSON-encode its full contents into the `markdown` field with `jq --rawfile` so newlines, quotes, and backticks are escaped correctly. Never hand-write the body or leave an inline placeholder — that publishes a placeholder doc instead of the source artifact.

```bash
SRC="path/to/plan.md"
TITLE="Plan: Foo"

RESPONSE=$(jq -n --arg title "$TITLE" --rawfile md "$SRC" '{title:$title, markdown:$md}' \
  | curl -sS -X POST https://www.proofeditor.ai/share/markdown \
    -H "Content-Type: application/json" -d @-)

URL=$(echo "$RESPONSE" | jq -r '.tokenUrl')
SLUG=$(echo "$RESPONSE" | jq -r '.slug')
TOKEN=$(echo "$RESPONSE" | jq -r '.accessToken')
OWNER_SECRET=$(echo "$RESPONSE" | jq -r '.ownerSecret')   # required for owner delete while unclaimed

# Keep OWNER_SECRET in session memory only — never write it into tracked files or a JJ change.

curl -sS -X POST "https://www.proofeditor.ai/api/agent/$SLUG/presence" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Agent-Id: ai:assistant" \
  -d '{"name":"AI Assistant","status":"reading","summary":"Uploaded doc"}'

echo "$URL"
```

After publish handoffs from planning workflows, surface the URL and return control — do not delete the doc automatically.

When the user later asks to clean up an unclaimed doc you created:

```bash
curl -sS -X DELETE "https://www.proofeditor.ai/api/documents/$SLUG" \
  -H "Authorization: Bearer $OWNER_SECRET"
```

## Workflow: Pull a Proof Doc to Local

Sync the current Proof doc state to a local markdown file. Used for:

- Ad-hoc snapshots of a Proof doc to disk
- Pulling a shared Proof doc that the user (or others) edited back down to a local working copy
- Refreshing a local working copy against the live Proof version

Canonical read for this workflow: `GET /api/agent/$SLUG/v3/document`.

```bash
SLUG=<slug>
TOKEN=<accessToken>
LOCAL=<absolute-path>

WORKSPACE_ROOT="$(jj workspace root 2>/dev/null)" || WORKSPACE_ROOT="$(pwd -P)"
WORKSPACE_ROOT="$(cd "$WORKSPACE_ROOT" && pwd -P)" || exit 1
ensure_private_dir() { dir="$1"; [ ! -L "$dir" ] || { printf '%s\n' "unsafe scratch directory symlink: $dir" >&2; return 1; }; if [ ! -e "$dir" ]; then (umask 077; mkdir "$dir") || return 1; fi; [ -d "$dir" ] && [ -O "$dir" ] || { printf '%s\n' "scratch directory is not owned by the current user: $dir" >&2; return 1; }; chmod 700 "$dir"; }
ensure_private_dir "$WORKSPACE_ROOT/.tmp" || exit 1
TMP_BASE="$WORKSPACE_ROOT/.tmp/rocketclaw"
ensure_private_dir "$TMP_BASE" || exit 1
RUN_DIR=""
for n in 0 1 2 3 4 5 6 7; do
  candidate="$TMP_BASE/ce-proof-$$-$n"
  if (umask 077; mkdir "$candidate") 2>/dev/null; then RUN_DIR="$candidate"; break; fi
done
[ -n "$RUN_DIR" ] || { printf '%s\n' "could not reserve workspace-local scratch" >&2; exit 1; }
STATE_TMP="$RUN_DIR/state.json"
(umask 077; : > "$STATE_TMP") || exit 1
curl -sS "https://www.proofeditor.ai/api/agent/$SLUG/v3/document" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Agent-Id: ai:assistant" > "$STATE_TMP"
REVISION=$(jq -r '.revision // empty' "$STATE_TMP")

SYNC_TMP="$RUN_DIR/sync.md"
(umask 077; : > "$SYNC_TMP") || exit 1
jq -jr '.markdown' "$STATE_TMP" > "$SYNC_TMP" || exit 1
LOCAL_DIR="$(dirname "$LOCAL")"
[ -d "$LOCAL_DIR" ] && [ ! -d "$LOCAL" ] || { printf '%s\n' "destination parent is missing or destination is a directory: $LOCAL" >&2; exit 1; }
device_id() { stat -f '%d' "$1" 2>/dev/null || stat -c '%d' "$1" 2>/dev/null; }
SCRATCH_DEV="$(device_id "$RUN_DIR")" || exit 1
DEST_DEV="$(device_id "$LOCAL_DIR")" || exit 1
[ "$SCRATCH_DEV" = "$DEST_DEV" ] || { printf '%s\n' "workspace scratch and destination must share a filesystem for atomic replacement" >&2; exit 1; }
mv -f "$SYNC_TMP" "$LOCAL" || exit 1
case "$RUN_DIR" in "$TMP_BASE"/ce-proof-*) rm -rf "$RUN_DIR" ;; *) printf '%s\n' "refusing unsafe cleanup path: $RUN_DIR" >&2; exit 1 ;; esac
```

`jq -jr` streams markdown bytes without going through a shell variable, so trailing newlines survive. Scratch stays under the JJ workspace root, or the current local directory outside JJ. The same-filesystem gate keeps the final replacement atomic; a mismatch leaves the destination unchanged instead of using an OS-global or adjacent temporary file.

**Confirm before writing when the pull isn't directly asked for.** If a workflow ends up pulling as a side-effect of a different action, surface the impending write with a short confirm like "Sync Proof doc to `<localPath>`?" A silent overwrite is surprising.
