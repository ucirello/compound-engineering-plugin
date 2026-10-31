# Committing the refresh

### Quoted Go source guidance (not a mandatory repository template)

The following verbatim excerpts are from https://go.dev/wiki/CommitMessage. Repository-local syntax ALWAYS wins; the Go illustration does not prescribe message syntax here. Keep the runtime full-guide/history comparison below.

> Commit messages, also known as CL (changelist) descriptions, should be formatted per https://go.dev/doc/contribute#commit_messages. For example,
>
> ```text
> net/http: handle foo when bar
>
> [longer description here in the body]
>
> Fixes #12345
> ```
>
> Notably, for the subject (the first line of description):
>
> - the name of the package affected by the change goes before the colon
> - the part after the colon uses the verb tense + phrase that completes the blank in, “this change modifies Go to **___**”
> - the verb after the colon is lowercase
> - there is no trailing period
> - it should be kept as short as possible (many git viewing tools prefer under ~72 characters, though Go isn’t super strict about this).
>
> For the body (the rest of the description):
>
> - the text should be wrapped to ~72 characters (to appease git viewing tools, mainly), unless you really need longer lines (e.g. for ASCII art, tables, or long links).
> - the Fixes line goes after the body with a blank newline separating the two. (It is acceptable but not required to use a trailing period, such as Fixes #12345.).
> - there is no Markdown in the commit message.
> - we **do not** use `Signed-off-by` lines. Don’t add them. Our Gerrit server & GitHub bots enforce CLA compliance instead.
> - similarly, we do not use Co-authored-by and Assisted-by lines. Don’t add them.
> - when referencing CLs, prefer saying “CL nnn” or using a go.dev/cl/nnn shortlink over a direct Gerrit URL or git hash, since that’s more future-proof.
> - when moving code between repos, include the CL, repository name, and git hash that it was moved from/to, so it is easier to trace history/blame.

Skip if no files changed. Resolve the absolute target JJ workspace root and inspect `jj status`, conflicts, bookmarks, and unrelated changes there. Run every JJ command with that absolute root as cwd, for example `(cd "$workspace_root" && jj status)`. Preserve unrelated work, including overlapping edits; if ownership cannot be separated safely, report a blocker rather than including it. Use `jj split` with the verified refresh paths (interactive selection for mixed files) to isolate only the refresh changes; JJ has no staging area.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.

Read the full linked guide before composing. Verify the intended history head for this task, then inspect several recent subjects AND bodies with `(cd "$workspace_root" && jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\n"')`. Compare package/prefix usage, casing, tense, subject/body separation, wrapping, and issue references. Repository-local syntax always wins; absent history, follow explicit instructions and compatible Go guidance without inventing precedent. Summarize the actual refresh outcomes without imposing a fixed message format. Do not put Markdown, Co-authored-by, or Assisted-by trailers in the message. Describe the isolated revision with `(cd "$workspace_root" && jj describe -r <verified-refresh-revision> -m "<message composed from the standards above>")`.

Non-interactive defaults: at the verified default bookmark → create a task-named bookmark for the refresh; on a verified feature bookmark → advance that bookmark to the isolated refresh revision. Preserve all existing bookmark identities. Attempt the authorized push using `jj git push --bookmark <verified-bookmark>` from the absolute target root and attempt a PR. Run repository-scoped `gh` only there with `GIT_DIR=$(jj git root)` in its environment. If publication fails, report the bookmark and exact failed step, retain local changes, and continue the report. No Git executable fallback.

Interactive: ask through the blocking-question mechanism, recommended option first. At the default bookmark: separate bookmark + described change + PR / describe directly on the current bookmark / don't commit. At a clean feature bookmark: describe and advance it / separate bookmark / don't commit. With unrelated work: isolate only refresh changes / don't commit. A failure leaves recovery state intact and recommended commands in the report.
