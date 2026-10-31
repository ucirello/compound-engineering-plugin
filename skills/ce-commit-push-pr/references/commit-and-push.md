# Committing and pushing

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.

Read the full guide before composing. From the absolute target workspace root compare SEVERAL recent subjects AND bodies using `(cd "$workspace_root" && jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\n"')`, resolving the history head from the actual task. Repository-local syntax ALWAYS wins: examine prefixes/packages, casing, tense, subject/body separation, wrapping and issue references. Apply compatible Go guidance within that pattern. Without history use explicit project/user instructions and compatible Go guidance, never invented precedent. No Markdown, Co-authored-by or Assisted-by in resulting messages; compatible local rules win. Every layer and explainer commit uses these same runtime standards.

## Verbatim Go source excerpts — illustration subordinate to repository patterns

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
> - we **do not** use `Signed-off-by` lines. Don’t add them. Our Gerrit server & GitHub bots enforce CLA compliance instead.
> - similarly, we do not use Co-authored-by and Assisted-by lines. Don’t add them.
> - when referencing CLs, prefer saying “CL nnn” or using a go.dev/cl/nnn shortlink over a direct Gerrit URL or git hash, since that’s more future-proof.
> - when moving code between repos, include the CL, repository name, and git hash that it was moved from/to, so it is easier to trace history/blame.

If `references/stack-submit.md` already built the stack layers, skip ordinary single-bookmark commits; Step 5 publishes the stack.

If you are on the default branch, creating the feature branch has to handle three things: a stale local `<base>`, unpushed commits on local `<base>`, and uncommitted changes that collide with the fresh remote base. Read `references/branch-creation.md` and follow its decision flow before continuing.

Scan changed files for naturally distinct concerns. If they clearly group into separate logical changes, create separate commits (2-3 max). Group at file level only, not interactive hunk partitioning. When ambiguous, one commit is fine.

Commit each owned path group only. JJ snapshots tracked work automatically; inspect status, diff and file list, and explicitly `jj file track <intended-new-paths>` from the absolute workspace root. Honor `exclude:<paths>`: leave and report excluded and unrelated work. When a plan Implementation Unit ID is already in hand, include its semantic identity in repository-compatible message syntax. Do not hunt for a plan; omit when unclear or spanning units.

Add your commits on top of other people's work; do not rewrite theirs or drop source authorship. Preserve human source credit in compatible plain prose, without inventing identities or adding prohibited trailers.

```bash
(cd "$workspace_root" && jj commit file1 file2 file3 -m "<message composed from the standards above>")
```

The explicit path list matters: commit only the owned group and leave unrelated/excluded changes in the working copy. Verify the resulting committed diff before moving the feature bookmark to that exact committed head. For authorized description edits use `(cd "$workspace_root" && jj describe -r <verified-owned-change> -m "<message composed from the standards above>")`.

Then apply the **Project publishing gate** to the exact committed state. Immediately re-verify repository, feature bookmark, remote, commit and push authority; move only that bookmark to the intended committed head, never an unrelated or nonempty working-copy change:

```bash
(cd "$workspace_root" && jj git push --remote <verified-remote> --bookmark <feature-bookmark>)
```

Add `--allow-new` only for an authorized new remote bookmark. Ambiguous targets, conflicts or unknown push authority block publishing. Already-pushed clean state is a no-op.
