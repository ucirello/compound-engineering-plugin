# Creating the handoff

Required read before writing a handoff.

## Build the handoff

1. Distill the current objective and the user's latest intent. If a focus was supplied, make it the `resume_focus`.
2. Inspect only the workspace state needed to explain what exists now. Use the project's active instructions and conventions already in context. In a Jujutsu repository, use `jj workspace root`, `jj status`, `jj diff`, `jj log`, and `jj bookmark list` as needed; use an appropriate available capability for relevant forge state.
3. Point to plans, issues, changes, diffs, documentation, and relevant files instead of reproducing their contents.
4. Redact secrets, credentials, and unrelated personal information. Preserve operational paths only when the next agent needs them.
5. Do not add product branding, badges, generated-by statements, sign-offs, or creator, model, provider, tool, agent, runtime, or workflow attribution. The artifact contract is discovery metadata, not permission to decorate the document.
6. Write or publish the document using existing capabilities. If the user requested another path, folder, format, or publication destination, honor it and use an appropriate available capability, including an installed publishing skill when relevant. Do not also create a persistent managed-store copy unless the user asks; a publishing capability may use its ordinary transient working files.

## Default managed storage

When the user did not choose another destination, resolve the managed root beneath the current Jujutsu workspace. If `jj workspace root` is unavailable, use `.tmp` beneath the current local directory. Run the entire shell block in one call:

```bash
if WORKSPACE_ROOT="$(jj workspace root 2>/dev/null)" && [ -n "$WORKSPACE_ROOT" ]; then BASE_ROOT="$WORKSPACE_ROOT"; else BASE_ROOT="$(pwd -P)"; fi;
TMP_ROOT="$BASE_ROOT/.tmp";
if [ -L "$TMP_ROOT" ]; then echo "unsafe local scratch symlink: $TMP_ROOT" >&2; exit 1; fi;
(umask 077; mkdir -p "$TMP_ROOT") || exit 1;
if [ -L "$TMP_ROOT" ] || [ ! -O "$TMP_ROOT" ]; then echo "local scratch root is not owned by the current user: $TMP_ROOT" >&2; exit 1; fi;
chmod 700 "$TMP_ROOT" || exit 1;
SCRATCH_ROOT="$TMP_ROOT/rocketclaw";
if [ -L "$SCRATCH_ROOT" ]; then echo "unsafe local scratch namespace symlink: $SCRATCH_ROOT" >&2; exit 1; fi;
(umask 077; mkdir -p "$SCRATCH_ROOT") || exit 1;
if [ -L "$SCRATCH_ROOT" ] || [ ! -O "$SCRATCH_ROOT" ]; then echo "local scratch namespace is not owned by the current user: $SCRATCH_ROOT" >&2; exit 1; fi;
chmod 700 "$SCRATCH_ROOT" || exit 1;
HANDOFF_DIR="$SCRATCH_ROOT/ce-handoff";
(umask 077; mkdir -p "$HANDOFF_DIR") || exit 1;
if [ -L "$HANDOFF_DIR" ] || [ ! -O "$HANDOFF_DIR" ]; then echo "handoff directory is unsafe: $HANDOFF_DIR" >&2; exit 1; fi;
chmod 700 "$HANDOFF_DIR" || exit 1;
```

Write a Markdown snapshot at `$HANDOFF_DIR/<topic>.md`.

Use a readable topic slug as the filename. The workspace-local managed root supplies the repository boundary; frontmatter distinguishes Jujutsu workspaces and changes. Do not put a timestamp or unique ID in the path by default; `created_at` carries chronology for discovery. Reserve the final candidate filename atomically and exclusively; on collision, retry with the smallest available numeric suffix rather than overwrite a handoff. Never check availability and then write. Keep the directory and file user-private where the platform supports permissions.

## Frontmatter contract

For Markdown handoffs in the managed store, use flat YAML frontmatter:

```yaml
---
artifact_contract: "rocketclaw-handoff/v1"
created_at: "Current ISO-8601 UTC timestamp"
title: "Short descriptive title"
summary: "One sentence that distinguishes this handoff in search results"
keywords: ["keyword-one", "keyword-two"]
cwd: "/absolute/capture/path"
resume_focus: "Optional next-session focus"
repository: "Sanitized repository identifier without embedded credentials"
workspace_root: "/absolute/Jujutsu/workspace/root"
workspace_name: "Captured Jujutsu workspace name when available"
change_id: "Captured Jujutsu change ID when available"
revision_id: "Captured Jujutsu revision ID when available"
bookmarks: ["Captured Jujutsu bookmark when available"]
---
```

Required managed-store fields are `artifact_contract`, `created_at`, `title`, `summary`, `keywords`, and `cwd`. Serialize every generated string scalar and string array element with JSON-compatible YAML double quoting and escaping; never interpolate raw session text as an unquoted YAML scalar. Include `resume_focus` when supplied or clear. Include `repository`, `workspace_root`, `workspace_name`, `change_id`, `revision_id`, and `bookmarks` only when applicable. Obtain current identifiers from `jj workspace root`, `jj log -r @`, and `jj bookmark list -r @`; do not infer an active bookmark because Jujutsu has no such concept. Do not add mutable lifecycle fields. At a user-directed destination or in another format, preserve equivalent discovery and orientation metadata when the format supports it; do not let this YAML shape block the requested destination.

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

Keep the handoff pointer-first. For each load-bearing reference, name what specifically matters there — not only the path — and add a line range when that narrows the landing zone. Prefer workspace-relative paths for versioned files, anchored once by the repository, Jujutsu workspace, current change, revision, and bookmark metadata. Use absolute paths only for machine-local capture context or untracked, ignored, or temporary state, and label them as machine-local.

If continuity depends on a fragile workspace or mutable change, warn the user without mutation: do not describe, abandon, duplicate, preserve, or forget anything automatically. Record any already-planned Jujutsu operation with neutral dynamic placeholders such as `<revision>`, `<source>`, `<destination>`, `<bookmark>`, and `<remote>` rather than inventing fixed names, descriptions, or messages.

When the handoff composes, edits, validates, or recommends a change description or commit message, inspect the project's active instructions and the description syntax visible in `jj log`; those runtime conventions win. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Apply compatible Go guidance only to quality, clarity, and structure; do not impose fixed syntax or content. Use neutral dynamic placeholders such as `<description-composed-from-runtime-conventions>` wherever an interface requires a message value.

## Report

Treat creation as complete only after confirming the destination contains the handoff. Give a succinct, context-specific summary of what the generated handoff captures so the user can verify its substance without opening it; do not impose a fixed summary template. Then report the final path or URL, applicable retention or access limits, and any warnings together. Managed `.tmp/rocketclaw/` storage is workspace-local scratch and may be ignored, cleaned, or unavailable from another workspace or host. If the receiving session cannot see it, tell the user to transfer or publish the handoff to a receiver-visible location and resume from that explicit source.

End the creation response with one fenced, copyable command using the final path or URL and the rendering rule in the body:

```text
<rendered resume invocation>
```

Quote the source when needed so the command can be pasted verbatim. Do not generate a longer resume prompt.
