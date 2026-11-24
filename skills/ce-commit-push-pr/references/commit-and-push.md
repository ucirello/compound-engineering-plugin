# Committing and pushing

If `references/stack-submit.md` built the stack layers before this step, skip the ordinary single-bookmark commit and push. Step 5 publishes the stack.

If the working change is based on the default bookmark, read `references/branch-creation.md` before continuing. For an existing feature, verify that the first owned change starts from the intended feature lineage, not an unrelated bookmark or another workspace's change.

## Compose each change description

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.

Before composing, read the full Go guide and compare several recent commit **subjects and bodies**. Resolve a verified history head from the applicable project lineage and task, such as the target base or the feature's verified published parent. Read it from the absolute JJ workspace root:

```bash
(cd "$workspace_root" && jj log --no-graph -r "::$verified_history_head" -n 10 -T 'description ++ "\n"')
```

Use the project instructions and the history to determine prefixes or package names, casing, verb tense, subject/body separation, wrapping, and issue-reference placement. Repository-local syntax always wins where it differs from Go's. Apply compatible guidance to make the subject clear and concise, the body explain why the change was needed, and issue references unambiguous. If there is no history, use explicit project/user instructions and compatible Go guidance; do not invent precedent. This sample decides style, not the content range of the commit or PR.

**Go source guidance, not a mandatory repository template:**

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

When a plan Implementation Unit ID is already in hand and the group belongs to that unit, include its ID using the observed conventions. Do not hunt for a plan; omit the ID when the group spans units or its unit is unclear.

Add changes on top of other people's commits; never rewrite theirs in a way that drops their author or credit. If a new change carries human work that will not otherwise land under its contributor's name, retain that credit using the repository's convention. Copy confirmed identities exactly from the source commit or patch; when no email is recorded, credit the person by name rather than guessing one. Do not copy or add model or harness attribution in the new description.

## Commit and publish only owned work

Scan changed files for naturally distinct concerns. Use whole-file groups (at most two or three), or one change when there is no clear split. Honor `exclude:<paths>`; leave those files outside every commit and report them. JJ may snapshot other work into `@`, so verify the exact file diff before committing and check the resulting commit after each group. Include both source and destination for an owned rename. If a file mixes work you may and may not publish, stop instead of capturing the whole file. Commit only an owned, unpublished working change. If `@` itself is already a completed change (including a published change), use its verified tip as the head candidate and skip the commit rather than rewriting it.

```bash
(cd "$workspace_root" && jj commit -m "<message composed from the standards above>" -- 'file:"path/to/owned-file"')
```

Use an exact `file:` fileset for each selected repo-relative file. Path-scoped `jj commit` leaves the selected files in the described change and carries the remaining changes into its new working-copy child. Don't run a bare commit; don't point the bookmark at the child holding the remainder. Record the final intended commit ID, verify its full outgoing range, and create a new bookmark at that ID or use `jj bookmark move "exact:$head_bookmark" --to <commit-id>` for a verified forward move of the intended feature bookmark only. Do not move the default, another owner's bookmark, or rewrite published history without explicit authorization.

Apply the **Project publishing gate** to the exact commit state. Re-verify the bookmark and its remote, outgoing range and PR state immediately before publishing; `jj git push` can update a non-fast-forward bookmark under a lease, so don't treat the lease as authorization to rewrite. Push only the named feature bookmark to its verified head remote:

```bash
(cd "$workspace_root" && jj git push --remote "exact:$head_remote" --bookmark "exact:$head_bookmark")
```

If the intended commits are already pushed, publishing is a no-op. Verify the pushed head against the remote and pass that identity to Step 5.
