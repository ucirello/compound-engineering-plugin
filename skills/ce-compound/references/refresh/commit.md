# Committing the refresh

Skip if no files changed. Check current bookmarks and unrelated working-copy changes. Include **only** paths this refresh modified, including `CODING_STANDARDS.md` when changed; use `jj split <owned-paths>` when necessary to isolate unrelated work without discarding it. Compose a descriptive message summarizing the refresh. Its body, and any PR body, lists each worth-based cut or Delete and each standards change with quoted evidence.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.

Before composing, read the full Go guide and resolve the actual relevant history head for this task. From the target workspace's absolute root compare several full subjects AND bodies with `(cd "$workspace_root" && jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\n"')`. Compare prefixes/package names, casing, tense, subject/body separation, wrapping and issue-reference placement. Repository-local instructions and observed syntax always win; apply compatible Go clarity and structure within that pattern. Without history use explicit project/user instructions and Go guidance, not invented precedent. Describe only the isolated refresh change with `(cd "$workspace_root" && jj describe -m "<message composed from the standards above>")`.

Verbatim Go source guidance below is illustrative, not a mandatory repository template:

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

Non-interactive defaults: on the verified default bookmark → create a bookmark named for what was refreshed (e.g., `docs/refresh-auth-learnings`), describe the isolated change, push with `jj git push`, attempt a PR (if creation fails report the bookmark); on a feature bookmark → separate change on that bookmark. JJ failures go in the report with recommended commands. Run JJ from the absolute workspace root. Repository-scoped `gh` requires `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh ...)`.

Interactive: ask (per Blocking questions), recommended first. On the default bookmark: bookmark+change+PR / describe directly on the current bookmark / don't commit. On a clean feature bookmark: commit to it / separate bookmark / don't commit. With unrelated changes: isolate only refresh paths with `jj split` / don't commit. Never discard unrelated work.
