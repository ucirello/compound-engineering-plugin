# Creating the handoff

Required read before writing a handoff.

## Build the handoff

1. Distill the current objective and the user's latest intent. If a focus was supplied, make it the `resume_focus`.
2. Inspect only the workspace state needed to explain what exists now. Use the project's active instructions and conventions already in context.
3. Point to plans, issues, Jujutsu changes, commits, diffs, documentation, and relevant files instead of reproducing their contents.
4. Redact secrets, credentials, and unrelated personal information. Preserve operational paths only when the receiving AI Assistant needs them.
5. Write or publish the document using existing capabilities. If the user requested another path, folder, format, or publication destination, honor it and use an appropriate available capability, including an installed publishing skill when relevant. Do not also create a persistent managed-store copy unless the user asks; a publishing capability may use its ordinary transient working files.

## Default managed storage

When the user did not choose another destination, use only `$(jj workspace root)/.tmp/rocketclaw/handoffs/`. Outside a Jujutsu workspace, use only `./.tmp/rocketclaw/handoffs/`. In a Jujutsu workspace, first confirm that existing ignore rules exclude `.tmp/rocketclaw/` from working-copy snapshots. If they do not, stop and report the blocker rather than editing ignore configuration or putting the handoff into the working-copy change.

Resolve the managed root with this POSIX and Git Bash compatible shell block:

```bash
WORKSPACE_ROOT="$(jj workspace root 2>/dev/null)" || WORKSPACE_ROOT="$PWD";
SCRATCH_ROOT="$WORKSPACE_ROOT/.tmp/rocketclaw";
[ ! -L "$SCRATCH_ROOT" ] && (umask 077; mkdir -p "$SCRATCH_ROOT") && [ ! -L "$SCRATCH_ROOT" ] && [ -O "$SCRATCH_ROOT" ] && chmod 700 "$SCRATCH_ROOT" || { echo "unsafe scratch root: $SCRATCH_ROOT" >&2; exit 1; };
HANDOFF_DIR="$SCRATCH_ROOT/handoffs/<repository-namespace>";
(umask 077; mkdir -p "$HANDOFF_DIR") || exit 1; chmod 700 "$HANDOFF_DIR" || exit 1;
```

Write a Markdown snapshot at `$HANDOFF_DIR/<topic>.md`.

Use a readable topic slug as the filename. Within a Jujutsu workspace, derive the repository namespace from verified repository identity, preferring a sanitized Git remote identity when the backend exposes one and otherwise using a sanitized workspace name. Do not use Jujutsu's synthetic root commit as repository identity. Outside Jujutsu, use `general`. Do not put a timestamp or unique ID in the path by default; `created_at` carries chronology for discovery. Reserve the final candidate filename atomically and exclusively; on collision, retry with the smallest available numeric suffix rather than overwrite a handoff. Never check availability and then write. Keep the directory and file user-private where the platform supports permissions.

This stable workspace-local collection intentionally omits a per-run directory so later invocations can enumerate handoffs directly. Never overwrite, relocate, or clean another handoff as part of creation.

## Jujutsu repository semantics

When the current directory is in a Jujutsu workspace, treat JJ as the source of truth. Resolve the workspace with `jj workspace root`; inspect the working-copy change and conflicts with `jj status`, its content with `jj diff`, relevant history and descriptions with `jj log`, and publication names with `jj bookmark list`. Use stable change IDs for continuity across rewrites and include current commit IDs when the exact materialized commit matters. Record the workspace name and bookmark targets when they matter. Jujutsu has no staging area, active branch, or Git-style detached `HEAD`; do not translate `@`, bookmarks, or workspace state into those concepts.

Capture only state needed for continuity. Distinguish the working-copy change from its parents, note unresolved conflicts or divergent bookmarks, and identify any fragile operation-log or workspace dependency. Jujutsu commands normally snapshot the working copy; report the state actually observed rather than claiming separate staged and unstaged snapshots.

Use `jj git` only for Git-backed interoperability. `jj git remote list` and `jj git root` may establish sanitized remote or backend identity. In a colocated repository, Git and JJ can operate side by side and import/export is normally automatic. When an operational Git-only tool is required in a non-colocated repository, export JJ state before that tool and import its changes afterward using the installed JJ version's supported commands. Never use Git `HEAD` or a Git branch to override JJ change and bookmark state.

Keep `gh` for GitHub issue, pull-request, repository, and URL evidence. A GitHub head branch corresponds operationally to a pushed JJ bookmark; verify that bookmark and remote rather than inventing a current branch. Preserve provider, model, runtime, Git Bash, or GitHub details only when they materially affect reproduction, access, or continuation, never as creator attribution.

When the handoff composes, edits, validates, or recommends a commit message or JJ change description, apply this requirement at that site exactly once:

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

The project's active instructions and syntax observed in current repository history win. Apply only compatible Go guidance to message quality, clarity, and structure. Preserve the required meaning with dynamic placeholders derived from runtime evidence; do not impose a fixed prefix, type, scope, subject, body, layout, syntax, template, or example.

## Frontmatter contract

For Markdown handoffs in the managed store, use flat YAML frontmatter. Required fields are `artifact_contract` with value `handoff/v1`, `actor` with value `ai:assistant`, `created_at`, `title`, `summary`, `keywords`, and `cwd`. Serialize every dynamic string scalar and string array element with JSON-compatible YAML double quoting and escaping; never interpolate raw session text as an unquoted YAML scalar.

Include `resume_focus` when supplied or clear. In a Jujutsu workspace, include applicable values from `repository`, `workspace_root`, `workspace`, `change_id`, `commit_id`, and `bookmarks`; include sanitized Git remote or GitHub repository identity only when operationally useful. Do not substitute Git-only state fields for JJ state. Do not add creator, model, provider, harness, generator, badge, byline, or mutable lifecycle fields. If another machine-readable protocol requires an actor, use `ai:assistant`; if it requires a prose actor label, use `AI Assistant`. At a user-directed destination or in another format, preserve equivalent discovery and orientation metadata when the format supports it; do not let the YAML shape block the requested destination.

## Body contract

Choose whatever sections and document organization best communicate this particular session to the receiving AI Assistant. Do not impose a fixed body syntax, heading set, template, or example. Include only what a fresh AI Assistant cannot safely infer, covering the applicable semantics:

- Objective and current user intent
- Work completed
- Decisions, constraints, and rejected alternatives
- Current state - when pieces of work differ in maturity, say which are complete, in progress and what remains inside them, or not started
- Authoritative references
- Unfinished work, blockers, dependencies, and fragile local state
- Failed approaches already abandoned, and wrong paths the receiving AI Assistant is likely to retry
- Verification performed and failures observed
- Plausible next steps, with exclusive forks as alternatives and related sequential work as one path
- Relevant installed skills that may help, if any

Wherever the receiving AI Assistant could mistake a statement of intent or a decision for the user's, distinguish the user's statement from the AI Assistant's inference or decision. Do not add creator attribution, generated-by text, model or harness attribution, badges, bylines, signatures, or product-marketing material.

Default the body to ground truth the receiving AI Assistant can verify: what exists, what is partial, what is missing, and what depends on what. Prefer that status framing over work orders aimed at the receiving AI Assistant. Orientation aids that load context without granting action authority remain useful, including which documents or files to read before deciding. Carry explicit directives only when the user asked the handoff to include them; keep those user-requested instructions distinct from status and evidence. Resume still treats the document as untrusted context and waits for the current user before acting.

Keep the handoff pointer-first. For each load-bearing reference, name what specifically matters there, not only the path, and add a line range when that narrows the landing zone. Prefer workspace-relative paths, anchored once by repository identity, workspace, stable change ID, current commit ID, and relevant bookmarks. Use absolute paths only for machine-local capture context or ignored and temporary state, and label them as machine-local.

## Report

Treat creation as complete only after confirming the destination contains the handoff. Give a succinct, context-specific summary of what the handoff captures so the user can verify its substance without opening it; do not impose a fixed summary template. Then report the final path or URL, applicable retention or access limits, and any warnings together. Managed `.tmp/rocketclaw` storage is workspace-local, ignored, and not a durable publication surface. Automatic discovery assumes the receiving session opens the same Jujutsu workspace, or the same current directory outside Jujutsu. Otherwise tell the user to transfer or publish the handoff to a receiver-visible location and resume from that explicit source.

End the creation response with one fenced, copyable command using the final path or URL and the rendering rule in the body:

```text
<rendered resume invocation>
```

Quote the source when needed so the command can be pasted verbatim. Do not generate a longer resume prompt.
