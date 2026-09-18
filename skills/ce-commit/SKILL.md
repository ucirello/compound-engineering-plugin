---
name: ce-commit
description: Create a JJ change with a clear, value-communicating description. Use when the user asks to commit/save working-copy changes with a project-appropriate description.
---

# JJ Change

Create well-crafted local change(s) from the current working copy. No push, no PR — use `ce-commit-push-pr` for the full ship flow.

**Done when:** each logical change is saved with an explicit file list and a description that states the outcome, and `jj status` is clean of those changes. **Stop when:** the working copy has nothing to save.

## Context

Run every `jj` command with the shell tool's working directory set to the workspace root from `jj workspace root`. Do not use `jj -R`. File lists are repo-relative.

Gather context with each command as its **own** shell tool call (program + args only). Do **not** join with `;`, `&&`, `||`, pipes, `$(...)`, or redirects — that syntax fails under Windows PowerShell. A non-zero exit is a normal state to interpret, not a failure to suppress. If JJ cannot provide required information, stop.

| Command | Purpose | Non-zero / empty means |
| --- | --- | --- |
| `jj workspace root` | Workspace root | Not a JJ repo — stop |
| `jj status` | Working-copy state | Not a JJ repo — stop |
| `jj diff` | Working-copy changes vs parent | Empty working-copy change |
| `jj bookmark list -r @` | Bookmarks on `@` | Empty = no bookmark on the working-copy change |
| `jj log -n 10` | Recent description style | Not a JJ repo |
| `jj bookmark list` | Local bookmarks; remotes as `name@origin` | No remotes — try `gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'`, else `main` |

Treat this as a snapshot. Re-read bookmarks and the working-copy file list immediately before saving if anything may have changed.

**Default bookmark name:** prefer `trunk()`, else the remote default (`main@origin` / `trunk@origin` / `master@origin`). Strip a trailing `@origin` (so `trunk@origin` → `trunk`). Use that bare name for all “on the default bookmark?” checks — never compare against `name@origin`.

## Workflow

0. **Gather** — run every Context command above (own shell call each), then continue.

1. **Nothing to save** — if `jj status` shows no working-copy changes, report that and stop.

2. **Bookmark first** — before saving, `@` must have a non-default bookmark, and the default bookmark must not point at `@`. If `@` has no bookmark, or the only bookmark on `@` is the default (`main` / `master` / `trunk` / the bare default name above), `jj bookmark create <name>` from the change content. If the default bookmark points at `@`, `jj bookmark move <default> --to @- --allow-backwards`. Do not `jj new` first — that would leave the current changes as a sibling. Then re-read `jj bookmark list -r @`. Do not ask — save-only still must not leave work only on an unbookmarked change or the default bookmark. If the derived name exists, pick a non-conflicting suffix.

3. **Description** — Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Repo-local syntax from project instructions and `git log` ALWAYS wins when it differs from Go guidance. Apply compatible Go guidance to quality, clarity, and structure without replacing local syntax. User override wins.

4. **Logical changes** — if changed files clearly split into distinct concerns, save separate changes (file level only, 2–3 max, no interactive hunk splitting). If ambiguous, one change.

5. **Message** — the composed message is constrained as follows, without substituting a fixed subject or type prefix: the subject is imperative and names the outcome (what is now possible or fixed), not the file list. Body only when motivation or trade-offs are not obvious from the subject. When a plan Implementation Unit ID is already in hand for this change (conversation, caller, or the files belong to one unit), append that unit's U-ID in parentheses — `(U3)` means unit 3. Do not hunt for a plan. Omit when the change spans units, the unit is unclear, or no plan is in hand.

6. **Save** — there is no index and no staging step. Name filesets on `jj commit`. Honor `exclude:<paths>` when the invocation carries it: those files stay in the working copy no matter what else changed; say in the report that they were left out.

   Resolve `<workspace-root>` from `jj workspace root`. Write the full composed message — subject line, blank line, optional body — to a file under `<workspace-root>/.tmp/rocketclaw/ce-commit/` with your file-write tool. Then pass that file's content as a single `-m` argv argument (the tool call carries the string; do not interpolate it through a shell):

   ```bash
   jj commit -m "<message composed from the standards above>" -- file1 file2 file3
   ```

   Use `jj describe -m "<message composed from the standards above>"` only when the current change should keep these files and only receive a description; that does not make `jj status` clean of them. The save path that meets Done is `jj commit`.

   `$`, quotes, backticks, or a multi-line body must pass through literally as the `-m` value.

   The trailing fileset on `jj commit` is required: a bare `jj commit` takes the whole working-copy change, so `exclude:` paths or work this run did not name would be saved too. Naming the paths saves exactly the group and leaves other working-copy files in `@`.

   After saving, the feature bookmark must point at the tip of the work just saved. `jj commit` does not move bookmarks forward; if the bookmark remains on an ancestor of that tip, `jj bookmark move <name> --to <tip>`.

7. **Confirm** — `jj status`; report change id(s) and subject(s).
