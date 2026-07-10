---
name: ce-commit
description: Create a JJ commit with a clear, value-communication message. Use when the user asks to commit/save current working-copy changes with a repo-appropriate, value-communicating message.
---

# JJ Commit

Describe and finish one or more well-crafted JJ changes from the working-copy commit.

Jujutsu has no staging area: the working copy is a commit (`@`), and most `jj` commands snapshot file-system changes into it. `jj commit` describes `@` and creates a new working-copy change on top. With filesets, selected changes remain in the commit being finished and unselected changes move to the new working-copy child.

## Context

**On platforms other than Claude Code**, skip to the "Context fallback" section below and run the command there to gather context.

**In Claude Code**, the labeled sections below contain pre-populated data. Use them directly throughout this skill -- do not re-run these commands.

**JJ status:**
!`jj status`

**Current diff:**
!`jj diff`

**Bookmarks pointing to the working-copy commit:**
!`jj bookmark list -r @`

**Recent changes:**
!`jj log -r '::@' --limit 10 --no-graph`

### Context fallback

**In Claude Code, skip this section — the data above is already available.**

Run this single command to gather all context:

```bash
printf '=== STATUS ===\n'; jj status; printf '\n=== DIFF ===\n'; jj diff; printf '\n=== BOOKMARKS AT @ ===\n'; jj bookmark list -r @; printf '\n=== LOG ===\n'; jj log -r '::@' --limit 10 --no-graph
```

## Workflow

### Step 1: Gather context

Use the context above (`jj status`, the diff of `@`, bookmarks pointing to `@`, and recent changes). All data needed for this step is already available -- do not re-run those commands.

If `jj status` shows no changes in the working-copy commit, report that there is nothing to finish and stop. Do not create an empty change.

Bookmarks are named pointers, not active branches: there is no current or checked-out bookmark. Do not create or move a bookmark unless the user explicitly asks; a working-copy change does not need a bookmark to be committed.

### Step 2: Determine commit message convention

Follow this priority order:

1. **Repo conventions already in context** -- If project instructions already loaded specify commit message conventions, follow those. Do not re-read these files; they are loaded at session start.
2. **Recent JJ history** -- If no explicit convention is documented, examine the descriptions of the 10 most recent changes from Step 1. If a clear pattern emerges, match that pattern.
3. **Default: conventional commits** -- If neither source provides a pattern, use conventional commit format: `type(scope): description` where type is one of `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`, `ci`, `style`, `build`.

When using conventional commits, choose the type that most precisely describes the change. Where `fix:` and `feat:` both seem to fit, default to `fix:`: a change that remedies broken or missing behavior is `fix:` even when implemented by adding code. Reserve `feat:` for capabilities the user could not previously accomplish. The user may override for a specific change.

### Step 3: Consider logical commits

Scan changed files for naturally distinct concerns. If modified files clearly group into separate logical changes, finish them as separate changes.

Keep this lightweight:

- Group at the **file level only** -- do not use interactive `jj split` unless the user explicitly asks for hunk-level separation.
- If the separation is obvious, separate it. If it is ambiguous, one change is fine.
- Two or three logical changes is the sweet spot. Do not over-slice.

### Step 4: Describe and finish

Write the change description:

- **Subject line**: Concise, imperative mood, focused on *why* not *what*. Follow the convention determined in Step 2.
- **Body** (when needed): Add a body separated by a blank line for non-trivial changes. Explain motivation, trade-offs, or anything a future reader would need. Omit the body for obvious single-purpose changes.

If all current changes belong together, finish `@` with:

```bash
jj commit -m "type(scope): subject line here"
```

Without filesets, this is equivalent to `jj describe -m "..."` followed by `jj new`: it updates the description of `@`, then creates a new empty working-copy change on top. Do not run an additional `jj new`.

For multiple file-level groups, finish one group at a time with path-limited commits:

```bash
jj commit path/to/file1 path/to/file2 -m "$(cat <<'EOF'
type(scope): subject line here

Optional body explaining why this change was made,
not just what changed.
EOF
)"
```

Each fileset selects changes to keep in the commit being finished. Changes outside those filesets move into the new working-copy child, where they remain available for the next group. Re-check `jj status` and `jj diff` after each path-limited commit before choosing the next filesets. Do not use Git-style staging commands.

### Step 5: Confirm

After each `jj commit`, run `jj log -r @- --no-graph` and record the completed change ID, commit ID, and description. For a path-limited commit, `@` should contain the unselected remainder; for the final commit, `@` should be a new empty change.

Run `jj status` after the final commit. Report every recorded change ID, commit ID, and subject line. If `@` is not empty, report the remaining paths rather than claiming all changes were committed.
