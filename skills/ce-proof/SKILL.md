---
name: ce-proof
description: Publish, read, comment on, or edit markdown in Proof. Use for Proof links, sharing specs/plans/drafts, or publish handoffs from planning workflows; avoid proofread, math, evidence, or proof-of-concept meanings.
allowed-tools:
  - Bash
  - Read
  - Write
  - WebFetch
---

# Proof - Collaborative Markdown Editor

Proof is a collaborative document editor for humans and agents. It supports two modes:

1. **Web API** - Create and edit shared documents via HTTP (no install needed)
2. **Local Bridge** - Drive the macOS Proof app via localhost:9847

## Operation Identity

Every write to a Proof doc must carry a stable operation identity:

- **Machine ID (`by` on every op, `X-Agent-Id` header):** `editor:automation` — stable, lowercase, neutral, and machine-parseable. Appears in marks, events, and the API response.
- **Display name (`name` on `POST /presence`):** `Document Editor` — neutral, human-readable, and shown in Proof's presence UI.

Set the display name once per doc session by posting to presence with the `X-Agent-Id` header; Proof binds the name to that agent ID for the session. Use these neutral values for every caller of this skill; do not substitute a caller-specific identity.

## Publish Mode

The primary use is one-way publishing: take an existing local markdown file (a brainstorm, a unified plan, a learning, a draft), read its full contents and post them as the new doc's body (see "Workflow: Create and Share a New Document" for the source-file recipe — never publish placeholder content), and hand the user a shareable URL. The local file stays canonical — publishing does not sync anything back to disk. The user can open the link to read, comment, and share with others; the agent can also participate via the edit APIs below when given the URL. Two entry points, identical mechanics (see "Workflow: Create and Share a New Document"):

- **Direct user request** — a bare user phrase naming a local markdown file and asking to share it via Proof: "share this to proof", "publish this to proof", "open this in proof editor so I can review", "get me a proof link for this doc". The file is whichever markdown the user just created, edited, or referenced; if ambiguous, ask which file. This is a first-class entry point — do not require an upstream caller.
- **Upstream skill handoff** — `ce-brainstorm`, `ce-ideate`, or `ce-plan` finishes a draft and hands it off to publish for human review, passing the file path and title explicitly.

Only publish markdown. If the source is an HTML unified plan, do not upload it
to Proof; return the local browser/open path instead. When publishing a unified
plan, label the title by readiness when available, e.g. `Plan: <title>
(requirements-only)` or `Plan: <title> (implementation-ready)`.

## Web API (Primary for Sharing)

### Create a Shared Document

No authentication required. Returns a shareable URL with access token.

```bash
curl -X POST https://www.proofeditor.ai/share/markdown \
  -H "Content-Type: application/json" \
  -d '{"title":"My Doc","markdown":"# Hello\n\nContent here."}'
```

**Response format:**
```json
{
  "slug": "abc123",
  "tokenUrl": "https://www.proofeditor.ai/d/abc123?token=xxx",
  "accessToken": "xxx",
  "ownerSecret": "yyy",
  "_links": {
    "state": "https://www.proofeditor.ai/api/agent/abc123/state",
    "ops": "https://www.proofeditor.ai/api/agent/abc123/ops"
  }
}
```

Use the `tokenUrl` as the shareable link. The `_links` give you the exact API paths.

### Read a Shared Document

If you already have a shared Proof URL, no browser automation is needed. Fetch the URL directly with content negotiation:

```bash
curl -s -H "Accept: application/json" "https://www.proofeditor.ai/d/{slug}?token=<token>"
curl -s -H "Accept: text/markdown" "https://www.proofeditor.ai/d/{slug}?token=<token>"
```

The JSON response includes the markdown, API links, and agent auth hints. Use `/state` when you need mutation metadata, marks, or presence:

```bash
curl -s "https://www.proofeditor.ai/api/agent/{slug}/state" \
  -H "x-share-token: <token>"
```

For comment-ingest workflows, prefer the server-side filter:

```bash
curl -s "https://www.proofeditor.ai/api/agent/{slug}/state?kinds=comment" \
  -H "x-share-token: <token>"
```

`state.marks` is a union of comments, suggestions, and provenance/authorship marks. The `?kinds=comment` filter avoids treating human-authored provenance marks as review comments.

### Edit a Shared Document

Comment, suggestion, and rewrite operations go to `POST https://www.proofeditor.ai/api/agent/{slug}/ops`. Block edits use `/api/agent/{slug}/edit/v2`.

**Note:** Use the `/api/agent/{slug}/ops` path (from `_links` in create response), NOT `/api/documents/{slug}/ops`.

**Authentication for protected docs:**
- Header: `x-share-token: <token>` or `Authorization: Bearer <token>`
- Token comes from the URL parameter: `?token=xxx` or the `accessToken` from create response
- Header: `X-Agent-Id: editor:automation` (required for presence; include on ops for consistent operation identity)

**Wire-format reminder.** `/api/agent/{slug}/ops` uses a top-level `type` field; `/api/agent/{slug}/edit/v2` uses an `operations` array where each entry has `op`. Do not mix — sending `op` to `/ops` returns 422.

**Every mutation requires a `baseToken`.** Reuse the `mutationBase.token` from the most recent `/state` or `/snapshot` read, then update it from successful mutation responses (`.mutationBase.token`). On `BASE_TOKEN_REQUIRED` or `STALE_BASE`, re-read and retry once. Only do a pre-mutation read if no prior read has happened in this session or you need fresh document/comment/snapshot content.

`/edit/v2` block refs are a separate concern: they can drift across revisions, so re-fetch `/snapshot` for fresh refs before a block edit if any writes have landed since your last snapshot.

### Edit Strategy: Avoid Whole-Doc Rewrite

Do not default to full-document replacement. Pick the narrowest edit primitive that matches the requested change:

1. **Literal repeated change:** use `/edit/v2` with `find_replace_in_doc` (optionally constrained by `fromRef`, `toRef`, or `block_filter`). This is the fastest and least error-prone path for terminology renames, punctuation/style sweeps, and other exact text substitutions.
2. **Known block or section change:** use `/edit/v2` block operations from a fresh `/snapshot`: `replace_block`, `insert_before`, `insert_after`, `delete_block`, `replace_range`, or `find_replace_in_block`.
3. **Visible track-changes desired:** use `/ops` `suggestion.add` (pending or `status: "accepted"`) when the user should see a suggestion mark and reject/revert affordance for that specific edit.
4. **Whole-doc replacement:** use `rewrite.apply` only as a last resort when the user explicitly asks to replace the entire document, when the intended change is genuinely global and cannot be expressed as block/range/find-replace operations, and when no live clients are present. Before rewriting, read current state, preserve comments/marks expectations, and mention that the rewrite is broad.

When in doubt, start with `/snapshot` and build a small `/edit/v2` batch. A narrow failed edit is easier to inspect and retry than a broad rewrite, and it avoids clobbering concurrent human work.

**Retry discipline after mutation errors — verify before retrying.** An error response is not proof that nothing was written.

- `STALE_BASE`, `BASE_TOKEN_REQUIRED`, `MISSING_BASE`, `INVALID_BASE_TOKEN` — pre-commit, token-related. Re-read `/state`, rebuild the request body with a fresh `baseToken`, and retry once with a new `Idempotency-Key`.
- `ANCHOR_NOT_FOUND`, `ANCHOR_AMBIGUOUS` — pre-commit, but the `quote` no longer uniquely matches content. Re-reading does not help by itself; the caller must tighten or regenerate the anchor before retrying. Do not auto-retry blindly.
- `INVALID_OPERATIONS`, `INVALID_REQUEST`, `INVALID_REF`, `INVALID_BLOCK_MARKDOWN`, `INVALID_RANGE`, `INVALID_MARKDOWN`, 422 — pre-commit, but the payload is wrong. Do not retry blindly; fix the payload first.
- `COLLAB_SYNC_FAILED`, `REWRITE_BARRIER_FAILED`, `PROJECTION_STALE`, `INTERNAL_ERROR`, 5xx, network timeout, and any **202 with `collab.status: "pending"`** — the canonical doc may have been written even though the call looks like a failure. Before any retry, re-read `/state` and check whether the intended mark/edit is already present; only retry if it isn't.
- `Idempotency-Key` (see below) protects against double-apply *on the same request* (e.g., TCP-level retry). It does not help if you build a new request body and send a second call — that is a new logical write with a new key.

Duplicate-mark incidents usually come from retrying a `comment.add` or `suggestion.add` after a timeout without verifying. When in doubt: re-read, diff, then decide.

**`Idempotency-Key` header** is recommended on every mutation for safe automation retries; required when `/state.contract.idempotencyRequired` is true. Use the same key only when resending the exact same serialized request body. If the body changes — including because you replaced `baseToken` after `STALE_BASE` — mint a new key or Proof will reject it as key reuse with a different payload.

**Comment on text:**
```json
{"type": "comment.add", "quote": "text to comment on", "by": "editor:automation", "text": "Your comment here", "baseToken": "<token>"}
```

**Reply to a comment:**
```json
{"type": "comment.reply", "markId": "<id>", "by": "editor:automation", "text": "Reply text", "baseToken": "<token>"}
```

**Reply and resolve in one mutation:**
```json
{"type": "comment.reply", "markId": "<id>", "by": "editor:automation", "text": "Fixed.", "resolve": true, "baseToken": "<token>"}
```

**Batch existing-thread comment mutations:**
```json
{"by": "editor:automation", "baseToken": "<token>", "operations": [
  {"type": "comment.reply", "markId": "<id-1>", "text": "Fixed.", "resolve": true},
  {"type": "comment.reply", "markId": "<id-2>", "text": "Leaving this open because X."}
]}
```

Batch `/ops` supports `comment.reply`, `comment.resolve`, and `comment.unresolve` for existing threads. Use it to reply to and resolve multiple threads in one call instead of issuing separate reply and resolve requests per thread.

**Resolve / unresolve a comment:**
```json
{"type": "comment.resolve", "markId": "<id>", "by": "editor:automation", "baseToken": "<token>"}
{"type": "comment.unresolve", "markId": "<id>", "by": "editor:automation", "baseToken": "<token>"}
```

**Suggest a replacement (pending — user must accept/reject):**
```json
{"type": "suggestion.add", "kind": "replace", "quote": "original text", "by": "editor:automation", "content": "replacement text", "baseToken": "<token>"}
```

**Suggest and immediately apply (tracked but committed — user can reject to revert):**
```json
{"type": "suggestion.add", "kind": "replace", "quote": "original text", "by": "editor:automation", "content": "replacement text", "status": "accepted", "baseToken": "<token>"}
```

`status: "accepted"` creates the suggestion mark and commits the change in one call. The mark persists as an audit trail with per-edit attribution and a reject-to-revert affordance. Works with `kind: "insert" | "delete" | "replace"`.

**Accept or reject an existing suggestion:**
```json
{"type": "suggestion.accept", "markId": "<id>", "by": "editor:automation", "baseToken": "<token>"}
{"type": "suggestion.reject", "markId": "<id>", "by": "editor:automation", "baseToken": "<token>"}
```

`suggestion.resolve` is not supported — use accept or reject instead.

**Whole-doc rewrite (last resort):**
```json
{"type": "rewrite.apply", "content": "full new markdown", "by": "editor:automation", "baseToken": "<token>"}
```

Prefer `find_replace_in_doc` or block-level `/edit/v2` operations first. `rewrite.apply` is broad, disruptive, and blocked while live clients are connected.

**Block-level edits via `/edit/v2`** (separate endpoint, separate shape):
```bash
curl -X POST "https://www.proofeditor.ai/api/agent/{slug}/edit/v2" \
  -H "Content-Type: application/json" \
  -H "x-share-token: <token>" \
  -H "X-Agent-Id: editor:automation" \
  -H "Idempotency-Key: <uuid>" \
  -d '{
    "by": "editor:automation",
    "baseToken": "mt1:<token>",
    "operations": [
      {"op": "replace_block", "ref": "b3", "block": {"markdown": "Updated paragraph."}},
      {"op": "insert_after", "ref": "b3", "blocks": [{"markdown": "## New section"}]}
    ]
  }'
```

Per-op body shape (singular `block` vs plural `blocks` is load-bearing — sending the wrong one returns 422):

| op | body fields |
|---|---|
| `replace_block` | `ref`, `block: {markdown}` |
| `insert_after` | `ref`, `blocks: [{markdown}, ...]` |
| `insert_before` | `ref`, `blocks: [{markdown}, ...]` |
| `delete_block` | `ref` |
| `replace_range` | `fromRef`, `toRef`, `blocks: [{markdown}, ...]` |
| `find_replace_in_block` | `ref`, `find`, `replace`, `occurrence: "first" \| "all"` |
| `find_replace_in_doc` | `find`, `replace`, `occurrence: "first" \| "all"`, optional `fromRef`, `toRef`, `block_filter` |

Read `/snapshot` to get block `ref` IDs and `mutationBase.token`. `ref` values are opaque request tokens tied to the snapshot/baseToken; re-read `/snapshot` before follow-up block edits if writes have landed. `operations` commits atomically — either every op lands or none do — so one `/edit/v2` call can batch dozens of block edits safely and efficiently. Successful full responses include the next `mutationBase.token` and fresh `snapshot.blocks[].ref` values for chaining.

For literal doc-wide sweeps, prefer `find_replace_in_doc` over many block replacements or a whole-doc rewrite. Validate large batches with `?dryRun=1` or `?validate=1`; use `?return=minimal` when you only need `ok`, `revision`, `appliedCount`, and the next `mutationBase`.

**Editing while a client is connected is fine.** `/edit/v2`, `suggestion.add` (including `status: "accepted"`), and all comment ops work during active collab. Only `rewrite.apply` is blocked by `LIVE_CLIENTS_PRESENT` — it would clobber in-flight Yjs edits.

**When the loop breaks.** If a mutation keeps failing after a fresh read and one retry, or state across reads looks inconsistent, call `POST https://www.proofeditor.ai/api/bridge/report_bug` with the failing request ID, slug, and raw response. The server enriches and files an issue.

### Known Limitations (Web API)

- Bridge-style endpoints (`/d/{slug}/bridge/*`) require client version headers (`x-proof-client-version`, `x-proof-client-build`, `x-proof-client-protocol`) and return 426 CLIENT_UPGRADE_REQUIRED without them. Use `/api/agent/{slug}/ops` instead.

## Local Bridge (macOS App)

Requires Proof.app running. Bridge at `http://localhost:9847`.

**Required headers:**
- `X-Agent-Id: editor:automation` (operation identity for presence; keep aligned with `by`)
- `Content-Type: application/json`
- `X-Window-Id: <uuid>` (when multiple docs open)

### Key Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/windows` | List open documents |
| GET | `/state` | Read markdown, cursor, word count |
| GET | `/marks` | List all suggestions and comments |
| POST | `/marks/suggest-replace` | `{"quote":"old","by":"editor:automation","content":"new"}` |
| POST | `/marks/suggest-insert` | `{"quote":"after this","by":"editor:automation","content":"insert"}` |
| POST | `/marks/suggest-delete` | `{"quote":"delete this","by":"editor:automation"}` |
| POST | `/marks/comment` | `{"quote":"text","by":"editor:automation","text":"comment"}` |
| POST | `/marks/reply` | `{"markId":"<id>","by":"editor:automation","text":"reply"}` |
| POST | `/marks/resolve` | `{"markId":"<id>","by":"editor:automation"}` |
| POST | `/marks/accept` | `{"markId":"<id>"}` |
| POST | `/marks/reject` | `{"markId":"<id>"}` |
| POST | `/rewrite` | Last-resort whole-doc replacement: `{"content":"full markdown","by":"editor:automation"}` |
| POST | `/presence` | `{"status":"reading","summary":"..."}` |
| GET | `/events/pending` | Poll for user actions |

### Presence Statuses

`thinking`, `reading`, `idle`, `acting`, `waiting`, `completed`

## Workflow: Review a Shared Document

When given a Proof URL like `https://www.proofeditor.ai/d/abc123?token=xxx`:

1. Extract the slug (`abc123`) and token from the URL
2. Read the document via content negotiation on the shared URL or via `/api/agent/{slug}/state` when you need marks/mutation metadata
3. For content edits, prefer `/edit/v2` `find_replace_in_doc` or block operations; use `/ops` for comments, suggestions, and comment replies/resolution
4. The author sees changes in real-time

```bash
SHARE_URL="https://www.proofeditor.ai/d/abc123?token=xxx"
curl -s -H "Accept: application/json" "$SHARE_URL"
curl -s -H "Accept: text/markdown" "$SHARE_URL"

# Read once for content + the initial baseToken.
# After each successful mutation, update BASE from the response's mutationBase.token.
STATE=$(curl -s "https://www.proofeditor.ai/api/agent/abc123/state" \
  -H "x-share-token: xxx")
BASE=$(printf '%s' "$STATE" | jq -r '.mutationBase.token')
# Inspect doc fields as needed: printf '%s' "$STATE" | jq '.markdown, .revision'

# Comment
OP_RESP=$(curl -s -X POST "https://www.proofeditor.ai/api/agent/abc123/ops" \
  -H "Content-Type: application/json" \
  -H "x-share-token: xxx" \
  -H "X-Agent-Id: editor:automation" \
  -H "Idempotency-Key: $(uuidgen)" \
  -d "$(jq -n --arg base "$BASE" '{type:"comment.add",quote:"text",by:"editor:automation",text:"comment",baseToken:$base}')")
NEXT_BASE=$(printf '%s' "$OP_RESP" | jq -r '.mutationBase.token // empty')
[ -n "$NEXT_BASE" ] && BASE="$NEXT_BASE"

# Suggest edit (tracked, pending)
OP_RESP=$(curl -s -X POST "https://www.proofeditor.ai/api/agent/abc123/ops" \
  -H "Content-Type: application/json" \
  -H "x-share-token: xxx" \
  -H "X-Agent-Id: editor:automation" \
  -H "Idempotency-Key: $(uuidgen)" \
  -d "$(jq -n --arg base "$BASE" '{type:"suggestion.add",kind:"replace",quote:"old",by:"editor:automation",content:"new",baseToken:$base}')")
NEXT_BASE=$(printf '%s' "$OP_RESP" | jq -r '.mutationBase.token // empty')
[ -n "$NEXT_BASE" ] && BASE="$NEXT_BASE"

# Suggest and immediately apply (tracked, committed)
OP_RESP=$(curl -s -X POST "https://www.proofeditor.ai/api/agent/abc123/ops" \
  -H "Content-Type: application/json" \
  -H "x-share-token: xxx" \
  -H "X-Agent-Id: editor:automation" \
  -H "Idempotency-Key: $(uuidgen)" \
  -d "$(jq -n --arg base "$BASE" '{type:"suggestion.add",kind:"replace",quote:"old",by:"editor:automation",content:"new",status:"accepted",baseToken:$base}')")
NEXT_BASE=$(printf '%s' "$OP_RESP" | jq -r '.mutationBase.token // empty')
[ -n "$NEXT_BASE" ] && BASE="$NEXT_BASE"

# Direct content edit (preferred when visible suggestion marks are not needed)
SNAPSHOT=$(curl -s "https://www.proofeditor.ai/api/agent/abc123/snapshot" \
  -H "x-share-token: xxx")
EDIT_BASE=$(printf '%s' "$SNAPSHOT" | jq -r '.mutationBase.token')
curl -X POST "https://www.proofeditor.ai/api/agent/abc123/edit/v2?return=minimal" \
  -H "Content-Type: application/json" \
  -H "x-share-token: xxx" \
  -H "X-Agent-Id: editor:automation" \
  -H "Idempotency-Key: $(uuidgen)" \
  -d "$(jq -n --arg base "$EDIT_BASE" '{by:"editor:automation",baseToken:$base,operations:[{op:"find_replace_in_doc",find:"old",replace:"new",occurrence:"all"}]}')"
```

## Workflow: Create and Share a New Document

**Publishing a local file (the primary case):** read the file and JSON-encode its full contents into the `markdown` field with `jq --rawfile` so newlines, quotes, and backticks are escaped correctly. Never hand-write the body or leave the inline placeholder — that publishes a placeholder doc instead of the source artifact (the plan, requirements, or ideation file the caller passed).

```bash
SRC="docs/plans/2026-05-04-001-feat-foo-plan.md"   # source file from the caller
TITLE="Plan: Foo"                                   # caller-provided title

# 1. Create — from a local source file:
RESPONSE=$(jq -n --arg title "$TITLE" --rawfile md "$SRC" '{title:$title, markdown:$md}' \
  | curl -s -X POST https://www.proofeditor.ai/share/markdown \
    -H "Content-Type: application/json" -d @-)
# (Ad-hoc inline content instead of a file:
#  -d '{"title":"My Doc","markdown":"# Title\n\nContent here."}')

# 2. Extract URL and token
URL=$(echo "$RESPONSE" | jq -r '.tokenUrl')
SLUG=$(echo "$RESPONSE" | jq -r '.slug')
TOKEN=$(echo "$RESPONSE" | jq -r '.accessToken')

# 3. Bind display name via presence
curl -s -X POST "https://www.proofeditor.ai/api/agent/$SLUG/presence" \
  -H "Content-Type: application/json" \
  -H "x-share-token: $TOKEN" \
  -H "X-Agent-Id: editor:automation" \
  -d '{"name":"Document Editor","status":"reading","summary":"Uploaded doc"}'

# 4. Share the URL
echo "$URL"

# 5. Make comment/suggestion edits using the ops endpoint (baseToken required)
BASE=$(curl -s "https://www.proofeditor.ai/api/agent/$SLUG/state" \
  -H "x-share-token: $TOKEN" | jq -r '.mutationBase.token')
OP_RESP=$(curl -s -X POST "https://www.proofeditor.ai/api/agent/$SLUG/ops" \
  -H "Content-Type: application/json" \
  -H "x-share-token: $TOKEN" \
  -H "X-Agent-Id: editor:automation" \
  -H "Idempotency-Key: $(uuidgen)" \
  -d "$(jq -n --arg base "$BASE" '{type:"comment.add",quote:"Content here",by:"editor:automation",text:"Added a note",baseToken:$base}')")
NEXT_BASE=$(printf '%s' "$OP_RESP" | jq -r '.mutationBase.token // empty')
[ -n "$NEXT_BASE" ] && BASE="$NEXT_BASE"

# For content edits, prefer /edit/v2 over rewrite.apply.
SNAPSHOT=$(curl -s "https://www.proofeditor.ai/api/agent/$SLUG/snapshot" \
  -H "x-share-token: $TOKEN")
EDIT_BASE=$(printf '%s' "$SNAPSHOT" | jq -r '.mutationBase.token')
curl -X POST "https://www.proofeditor.ai/api/agent/$SLUG/edit/v2?return=minimal" \
  -H "Content-Type: application/json" \
  -H "x-share-token: $TOKEN" \
  -H "X-Agent-Id: editor:automation" \
  -H "Idempotency-Key: $(uuidgen)" \
  -d "$(jq -n --arg base "$EDIT_BASE" '{by:"editor:automation",baseToken:$base,operations:[{op:"find_replace_in_doc",find:"Content",replace:"Updated content",occurrence:"all"}]}')"
```

## Workflow: Pull a Proof Doc to Local

Sync the current Proof doc state to a local markdown file. Used for:

- Ad-hoc snapshots of a Proof doc to disk (before closing the tab, archiving, handing off)
- Pulling a shared Proof doc that the user (or others) edited back down to a local working copy
- Refreshing a local working copy against the live Proof version

```bash
SLUG=<slug>
TOKEN=<accessToken>
LOCAL=<absolute-path>

# Keep scratch data under the JJ workspace root, with a local fallback outside a workspace.
if WORKSPACE_ROOT=$(jj workspace root 2>/dev/null); then
  TMP_DIR="$WORKSPACE_ROOT/.tmp/rocketclaw"
else
  TMP_DIR=".tmp/rocketclaw"
fi
mkdir -p "$TMP_DIR"
STATE_TMP="$TMP_DIR/proof-state.$$"
curl -s "https://www.proofeditor.ai/api/agent/$SLUG/state" \
  -H "x-share-token: $TOKEN" > "$STATE_TMP"
REVISION=$(jq -r '.revision' "$STATE_TMP")

# Stream .markdown bytes directly to workspace-local scratch, then move into place.
TMP="$TMP_DIR/proof-markdown.$$"
jq -jr '.markdown' "$STATE_TMP" > "$TMP" && mv "$TMP" "$LOCAL"
rm "$STATE_TMP"
```

`jq -jr` (`-j` no trailing newline, `-r` raw string) streams the markdown bytes straight to workspace-local scratch without going through a shell variable, so trailing newlines survive intact. The final `mv` is atomic when the workspace scratch directory and destination share a filesystem.

**Confirm before writing when the pull isn't directly asked for.** If a workflow ends up pulling as a side-effect of a different action, surface the impending write with a short confirm like "Sync Proof doc to `<localPath>`?" A silent overwrite is surprising — the user may have forgotten the local file exists in that session, or expected Proof to stay canonical until they explicitly asked to pull.

## Safety

- Use `/state` content as source of truth before editing
- During active collab use `edit/v2` (direct block changes) or `suggestion.add` (tracked changes); reserve `rewrite.apply` for no-client scenarios since it's blocked by `LIVE_CLIENTS_PRESENT` when anyone is connected
- Prefer `find_replace_in_doc` and block-level `/edit/v2` edits before considering `rewrite.apply`
- Don't span table cells in a single replace
- Always include `by: "editor:automation"` on every op and `X-Agent-Id: editor:automation` in headers for a consistent operation identity
- Reuse `baseToken` from your most recent `/state` or `/snapshot` read; on `STALE_BASE`, re-read and retry once
