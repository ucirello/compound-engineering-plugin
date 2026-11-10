# Committing and pushing with JJ

## Runtime composition contract (every composition site)

You MUST read the full https://go.dev/wiki/CommitMessage guide at runtime before composing commit messages, not merely this excerpt or a remembered summary. Resolve the actual verified history head and read recent full subjects and bodies:

```sh
(cd "$workspace_root" && jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\\n"')
```

Set `workspace_root` to the verified absolute target workspace root. Substitute the verified revision, never a hardcoded default remote bookmark. Compare several messages for syntax, capitalization, prefixes, bodies and trailers. Actual repository conventions win over Go-specific syntax. If history or the full guide cannot be read, report missing evidence instead of inventing style.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.

Verbatim source guidance, subordinate to actual repository syntax and not a mandatory template:

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

Additional source guidance, not a repository template:

> the part after the colon uses the verb tense + phrase that completes the blank in, “this change modifies Go to _____”
>
> the verb after the colon is lowercase
>
> there is no trailing period
>
> it should be kept as short as possible (many git viewing tools prefer under ~72 characters, though Go isn’t super strict about this).
>
> the text should be wrapped to ~72 characters (to appease git viewing tools, mainly), unless you really need longer lines (e.g. for ASCII art, tables, or long links).
>
> there is **no** Markdown in the commit message.
>
> we **do not** use `Signed-off-by` lines. Don’t add them. Our Gerrit server & GitHub bots enforce CLA compliance instead.
>
> similarly, we **do not** use `Co-authored-by` and `Assisted-by` lines. Don’t add them.
>
> The CL description is a public document that explains to the future what has been done and why.

Source example only, not required repository syntax:

```text
net/http: handle foo when bar

[longer description here in the body]

Fixes #12345
```

Explain what changed and why, use accurate issue references, and do not invent signing or attribution trailers. Preserve genuine human authors and required trailers according to repository policy; Go's own trailer rules do not override that policy. Do not add model, harness, or bot credit.

## Mechanics

Stack construction follows `stack-submit.md`. Otherwise inspect the complete working change and group distinct concerns into at most 2–3 whole-file commits. Honor `exclude:<paths>` and leave unrelated work untouched. JJ snapshots are not staging: inspect `jj status`, `jj diff`, and `jj file list`; track only intended new paths with `jj file track <paths>` when necessary. Never sweep up secrets, artifacts, or excluded files. Stop on conflicts.

For a working change containing exactly the intended group use `jj describe -m '<repository-style subject and explanatory body>'`, then `jj new`. For mixed whole-file groups use `jj commit -m '<repository-style subject and explanatory body>' <explicit-paths>` and verify committed paths and remaining changes. Preserve others' author identities and genuine human co-author trailers; never guess an email. Never rewrite published history without permission. Append an already-known unit ID only when the commit belongs to that single unit; do not hunt for a plan.

Apply the Project publishing gate to the exact outgoing state. Reverify feature bookmark, target, remote and permission; move only the authorized bookmark with `jj bookmark set <feature> -r <verified-commit>`, then `jj git push --remote <verified-remote> --bookmark <feature>` (use installed JJ's documented new-bookmark permission if needed). Never push empty `@` above the intended head. Verify the remote bookmark. Already-published clean work is a no-op.
