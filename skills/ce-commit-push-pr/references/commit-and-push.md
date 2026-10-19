# Compose, commit, and push with JJ

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Before composing, read the full Go guide and project instructions, then examine several recent subjects AND bodies using `(cd "$workspace_root" && GIT_DIR=$(jj git root) git log -10 --format=%B)`. This is a read-only Git-backend exception, not permission for Git mutations. Compare prefixes/package names, casing, tense, subject/body separation, wrapping and issue-reference placement. Repository-local syntax ALWAYS wins; apply compatible Go guidance to clarity and structure within that pattern. With no history, use explicit project/user instructions and Go guidance without inventing precedent.

The following is verbatim Go source guidance, illustrative rather than a mandatory repository template:

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

## Commit only intended files

Read `context.md` and `branch-creation.md` as applicable. Inspect `jj status`, `jj diff`, conflicts, and the complete intended file group, including newly tracked files. JJ has no Git staging area. Honor `exclude:<paths>` and preserve unrelated work exactly. Use explicit repo-relative paths such as `src/example.py`, never workspace-prefixed paths. Explicitly track only intended untracked files with `jj file track <paths>` when needed; never force ignored content into tracking.

From the absolute workspace root, commit a working-copy group with `jj commit -m "<message composed from the standards above>" <explicit-paths>`. Inspect the resulting revision and remaining diff to prove excluded/unrelated work remains outside it. Never include all working-copy files by default. If a plan Implementation Unit ID is already in hand and unambiguous, include that identity in the dynamically composed message using repository-compatible syntax; do not hunt for plans or impose a suffix format.

Move only the intended feature bookmark to the verified committed revision with `jj bookmark set <bookmark> -r <revision>`, preserving other references. Apply the Project publishing gate to this exact state. Re-verify repository, remote, bookmark and head authority, then `(cd "$workspace_root" && jj git push --remote <remote> --bookmark <bookmark>)`. Establish tracking/new-bookmark publication only when authorized and required by JJ's reported state. Never push all bookmarks. Verify the remote tip; clean, already-pushed work is a no-op.

Guidance: https://docs.jj-vcs.dev/latest/git-experts/ ; https://docs.jj-vcs.dev/latest/git-command-table/ ; https://docs.jj-vcs.dev/latest/cli-reference/ .
