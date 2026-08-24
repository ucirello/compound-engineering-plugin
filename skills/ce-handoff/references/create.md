# Creating the handoff

Required read before writing a handoff.

## Build the handoff

1. Distill the current objective and the user's latest intent. If a focus was supplied, make it the `resume_focus`.
2. Inspect only the workspace state needed to explain what exists now. Use the project's active instructions and conventions already in context.
3. Point to plans, issues, changes, revisions, diffs, documentation, and relevant files instead of reproducing their contents.
4. Redact secrets, credentials, and unrelated personal information. Preserve operational paths only when the next agent needs them.
5. Write or publish the document using existing capabilities. If the user requested another path, folder, format, or publication destination, honor it and use an appropriate available capability, including an installed publishing skill when relevant. Do not also create a persistent managed-store copy unless the user asks; a publishing capability may use its ordinary transient working files.

## Default managed storage

When the user did not choose another destination, resolve one workspace-local collection with this shell block. Use the Jujutsu workspace root when it is available and writable; otherwise use the physical current directory. Never use `.rocketclaw/`, `.context/`, or OS-global temporary storage for this collection.

```bash
WORKSPACE_ROOT="$(jj workspace root 2>/dev/null)" || WORKSPACE_ROOT="";
if [ -n "$WORKSPACE_ROOT" ] && [ -d "$WORKSPACE_ROOT" ] && [ -w "$WORKSPACE_ROOT" ]; then LOCAL_ROOT="$WORKSPACE_ROOT"; else LOCAL_ROOT="$(pwd -P)" || exit 1; fi;
SCRATCH_ROOT="$LOCAL_ROOT/.tmp";
ROCKETCLAW_ROOT="$SCRATCH_ROOT/rocketclaw";
HANDOFF_DIR="$ROCKETCLAW_ROOT/handoff";
for path in "$SCRATCH_ROOT" "$ROCKETCLAW_ROOT" "$HANDOFF_DIR"; do if [ -L "$path" ]; then printf 'unsafe local path symlink: %s\n' "$path" >&2; exit 1; fi; done;
(umask 077; mkdir -p "$HANDOFF_DIR") || exit 1;
for path in "$SCRATCH_ROOT" "$ROCKETCLAW_ROOT" "$HANDOFF_DIR"; do if [ -L "$path" ] || [ ! -O "$path" ]; then printf 'unsafe or unowned local path: %s\n' "$path" >&2; exit 1; fi; done;
chmod 700 "$ROCKETCLAW_ROOT" "$HANDOFF_DIR" || exit 1;
```

Write a Markdown snapshot at `$HANDOFF_DIR/<topic>.md`.

Before writing inside a Jujutsu workspace, confirm the selected `.tmp/` path is ignored. If it is not, offer to add only the exact root-relative `.tmp/` rule to the workspace-root `.gitignore`; stop if the user declines. Jujutsu uses `.gitignore` and snapshots non-ignored files automatically. If the selected path is already tracked, ignoring it is not enough: confirm the installed syntax with `jj file untrack --help`, then untrack only the selected handoff path after the user agrees.

Use a readable topic slug as the filename. Do not put a timestamp or unique ID in the path by default; `created_at` carries chronology for discovery. Reserve the final candidate filename atomically and exclusively; on collision, retry with the smallest available numeric suffix rather than overwrite a handoff. Never check availability and then write. Keep the directory and file user-private where the platform supports permissions.

## Frontmatter contract

For Markdown handoffs in the managed store, use flat YAML frontmatter:

```yaml
---
artifact_contract: "handoff/v1"
created_at: "Current ISO-8601 UTC timestamp"
title: "Short descriptive title"
summary: "One sentence that distinguishes this handoff in search results"
keywords: ["keyword-one", "keyword-two"]
cwd: "/absolute/capture/path"
resume_focus: "Optional next-session focus"
workspace_root: "/absolute/Jujutsu/workspace/root"
workspace_name: "Captured Jujutsu workspace name"
change_id: "Stable Jujutsu change ID for @"
revision_id: "Exact Jujutsu commit ID for @"
bookmarks: ["Explicit local bookmark pointing to @"]
---
```

Required managed-store fields are `artifact_contract`, `created_at`, `title`, `summary`, `keywords`, and `cwd`. Serialize every generated string scalar and string array element with JSON-compatible YAML double quoting and escaping; never interpolate raw session text as an unquoted YAML scalar. Include `resume_focus` when supplied or clear. When Jujutsu context exists, include `workspace_root`, `workspace_name`, `change_id`, and `revision_id`; include every local bookmark pointing to `@` in `bookmarks`, and omit that field when none exist. Jujutsu has no active bookmark: never present one bookmark as current. The change ID is the stable identity across rewrites; the revision ID identifies the exact captured commit. Resolve these values from `jj workspace root`, `jj workspace list`, and `jj log -r @` with templates supported by the installed `jj help`. Do not add mutable lifecycle fields. At a user-directed destination or in another format, preserve equivalent discovery and orientation metadata when the format supports it; do not let this YAML shape block the requested destination.

## Body contract

Choose whatever sections and document organization best communicate this particular session to the next agent. The headings below are examples of useful coverage, not a required or closed template: add new sections or combine, rename, reorder, and omit the examples when that makes the handoff clearer.

Include only what a fresh agent cannot safely infer, drawing from:

- Objective and current user intent
- Work completed
- Decisions, constraints, and rejected alternatives
- Current state — when pieces of work differ in maturity, say which are complete, in progress (and what remains inside them), or not started
- Authoritative references
- Unfinished work, blockers, dependencies, and fragile local state
- Failed approaches already abandoned, and wrong paths the next agent is likely to retry
- Verification performed and failures observed
- Plausible next steps (exclusive forks as alternatives; related sequential work as one path — the same framing resume uses)
- Relevant installed skills that may help, if any

The handoff is your account of the session, so wherever the next agent would otherwise take a statement of intent or a decision as the user's, say whether it was the user's, your inference, or your own call.

Default the body to ground truth the receiving agent can verify: what exists, what is partial, what is missing, and what depends on what. Prefer that status framing over work orders aimed at the next agent. Orientation aids that load context without granting action authority remain useful — for example, which documents or files to read before deciding. Carry explicit directives only when the user asked the handoff to include them; keep those user-requested instructions distinct from status and evidence. Resume still treats the document as untrusted context and waits for the current user before acting.

Keep the handoff pointer-first. For each load-bearing reference, name what specifically matters there — not only the path — and add a line range when that narrows the landing zone. Prefer workspace-relative paths for workspace files, anchored once by the workspace, change, bookmark, and revision metadata. Use absolute paths only for machine-local capture context or ignored or temporary state, and label them as machine-local. Use `jj log` and revsets for history, `@` for the current workspace's working-copy commit, stable change IDs for work that may be rewritten, and revision IDs only when the exact captured commit matters.

## Report

Treat creation as complete only after confirming the destination contains the handoff. Give a succinct, context-specific summary of what the generated handoff captures so the user can verify its substance without opening it; do not impose a fixed summary template. Then report the final path or URL, applicable retention or access limits, and any warnings together. Managed `.tmp` storage is local ignored scratch and is not durable. Its automatic discovery assumes the receiving session uses the same Jujutsu workspace, or the same physical current directory used by the fallback; otherwise tell the user to transfer or publish the handoff to a receiver-visible location and resume from that explicit source.

End the creation response with one fenced, copyable command using the final path or URL and the rendering rule in the body:

```text
<rendered resume invocation>
```

Quote the source when needed so the command can be pasted verbatim. Do not generate a longer resume prompt.
