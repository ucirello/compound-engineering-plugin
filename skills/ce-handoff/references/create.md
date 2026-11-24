# Creating the handoff

Required read before writing a handoff.

## Build the handoff

1. Distill the current objective and the user's latest intent. If a focus was supplied, make it the `resume_focus`.
2. Inspect only the workspace state needed to explain what exists now. Use the project's active instructions and conventions already in context.
3. Point to plans, issues, commits, diffs, documentation, and relevant files instead of reproducing their contents.
4. Redact secrets, credentials, and unrelated personal information. Preserve operational paths only when the next agent needs them.
5. Write or publish the document using existing capabilities. If the user requested another path, folder, format, or publication destination, honor it and use an appropriate available capability, including an installed publishing skill when relevant. Do not also create a persistent managed-store copy unless the user asks; put any transient staging files in the workspace's ignored local `.tmp/`, or local `.tmp/` outside JJ.

## Default managed storage

When the user did not choose another destination, resolve the absolute base with `jj --at-operation=@ workspace root` (see [JJ workspace commands](https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace)). Run any further JJ commands from that absolute workspace root. Outside JJ, use the current absolute directory. If workspace resolution fails in a known JJ checkout, report the failure rather than silently choosing a different base. Use ignored local `.tmp/` in JJ; if that storage is not available, ask for a destination instead of modifying ignore rules or using a global temporary directory.

With `BASE` set to that absolute directory and `REPO_NAMESPACE` set as described below, initialize the managed directory:

```bash
case "$BASE" in /*) ;; *) exit 1 ;; esac
case "$REPO_NAMESPACE" in ''|*[!a-z0-9-]*) exit 1 ;; esac
HANDOFF_DIR="$BASE/.tmp/rocketclaw/ce-handoff/$REPO_NAMESPACE"
for dir in "$BASE/.tmp" "$BASE/.tmp/rocketclaw" \
           "$BASE/.tmp/rocketclaw/ce-handoff" "$HANDOFF_DIR"; do
  if [ -L "$dir" ]; then
    printf 'Unsafe handoff directory symlink: %s\n' "$dir" >&2
    exit 1
  fi
  (umask 077; mkdir -p -- "$dir") || exit 1
  if [ -L "$dir" ] || [ ! -d "$dir" ] || [ ! -O "$dir" ] || [ ! -w "$dir" ]; then
    printf 'Handoff directory is not an owned, writable directory: %s\n' "$dir" >&2
    exit 1
  fi
  [ "$dir" != "$BASE/.tmp" ] || continue
  chmod 700 -- "$dir" || exit 1
done
```

Write a Markdown snapshot at `$HANDOFF_DIR/<topic>.md`.

Use a readable topic slug as the filename. In JJ, derive the namespace from a sanitized repository name (lowercase letters, digits, and hyphens; use `repo` if the name is unknown) and a stable first real root-commit prefix when available. Query `jj --at-operation=@ log --no-graph -r 'roots(::@ ~ root())' -T 'commit_id ++ "\n"'` from the workspace root to exclude JJ's synthetic root; if there are multiple real roots, use the lexicographically first full ID. Outside JJ, use `general`. Each workspace has its own managed store; a shared namespace helps identify the repository but does not make other workspaces' files automatically discoverable.

Do not put a timestamp or unique ID in the path by default; `created_at` carries chronology for discovery. Reserve the final candidate filename atomically and exclusively; on collision, retry with the smallest available numeric suffix rather than overwrite a handoff. Never check availability and then write. Keep the directory and file user-private where the platform supports permissions.

## Frontmatter contract

For Markdown handoffs in the managed store, use flat YAML frontmatter:

```yaml
---
artifact_contract: "ce-handoff/v1"
created_at: "Current ISO-8601 UTC timestamp"
title: "Short descriptive title"
summary: "One sentence that distinguishes this handoff in search results"
keywords: ["keyword-one", "keyword-two"]
cwd: "/absolute/capture/path"
resume_focus: "Optional next-session focus"
repository: "Sanitized repository identifier without embedded credentials"
repo_root_sha: "First real root commit ID when available"
branch: "Verified JJ bookmark when applicable"
head: "Recorded JJ working-copy commit ID when available"
worktree_path: "Absolute JJ workspace path when relevant"
---
```

Required managed-store fields are `artifact_contract`, `created_at`, `title`, `summary`, `keywords`, and `cwd`. Serialize every generated string scalar and string array element with JSON-compatible YAML double quoting and escaping; never interpolate raw session text as an unquoted YAML scalar. Include `resume_focus` when supplied or clear. Keep the existing optional `ce-handoff/v1` keys for discovery. Use `jj --at-operation=@ log --no-graph -r @ -T 'commit_id ++ "\n"'` from the absolute workspace root to capture the recorded working-copy commit without taking a new snapshot. It may not include current on-disk edits; distinguish those separately. Include `branch` only for an applicable verified bookmark, not an assumed current branch. Include `repository`, `repo_root_sha`, `head`, and `worktree_path` only when applicable. Do not add mutable lifecycle fields. At a user-directed destination or in another format, preserve equivalent discovery and orientation metadata when the format supports it; do not let this YAML shape block the requested destination.

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

Keep the handoff pointer-first. For each required reference, name what specifically matters there — not only the path — and add a line range when that narrows the landing zone. Prefer repository-relative paths for repository files, anchored once by the available repository, bookmark, and commit metadata. Use absolute paths only for machine-local capture context or uncommitted, untracked, ignored, or temporary state, and label them as machine-local.

## Report

Treat creation as complete only after confirming the destination contains the handoff. Give a succinct, context-specific summary of what the generated handoff captures so the user can verify its substance without opening it; do not impose a fixed summary template. Then report the final path or URL, applicable retention or access limits, and any warnings together. Workspace-local `.tmp/` storage is not permanent; it can disappear with workspace cleanup. Automatic discovery uses only the receiving session's workspace (or current directory outside JJ). From another workspace on the same host, resume using the verified absolute path if accessible. If the receiver cannot read it, tell the user to transfer or publish to a receiver-visible location before resuming.

Tell the user to open a fresh OpenCode session (for example, `/new` in the TUI) in the intended workspace. Do not start it for them. End the creation response with one fenced, copyable OpenCode command:

```text
/ce-handoff resume <source>
```

Quote the source when needed so the command can be pasted verbatim. Do not generate a longer resume prompt.
