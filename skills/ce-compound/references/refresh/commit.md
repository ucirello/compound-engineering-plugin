# Committing the refresh

Skip if no files changed. Check bookmarks, conflicts and unrelated tracked/ignored/untracked work from the absolute target workspace root. Commit **only** the files this refresh modified, including a changed `CODING_STANDARDS.md`, using JJ's path-scoped commit operation; never sweep unrelated work into the change. Describe the refresh's outcomes. Its body, and the pull request body when there is one, lists each worth-based cut or Delete and each standards change with its quoted evidence.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.

Before composing, read the full Go guide and compare several recent subjects AND bodies from the task's verified history head: `(cd "$workspace_root" && jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\n"')`. Establish actual prefixes/package names, casing, verb tense, subject/body separation, wrapping and issue placement. Repository-local instructions and observed syntax always win; apply compatible Go guidance for clarity and structure. Without history use explicit project/user instructions and Go guidance without inventing precedent. No fixed message template is prescribed.

The following is verbatim Go source guidance, not a mandatory repository template:

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

Non-interactive defaults: on the verified remote default bookmark → create a task-named bookmark, commit, push that exact bookmark with `jj git push --bookmark <verified-bookmark>`, and attempt a PR; on a feature bookmark → separate commit on that bookmark. JJ or PR failures → put recommended commands and exact bookmark in the report and continue. Run all JJ commands with cwd set to the absolute workspace root. Run repository-scoped `gh` from that root with `GIT_DIR=$(jj git root)`.

Interactive: ask (per Blocking questions), with the recommended option first. On the default branch: branch+commit+PR (recommended; specific branch name) / commit directly to the current branch / don't commit. On a clean feature branch: commit to it (recommended) / separate branch / don't commit. On a dirty feature branch: selective-stage and commit only refresh changes / don't commit.
