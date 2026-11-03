# Committing the refresh

Skip if nothing changed. Resolve the current bookmark and actual history head, inspect unrelated and conflicted work, and isolate only refresh paths (including changed standards) into a dedicated revision with JJ explicit-file selection; there is no staging area. Preserve all unrelated work. Verify the selected diff before publishing. The description and PR body list every worth-based cut/Delete and standards change with quoted evidence.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.

**Illustrative Go source excerpts — NOT a mandatory repository template.** The following verbatim source example and guidance illustrate Go conventions; repository instructions and observed history take precedence over incompatible syntax.

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

Read the FULL Go guide before composing. Resolve `<verified-history-head>` from this task/repository, never assume main. Compare several recent full subjects AND bodies using `(cd "$workspace_root" && jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\n"')`. Infer prefixes/package/case/tense/body separation/wrapping/issues. Repository instructions/history syntax wins; use compatible Go quality guidance only. Without history use project/user instructions plus Go guidance, never invent precedent. Describe with `(cd "$workspace_root" && jj describe -m "<message composed from the standards above>")`. No fixed example syntax elsewhere prescribes the message.

Non-interactive: on the verified remote default bookmark, create a task-named bookmark for the refresh revision and attempt a PR; on a feature bookmark, use a separate refresh revision. On failure retain work, report the exact failed operation and recommended commands, and continue. Never run the Git executable or substitute another ref. All JJ commands execute from the absolute target workspace cwd. Publish using JJ transport and repository-scoped `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh <arguments>)`.

Interactive: ask once with the recommended option first: task bookmark+revision+PR on default, dedicated revision on feature, or leave uncommitted. With unrelated changes, offer explicit-path isolation or leave uncommitted; never capture unrelated content. Existing authorization needs no repeated approval.
