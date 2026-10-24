# Committing and pushing

If stack construction already committed layers, skip ordinary single-bookmark committing; Step 5 publishes the stack. For default-bookmark work first follow `branch-creation.md`.

## Required message composition standard

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.

Before composing, read the full Go guide and examine several recent subjects AND bodies from the target workspace's absolute root:

```bash
(cd "$workspace_root" && jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\n"')
```

Resolve that head from the actual task and repository; this style sample never replaces the exact reviewed base/head range. Compare prefixes/package names, casing, tense, subject/body separation, wrapping, and issue placement across several messages. Repository-local instructions and observed syntax ALWAYS win over conflicting Go guidance. Apply compatible guidance for clarity and structure within that syntax; do not impose a prefix/type/scope/template. With no history, use explicit project/user instructions and Go guidance without inventing precedent.

Verbatim source guidance (the Go example is illustrative, not a mandatory repository template):

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

## Owned-path mechanics

Scan files for distinct concerns; use whole-file groups, 2–3 commits maximum when clearly separate, otherwise one. Honor `exclude:<paths>` and report excluded files left untouched. JJ snapshots automatically: inspect `jj status`, `jj diff`, and new-file tracking before committing; never broadly track everything. Track only intended untracked paths with `jj file track <owned-paths>` if needed. Commit only named owned paths:

```bash
(cd "$workspace_root" && jj commit -m "<message composed from the standards above>" -- <owned-paths>)
```

Unselected changes remain in the working copy. If describing an already isolated owned change, use `jj describe -r <verified-owned-change> -m "<message composed from the standards above>"`. Verify the committed diff contains no unrelated or excluded work. When a single plan Implementation Unit ID is already in hand, include that U-ID as semantic content using the repository's runtime syntax; do not hunt for a plan or impose a suffix template.

Apply the **Project publishing gate** to the exact final commit. Reverify intended feature bookmark, remote, head repository, exact target and push authority immediately before publishing. Move only the intended feature bookmark to the verified committed tip (not an empty working-copy child), then use `jj git push --remote <verified-remote> --bookmark <feature-bookmark>`. Do not move the default bookmark. A clean workspace with all commits already pushed is a no-op. Published-history rewriting requires its own explicit authorization.
