# Committing and pushing

## Message-composition standards

"Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards."

Before composing any message, read the full https://go.dev/wiki/CommitMessage at runtime. Resolve the actual task's verified history head, then from the target workspace's absolute root examine several recent full subjects AND bodies, for example `(cd "$workspace_root" && jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\n"')`. Compare prefixes/package names, casing, tense, subject/body separation, wrapping and issue placement. Repository-local syntax established by project instructions and history ALWAYS wins. Apply compatible Go guidance to clarity, quality and structure, not to replacing that syntax. Without history, use explicit project/user instructions and compatible Go guidance; do not invent precedent. Keep required scope, hypothesis, unit and issue content within the dynamically composed message.

Verbatim Go source guidance (the example is illustrative, not a mandatory repository template):

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

Preserve the human-authorship requirements below when repository-local policy requires them; never add model or harness attribution. All composition sites, including explainer and stack changes, must load these standards before composing. A neutral description operation is `jj describe -m "<message composed from the standards above>"`, from the target absolute root and only for a verified owned change.

If `references/stack-submit.md` already built and committed the stack layers before this step, skip the ordinary single-branch commit and push and continue to Step 4 (compose the PR title and body); Step 5 publishes the exact layer bookmarks with JJ and links their hosted topology.

If you are on the default branch, creating the feature branch has to handle three things: a stale local `<base>`, unpushed commits on local `<base>`, and uncommitted changes that collide with the fresh remote base. Read `references/branch-creation.md` and follow its decision flow before continuing.

Inspect the complete change set and group naturally distinct concerns at whole-file level (2–3 changes maximum). Commit only explicitly owned paths with `jj commit <owned-paths> -m "<message composed from the standards above>"`. Honor `exclude:<paths>`: leave excluded and unrelated changes untouched and report them. Include an already-known single Implementation Unit ID as semantic context, without prescribing message syntax; do not hunt for a plan.

Add your commits on top of other people's commits on this branch; never rewrite theirs in a way that drops their author or existing trailers, such as squashing them into yours. When a commit you create carries someone else's work that will not otherwise land under their name (ported from their branch or PR, or applied from their patch), preserve human credit using the repository-local attribution convention established at runtime. Add coauthor trailers only when that convention requires them; otherwise include the credit in the compatible message body. Copy human identities exactly from the source commits or patch, including people credited by existing trailers. Never guess an email: when none is recorded, credit the name only. This semantic credit requirement does not impose fixed message syntax or model/harness attribution.

Apply the **Project publishing gate**. Re-verify the head repository, intended feature bookmark, remote, exact committed head and push authority. Move only the owned feature bookmark with `jj bookmark set <feature> -r <verified-committed-head>` and push it using `jj git push --remote <verified-remote> --bookmark <feature>` (`--allow-new` only for an authorized new remote bookmark). An empty `@` above that head is normal; never push an unrelated bookmark or guess the commit.

If the working tree is clean and all commits are already pushed, this step is a no-op.
