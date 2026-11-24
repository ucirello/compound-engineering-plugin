# Committing the refresh

Skip if no files changed. From the absolute target workspace root, verify the active bookmark at `@` or its parent, the remote default (`trunk()` checked against the intended remote), and the current diff. Inventory only refresh-owned paths, including both ends of renames and a `CODING_STANDARDS.md` this refresh changed. Preserve unrelated changes; if refresh edits share a path with unrelated work, use hunk selection (`jj commit --interactive` with the relevant filesets) only if the separation can be verified, otherwise leave it uncommitted and report the blocker.

**Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.** Before composing, read the full guide and use `jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\n"'` from the absolute workspace root. Resolve that history head from this refresh's verified lineage; compare several full subjects and bodies for prefixes, casing, tense, subject/body separation, wrapping, and issue references. Repository-local syntax always wins; apply compatible Go guidance to clarity and structure. If there is no history, use project/user instructions and the Go guidance without inventing precedent. Summarize the refresh; its body and any PR body list each worth-based cut or Delete and each standards change with quoted evidence.

Source guidance from https://go.dev/wiki/CommitMessage (illustrative, not a repository template):

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

**Non-interactive defaults:** on the remote's verified default bookmark, use a separate bookmark named for the refresh (e.g., `docs/refresh-auth-learnings`), commit, and attempt a PR. On a feature bookmark, make a separate commit and advance only that verified local bookmark; do not push it as part of this route. If JJ fails or the active bookmark is ambiguous, put the recommended recovery commands and blocker in the report and continue without guessing.

**Interactive:** ask per Blocking questions. On the default bookmark: separate bookmark + commit + PR (recommended; name the bookmark) / commit directly to the current bookmark / don't commit. On a clean feature bookmark: commit to it (recommended) / separate bookmark / don't commit. On a dirty feature bookmark: commit only refresh-owned changes / don't commit.

Before committing capture the refresh change ID of `@`. Use `jj commit -m "<message composed from the standards above>" -- <verified-refresh-filesets>` and verify the committed diff for that change ID and the remaining working-copy diff. For a separate bookmark, use `jj bookmark create <name> -r <verified-refresh-change>`; otherwise move the verified local bookmark forward to that exact revision (`jj bookmark move <bookmark> --to <verified-refresh-change>`), never force. For the PR route, verify the intended remote, base and named head, then `jj git push --remote <remote> --bookmark <name>`. From the absolute workspace root after confirming `jj git root` succeeds, use `GIT_DIR=$(jj git root) gh pr create --base <base> --head <name>` with the evidence-bearing title/body. If PR creation fails, report the bookmark and whether it was pushed. Do not switch or discard unrelated work to recover.
