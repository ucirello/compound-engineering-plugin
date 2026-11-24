# Compose the fix change description

Read this before composing a message in either non-interactive mode. Describe the verified fix, why it was needed, and any relevant issue of record in the location and syntax the tracker and repository require. Do not invent an issue or claim a fix was verified when it was not.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.

Read the full Go guide and compare several recent complete descriptions in the target repository before composing. Resolve `history_head` from the actual feature/PR history applicable to this fix, not a hardcoded default. From the verified absolute workspace root:

```sh
(cd "$workspace_root" && jj log --no-graph -r "::$history_head" -n 10 -T 'description ++ "\n"')
```

Compare prefixes or package names, casing, verb tense, subject/body separation, wrapping, and issue-reference placement. Repository instructions and the observed repository syntax win where they differ from the source guidance. Apply compatible Go guidance for clarity, brevity, and separating subject, rationale, and issue links. If there is no history, use explicit user/project instructions and compatible Go guidance without claiming a precedent.

Verbatim excerpts from the Go wiki; the Go example is source guidance, not a mandatory repository template:

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

From the same workspace root, commit the verified fix-owned file set only using `jj commit -m "<message composed from the standards above>" -- <fix-owned-filesets>`. Use `file:"<workspace-relative-path>"` filesets with paths quoted for JJ and the shell, not broad patterns. Verify the resulting commit has exactly the intended changes and no conflicts, and that unrelated work remains in the working copy. Record the fix commit ID, not the new `@`. If needed, advance only the authorized feature/PR bookmark from its verified old head to that exact fix commit with `jj bookmark move --from "$verified_old_head" --to "$fix_commit" -- "$exact_bookmark_pattern"`; confirm the resulting target. Stop if this would publish unrelated changes, require a backward move, or clobber a concurrent change. Push only if the calling mode authorizes and verifies it.
