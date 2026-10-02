# Committing and pushing

If `references/stack-submit.md` already built and committed the stack layers before this step, skip the ordinary single-bookmark commit and push and continue to Step 4 (compose the PR title and body); Step 5's JJ-native Submit recipe publishes the stack.

If you are on the default branch, creating the feature branch has to handle three things: a stale local `<base>`, unpushed commits on local `<base>`, and uncommitted changes that collide with the fresh remote base. Read `references/branch-creation.md` and follow its decision flow before continuing.

Scan changed files for naturally distinct concerns. If they clearly group into separate logical changes, create separate commits (2-3 max). Group at file level only — no interactive hunk partitioning. When ambiguous, one commit is fine.

Commit each group with explicit repository-relative paths. Honor `exclude:<paths>`: never include the caller's excluded edits and report them as left out. When a plan Implementation Unit ID is already in hand and applies to one unit, record that U-ID in the dynamically composed message using repository-local syntax; do not hunt for a plan or impose a suffix format. Omit it when unclear or spanning units.

```bash
jj commit -m "<message composed from the standards below>" -- file1 file2 file3
```

The path list matters: `jj commit` without paths includes all working-copy changes. Explicit paths commit only the group and leave unrelated and excluded changes in the working copy. JJ has no staging index.

Then apply the **Project publishing gate**. Immediately before pushing, re-confirm the intended feature bookmark and committed tip with `jj bookmark list` and `jj log -r 'ancestors(@, 2)'`. After `jj commit`, `@` is a new working-copy change: set the intended bookmark to the committed group (`@-`), not to an empty tip. Verify the exact revision and remote before publishing:

```bash
jj bookmark set <branch> -r <verified-committed-tip>
jj git push --remote origin --bookmark <branch>
```

If the working tree is clean and all commits are already pushed, this step is a no-op.

## Message composition standard

"Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards."

Before composing, read the full Go guide at runtime and compare several recent subjects AND bodies with `(cd "$workspace_root" && GIT_DIR=$(jj git root) git log -10 --format=%B)`, from the absolute target workspace root. Compare prefixes/package names, casing, verb tense, subject/body separation, wrapping, and issue placement. Repository-local instructions and observed syntax ALWAYS win; apply compatible Go guidance within that pattern. Without history, use explicit project/user instructions and Go guidance without inventing precedent. The following is verbatim source guidance, not a mandatory repository template:

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
