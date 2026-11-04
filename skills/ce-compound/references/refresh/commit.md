# Committing the refresh

Skip if no files changed. From the absolute target workspace root, inspect `jj status`, `jj diff`, bookmarks and recent history. Include **only** files this refresh modified, including its `CODING_STANDARDS.md` edits; never absorb unrelated edits. Use `jj commit <owned-paths> -m "<message composed from the standards below>"` for a separate owned-path change, preserving the remaining working-copy changes. Its description and any PR body list each worth-based cut or Delete and standards change with quoted evidence.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.

Before composition read the full Go guide and compare several recent subjects AND bodies from the task's verified history head, from the absolute workspace root: `jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\n"'`. Establish actual prefixes/package names, casing, tense, subject/body separation, wrapping, and issue placement. Repository-local instructions and observed syntax always win; apply compatible Go clarity/structure guidance without imposing its example syntax. Without history use explicit project/user instructions and Go guidance, not an invented precedent.

Go source guidance (illustration, not a mandatory repository template):

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

Non-interactive defaults: on the verified default bookmark → create a refresh-named bookmark, commit owned paths, move that bookmark to the refresh commit, push it with `jj git push --bookmark <verified-bookmark>` when authorized, and attempt a PR using `GIT_DIR=$(jj git root) gh pr create` with verified explicit base/head (if creation fails, report the bookmark); on a feature bookmark → separate owned-path commit and advance that bookmark; JJ failures → report recommended commands and continue. Do not guess a default or alter unrelated bookmarks.

Interactive: ask (per Blocking questions), recommended option first. On the default bookmark: bookmark+commit+PR / commit on the current bookmark / don't commit. On a clean feature bookmark: commit to it / separate bookmark / don't commit. With unrelated changes: commit only refresh-owned paths / don't commit. Routine actions already authorized by the user or active workflow need no repeated approval; genuine scope expansion, unknown push authority, conflicts, or ambiguous targets retain the safe decision path.
