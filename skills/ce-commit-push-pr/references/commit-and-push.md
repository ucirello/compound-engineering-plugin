# Committing and pushing

If stack mode already committed its layers, continue to composition; Step 5 owns submission. For default-bookmark work, first follow `references/branch-creation.md`.

Run JJ from the target workspace's absolute root. Scan changed files for naturally distinct concerns and group whole files into at most 2–3 logical changes; ambiguous work can be one change. There is no Git staging index. Inspect `jj status` and `jj diff`, including newly tracked files, and honor `exclude:<paths>`: they and unrelated user work stay outside every published revision and are reported as excluded. Use path-limited `jj commit -m "<message composed from the standards below>" -- <owned-files>` to leave other work in the working-copy change. Inspect the resulting revisions to prove their scope; never commit all paths blindly. For untracked files, use explicit `jj file track <owned-files>` only as needed, never force ignored artifacts into history.

## Runtime message composition standards

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Before composing each message, read the full Go guide and inspect several recent subjects AND bodies with `(cd "$workspace_root" && GIT_DIR=$(jj git root) git log -10 --format=%B)`. This Git command is read-only access to JJ's backend, not a Git mutation. Compare prefixes/package names, casing, verb tense, subject/body separation, wrapping, and issue-reference placement. Repository-local syntax from project instructions and history ALWAYS wins over differing Go guidance; apply compatible guidance to clarity, quality, and structure. With no history, follow explicit project/user instructions and compatible Go guidance without inventing precedent. Do not impose a fixed prefix, type, scope, or message template.

The following verbatim Go source guidance is illustrative, not a mandatory repository template:

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

Describe each group's actual change. When a plan Implementation Unit ID is already in hand and uniquely identifies that group's unit, include its U-ID using syntax compatible with the runtime repository pattern. Do not hunt for a plan; omit unclear or multi-unit IDs.

Apply the **Project publishing gate**. Re-verify the feature bookmark, head repository, push remote and exact committed revision immediately before publishing. Move only the verified owned feature bookmark to that revision with `jj bookmark set <feature> -r <verified-commit>`, then `jj git push --remote <verified-remote> --bookmark <feature>` (use `--allow-new` only for an authorized new remote bookmark). Never push the empty `@` tip or unrelated bookmarks by accident. Already-pushed clean work is a no-op. Unknown push authority, conflicts or uncertain targets block instead of guessing.

JJ guidance: https://docs.jj-vcs.dev/latest/git-command-table/ and https://docs.jj-vcs.dev/latest/cli-reference/ .
