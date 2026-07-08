---
name: ce-commit
description: Create a JJ change with a clear, value-communicating description. Use when the user asks to describe/save current changes with a repo-appropriate, value-communicating message.
---

# JJ Change Description

Create a single, well-crafted JJ change description from the current working tree changes.

## Context

**On platforms other than Claude Code**, skip to the "Context fallback" section below and run the command there to gather context.

**In Claude Code**, the five labeled sections below (JJ status, Working tree diff, Current bookmark, Recent changes, Remote default bookmark) contain pre-populated data. Use them directly throughout this skill -- do not re-run these commands.

**JJ status:**
!`jj st`

**Working tree diff:**
!`jj diff`

**Current bookmark:**
!`jj log -r 'bookmarks() & @' --no-graph -T 'bookmarks.join(" ")' 2>/dev/null || true`

**Recent changes:**
!`jj log -n 10 --no-graph -T 'change_id.short() ++ " " ++ description.first_line() ++ "\n"'`

**Remote default bookmark:**
!`jj log -r 'remote_bookmarks() & bookmarks(main)' --no-graph -T 'bookmarks.join(" ")' 2>/dev/null || echo '__DEFAULT_BOOKMARK_UNRESOLVED__'`

### Context fallback

**In Claude Code, skip this section — the data above is already available.**

Run this single command to gather all context:

```bash
printf '=== STATUS ===\n'; jj st; printf '\n=== DIFF ===\n'; jj diff; printf '\n=== BOOKMARK ===\n'; jj log -r 'bookmarks() & @' --no-graph -T 'bookmarks.join(" ")' 2>/dev/null || true; printf '\n=== LOG ===\n'; jj log -n 10 --no-graph -T 'change_id.short() ++ " " ++ description.first_line() ++ "\n"'; printf '\n=== DEFAULT_BOOKMARK ===\n'; jj log -r 'remote_bookmarks() & bookmarks(main)' --no-graph -T 'bookmarks.join(" ")' 2>/dev/null || echo '__DEFAULT_BOOKMARK_UNRESOLVED__'
```

---

## Workflow

### Step 1: Gather context

Use the context above (JJ status, working tree diff, current bookmark, recent changes, remote default bookmark). All data needed for this step is already available -- do not re-run those commands.

The remote default bookmark value may include something like `main@origin`. Strip the `@origin` suffix to get the bookmark name. If it returned `__DEFAULT_BOOKMARK_UNRESOLVED__` or empty output, try:

```bash
gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'
```

If both fail, fall back to `main`.

If the JJ status from the context above shows a clean working copy and the current change already has the intended description, report that there is nothing to describe and stop.

If the current change is not associated with a bookmark, that is valid in JJ. Do not create a bookmark here unless the user explicitly asked for a push/PR workflow; `ce-commit-push-pr` owns bookmark creation for sharing.

### Step 2: Determine change description convention

Follow this priority order:

1. **Repo conventions already in context** -- If project instructions (AGENTS.md, CLAUDE.md, or similar) are already loaded and specify commit message conventions, follow those. Do not re-read these files; they are loaded at session start.
2. **Recent change history** -- If no explicit convention is documented, examine the 10 most recent change descriptions from Step 1. If a clear pattern emerges (e.g., conventional commits, ticket prefixes, emoji prefixes), match that pattern.
3. **Default: conventional commits** -- If neither source provides a pattern, use conventional commit format for the JJ change description: `type(scope): description` where type is one of `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`, `ci`, `style`, `build`.

When using conventional commits, choose the type that most precisely describes the change (the type list above). Where `fix:` and `feat:` both seem to fit, default to `fix:`: a change that remedies broken or missing behavior is `fix:` even when implemented by adding code. Reserve `feat:` for capabilities the user could not previously accomplish. Other types remain primary when they fit better. The user may override for a specific change.

### Step 3: Consider logical changes

Before describing everything together, scan the changed files for naturally distinct concerns. If modified files clearly group into separate logical changes (e.g., a refactor in one directory and a new feature in another, or test files for a different change than source files), create separate JJ changes for each group.

Keep this lightweight:
- Group at the **file level only** -- use path-limited JJ operations when splitting; do not try to split hunks within a file.
- If the separation is obvious (different features, unrelated fixes), split. If it's ambiguous, one change is fine.
- Two or three logical changes is the sweet spot. Do not over-slice into many tiny changes.

### Step 4: Describe and advance

If the current bookmark from the context above is `main`, `master`, or the resolved default bookmark from Step 1, do not move the bookmark here. Describe the current change; bookmark creation for publishing belongs to `ce-commit-push-pr`.

Write the change description:
- **Subject line**: Concise, imperative mood, focused on *why* not *what*. Follow the convention determined in Step 2.
- **Body** (when needed): Add a body separated by a blank line for non-trivial changes. Explain motivation, trade-offs, or anything a future reader would need. Omit the body for obvious single-purpose changes.

For each change group, use `jj commit` with a heredoc to describe the current change and advance to a new empty working-copy change. If splitting into multiple changes, use JJ's file-level split/move operations first; do not stage everything with legacy VCS commands.

```bash
jj commit -m "$(cat <<'EOF'
type(scope): subject line here

Optional body explaining why this change was made,
not just what changed.
EOF
)"
```

### Step 5: Confirm

Run `jj st` and `jj log -r @- --no-graph -T 'change_id.short() ++ " " ++ description.first_line() ++ "\n"'` after each described change to verify success. Report the change ID(s) and subject line(s).
