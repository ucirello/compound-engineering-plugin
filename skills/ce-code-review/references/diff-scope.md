# Diff Scope Rules

These rules apply to every reviewer. They define what is "your code to review" versus pre-existing context.

## Scope Discovery

Determine the diff to review using this priority order:

1. **User-specified scope.** If the caller passed `BASE:`, `FILES:`, or `DIFF:` markers, use that scope exactly.
2. **Captured working-copy changes.** Use Stage 1's exact immutable base/head IDs, which include eligible working-copy changes.
3. **Committed bookmark work.** An empty `@` above the PR/bookmark head is not no-work. Include all work since the verified base; never guess main/master or recompute the helper's range.

Stage 1 handles discovery and passes the exact diff. Run every JJ command in the absolute target workspace root and every repository gh call with `GIT_DIR=$(jj git root)` there. No Git executable calls.

## Remote scope (`pr-remote` and `branch-remote`)

When the review context includes `<pr-scope-mode>pr-remote</pr-scope-mode>` or `<pr-scope-mode>branch-remote</pr-scope-mode>`, the working tree is **not** the reviewed head. Do **not** use Read/Grep on workspace paths for any file that belongs to the reviewed tree — the changed-file list, and any other file the review points you at, such as a criteria file. They may not match the branch or PR under review, and an unchanged file is not exempt: the checkout can hold a version the reviewed head never had.

Instead:

- Prefer `jj file show -r <remote-head-ref> <path>` when `<pr-head-ref>` or `<branch-head-ref>` is provided in context.
- Otherwise rely on diff hunks in the provided `<diff>` only.
- Do not treat local workspace contents as evidence for findings on changed files.

## Whole-file deletions

A file the change deletes appears in the presentation diff as a header only: `deleted file mode` and its path. Its old body is left out. The `<deleted-files>` block lists exports and import-time behavior. Read a body only when needed with `jj file show -r <captured-base> <path>`; mechanics retain the raw deletion data.

Whether the surviving tree still uses a deleted file is the correctness and adversarial reviewers' question; their personas say what to check. That check needs the reviewed tree, and a body needs the base the block names. When you cannot read one of them (for example, remote scope with no head ref, or a block with no base), record in `residual_risks` which deleted files went unchecked and why; never report their liveness as checked. Every other reviewer reviews the files that survive, including what the deletion left behind there: imports, props, styles, flags, and assets that no longer have a reader. The body of a deleted file is not code to review.

## Evidence Tools (tool-adaptive)

Recall depends on how you find related code. A diff-local read plus a text `grep` misses callers reached through re-exports, aliases, and barrel files, and mis-hits identifiers inside strings, comments, or longer names. When a claim depends on a symbol's callers, implementations, or whether a construct appears elsewhere, use the strongest search your harness actually exposes, preferring in this order and falling through when a tier is unavailable:

1. **Symbol-aware search** — a references/definitions/implementations capability (LSP or an equivalent MCP tool) that follows renames, re-exports, and barrels text search cannot. Most reviewer harnesses do not expose one; when it is absent, drop to the next tier without ceremony.
2. **Structural (AST) search** — a syntax-tree matcher such as `ast-grep` (optional; may not be installed). For "does construct X occur elsewhere" it beats regex: it matches the parsed tree, ignoring formatting and skipping the string/comment hits `grep` reports as false positives.
3. **Text search (`grep`)** — always available; correct for genuinely lexical checks (config keys, string literals, log messages), and the fallback when the tiers above are not reachable.

No tool is complete: dynamic dispatch, reflection, dependency injection, string-keyed routes/config, generated code, and external consumers hide usages from all of them. This only bites a claim that rests on *exhaustive* coverage — "this symbol is unused," "nothing else calls this," "safe to change." For such a claim, when coverage is text-search-only or a hiding construct could apply, record the unresolved boundary in `residual_risks` (e.g. `callsite completeness: grep-only`) or step the finding down, rather than asserting absence or safety. A finding that does not turn on exhaustive coverage needs no such note.

In `pr-remote` / `branch-remote` scope the working tree is not the reviewed head — search targeted `jj file show -r <captured-head> <path>` output, not local changed paths.

## Finding Classification Tiers

Every finding you report falls into one of three tiers based on its relationship to the diff:

### Primary (directly changed code)

Lines added or modified in the diff. This is your main focus. Report findings against these lines at full confidence.

### Secondary (immediately surrounding code)

Unchanged code within the same function, method, or block as a changed line. If a change introduces a bug that's only visible by reading the surrounding context, report it -- but note that the issue exists in the interaction between new and existing code.

### Pre-existing (unrelated to this diff)

Issues in unchanged code that the diff didn't touch and doesn't interact with. Mark these as `"pre_existing": true` in your output. They're reported separately and don't count toward the review verdict. When history is what makes the pre-existing call, attach one concise provenance evidence line from targeted blame/log (see the line provenance rule in `subagent-template.md`).

**The rule:** If you'd flag the same issue on an identical diff that didn't include the surrounding file, it's pre-existing. If the diff makes the issue *newly relevant* (e.g., a new caller hits an existing buggy function), it's secondary.
