# Committing the refresh

Skip if no files changed. Check the current bookmark and whether the workspace has unrelated changes or conflicts. Include **only** the files this refresh modified, including a `CODING_STANDARDS.md` it changed; use path-scoped `jj commit` from the absolute workspace root, preserving unrelated work. Describe the refresh's updates, consolidations and deletions. Its body, and the pull request body when there is one, lists each worth-based cut or Delete and each standards change with its quoted evidence, because reviewers and later readers rely on that trail.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.

Before composing, read the full guide at runtime and inspect several recent complete subjects AND bodies: `(cd "$workspace_root" && jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\n"')`. Resolve that history head from this task's actual bookmark/revision; never hardcode a default remote or replace an exact reviewed range with this style sample. Compare prefixes/package names, casing, tense, subject/body separation, wrapping and issue placement. Repository/user syntax always wins; apply Go only for compatible clarity and structure. With no history, use explicit project/user instructions plus Go guidance without inventing precedent. A describe example, when appropriate for the owned change, is `(cd "$workspace_root" && jj describe -m "<message composed from the standards above>")`; never describe a mixed unrelated change.

### Go SOURCE GUIDANCE — subordinate to the observed repository pattern

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

Non-interactive defaults: on the verified repo default bookmark → create a bookmark named for what was refreshed (e.g., `docs/refresh-auth-learnings`), commit only owned paths, attempt a PR (if PR creation fails, report the bookmark name); on a feature bookmark → separate change on that bookmark; JJ failures → put the recommended commands in the report and continue. Verify remote/bookmark/push authority before publishing and preserve recovery references. Repository-scoped `gh` uses `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh ...)`; no direct Git. Routine already-authorized publishing needs no redundant approval; preserve genuine tool gates, final merge and scope-expansion decisions.

Interactive: ask (per Blocking questions), with the recommended option first. On the default bookmark: bookmark+commit+PR (recommended; specific bookmark name) / commit directly to the current bookmark / don't commit. On a clean feature bookmark: commit to it (recommended) / separate bookmark / don't commit. On a dirty feature bookmark: path-scoped commit of only refresh changes / don't commit.
