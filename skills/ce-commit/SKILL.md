---
name: ce-commit
description: Finalize selected local JJ changes with clear, value-communicating, repository-appropriate descriptions.
---

# Local commits

Create well-crafted local commits. No push or PR — use `ce-commit-push-pr` for the full ship flow. Use latest JJ exclusively, never direct Git (including read-only commands or fallbacks). JJ automatically snapshots files; there is no staging-area workflow.

**Done when:** each requested logical change has an explicit file list, a verified outcome-focused description, and a recorded commit/change ID, with unrelated work preserved. **Stop when:** nothing requested remains to finalize, or scope, conflicts, history, or permissions are uncertain.

## Context

Resolve `jj root`, then set each repository tool call's cwd to that absolute workspace root (`workspace_root` below). Never use `-R` instead of cwd. Read repository instructions. Inspect `jj status`, `jj diff --summary`, `jj diff`, `jj log --no-graph -r '@ | @-'`, `jj bookmark list`, and `jj workspace list` in separate calls. Inspect untracked and ignored files separately; snapshots do not protect ignored files. Stop on conflicts without discarding or resolving unrelated work.

Verify the actual history head from the current change's parents and relevant existing bookmarks. An empty `@` above the real head is not missing history. For merges inspect both parents and explicitly select the relevant lineage. Never assume `main@origin`, a remote, or a default branch. Report a genuine initial/no-history repository as such.

If repository-scoped `gh` is necessary, export `GIT_DIR=$(jj git root)` in its scoped shell call in the absolute workspace root before invoking `gh`. No fetch or network mutation is needed. Re-read status, selected files, current revision, parents, and bookmarks immediately before mutation. Preserve existing descriptions, other workers' work, and unrelated bookmarks. Do not rewrite published or immutable changes without explicit authorization. Reuse existing isolation; this skill does not create or remove workspaces.

## Workflow

1. **Nothing to finalize** — inspect complete status and file inventory, not just the diff. If `@` is empty and no requested undescribed nonempty change exists, report nothing to commit and stop. If a nonempty `@` already has a description, establish whether requested work is new before changing it.

2. **Protect the destination** — identify task and shared/default bookmarks. Do not move a default/shared bookmark. When a task bookmark is needed, derive a meaningful name from the change, collision-check registrations with `jj bookmark list`, and create it at the finalized task commit using `jj bookmark create <unique-task-name> -r <verified-finalized-commit>`. Preserve existing task/source bookmark names. Do not create a workspace to imitate branch checkout.

3. **Logical commits** — split only clearly distinct concerns (file level only, 2–3 groups maximum); otherwise one commit. Honor `exclude:<paths>`: excluded files and unrelated work must remain outside all finalized groups and be reported. There is no index to stage. Before composing any split description, read and execute step 4's full runtime guide/history contract. For partial selection use `jj split` with explicit literal file filesets; consult installed `jj split --help` for its noninteractive message-file option. Include renames/deletions deliberately, never interactive patch selection or broad all-files selection. Verify every resulting group's complete diff and exact file list. Do not split another worker's work. Stop if exact separation cannot be proven.

4. **Read complete guidance and compare actual history before composing** — at runtime fetch and read the **entire** https://go.dev/wiki/CommitMessage guide, not a summary, remembered version, or these excerpts. Also read its linked https://go.dev/doc/contribute#commit_messages section. If unavailable disclose the blocker; do not claim completion. Read recent **full subjects and bodies**, not one-line summaries, from the actual verified history head:

   ```bash
   (cd "$workspace_root" && jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\n"')
   ```

   Substitute the verified revision before execution. Compare several substantive examples and explicitly identify actual subject syntax (prefix/scope/case/tense/punctuation), body structure and explanatory depth, and issue-reference conventions. Repository instructions and demonstrated repository history determine syntax and win over Go-specific formatting; user override wins. Never impose conventional commits, package prefixes, fixed templates, or a fallback message syntax. With no history explain the limitation and use clear outcome-focused language without inventing a convention.

   Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.

   Verbatim source guidance, subordinate to actual repository syntax and not a mandatory template:

   > Commit messages, also known as CL (changelist) descriptions, should be formatted per https://go.dev/doc/contribute#commit_messages. For example,

   ```text
   net/http: handle foo when bar

   [longer description here in the body]

   Fixes #12345
   ```

   > Notably, for the subject (the first line of description):
   > - the name of the package affected by the change goes before the colon
   > - the part after the colon uses the verb tense + phrase that completes the blank in, “this change modifies Go to **___**”
   > - the verb after the colon is lowercase
   > - there is no trailing period
   > - it should be kept as short as possible (many git viewing tools prefer under ~72 characters, though Go isn’t super strict about this).

   > For the body (the rest of the description):
   > - the text should be wrapped to ~72 characters (to appease git viewing tools, mainly), unless you really need longer lines (e.g. for ASCII art, tables, or long links).
   > - the Fixes line goes after the body with a blank newline separating the two. (It is acceptable but not required to use a trailing period, such as Fixes #12345.).
   > - there is no Markdown in the commit message.
   > - similarly, we do not use Co-authored-by and Assisted-by lines. Don’t add them.

   Additional Go source guidance:

   > The CL description is a public document that explains to the future what has been done and why.

   > The first line of the change description is conventionally a short one-line summary of the change, prefixed by the primary affected package.

   > A rule of thumb is that it should be written so to complete the sentence "This change modifies Go to _____."

   > That means it does not start with a capital letter, is not a complete sentence, and actually summarizes the result of the change.

   > The rest of the description elaborates and should provide context for the change and explain what it does.

   > Write in complete sentences with correct punctuation, just like for your comments in Go.

   > Don't use HTML, Markdown, or any other markup language.

   > The text should be wrapped at around 72 columns.

   This is a **quoted Go source example, source guidance only, not a required repository message template**:

   ```text
   net/http: handle foo when bar

   [longer description here in the body]

   Fixes #12345
   ```

   Apply the underlying requirement to explain what changed and why while matching actual repository syntax. Name the outcome, not just edited files. Add a body when motivation, behavior, evidence, or trade-offs would otherwise be unclear. Reference issues accurately: claim a fix only when complete, and reference partial progress without falsely closing an issue. Do not add generated attribution, coauthor/assistant trailers, or sign-offs.

5. **Describe and finalize exact groups** — when a plan Implementation Unit ID is already in hand (conversation, caller, or files belonging to one unit), append that unit's U-ID in parentheses where compatible with repository conventions. Do not hunt for a plan; omit when spanning units, unclear, or absent. Write the full chosen description with the file-write tool to a uniquely owned message file under the workspace-local `.tmp/`, including retries/error artifacts; never use global temporary paths or an external directory. Verify that scratch is ignored and absent from selected changes. Use neutral placeholders rather than fixed message syntax:

   ```bash
   jj describe -r <verified-change-id> --message-file <absolute-workspace-root>/.tmp/<owned-message-file>
   ```

   Read back the full description and diff. If the finalized change is the working-copy change, create an empty child with `jj new <verified-finalized-commit>` only after verification. If splitting left unrelated work in `@`, preserve it in place rather than moving away from or discarding it. Create or move only the authorized task bookmark to the verified finalized commit (`jj bookmark set <task-bookmark> -r <verified-finalized-commit>` for an existing authorized task bookmark). Never push, reset, squash unrelated work, or automatically rewrite published history.

6. **Confirm** — inspect `jj status` and finalized revisions' full descriptions and exact file lists. Verify selected files no longer remain unfinalized. Report commit/change IDs, subjects, explicit files per group, task bookmark, and all excluded/unrelated remaining work. Intentionally retained work need not be clean; never call that workspace wholly clean. Stop if concurrent edits changed scope or verification disagrees with the requested groups.
