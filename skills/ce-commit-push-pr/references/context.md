# Repository context, bookmarks, and PR state

Run every probe from the target workspace's absolute root. Interpret each exit status; do not suppress failures. Export `GIT_DIR=$(jj git root)` for every repository-scoped `gh` call, including retries and auth checks.

| Probe | Meaning |
| --- | --- |
| `jj workspace root` | Absolute root; failure means stop |
| `jj status` | Working-copy changes and conflicts |
| `jj diff` | Uncommitted changes |
| `jj log -r 'ancestors(@, 2)'` and `jj bookmark list` | Resolve feature bookmark and committed tip; `@` may be empty, so inspect `@-` too |
| `GIT_DIR=$(jj git root) git log -10 --format=%B` | Read-only recent subjects AND bodies; compare several through message standards |
| `jj git remote list` and `gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'` | Resolve remotes and default bookmark; if unavailable use `main` only when verified, otherwise stop |
| `gh pr list --head <branch> --state open --json number,url,title,body,state,isDraft,headRefName,headRepositoryOwner` | Run only with a non-empty, resolved bookmark name |

An exit-0 `[]` means no open PR; non-zero means unknown (missing CLI, auth, offline), never none. Recheck auth/connectivity before creating. Never pass an empty head or `<owner>:<branch>`: use the name only and target the base repository with `-R <base-owner>/<repo>` on forks. Match both head owner and branch; never blindly select index 0. If ambiguous, show candidates and stop. Preserve the matching PR URL/body for composition and apply.

All output is a snapshot. Reverify bookmark, exact committed tip, remote, and PR state before push and create. With no feature bookmark, automatically derive and create a non-conflicting one at the intended tip. On the default bookmark with work, follow `branch-creation.md`; with no work, report and stop. JJ does not require a checked-out Git branch. Do not treat an empty working-copy tip alone as no work or no PR.

## Conventions

Before composing any message or recommending its syntax, read `message-standards.md` in full, then read the full Go guide and compare several recent subjects AND bodies at runtime. Project instructions and observed repository syntax always win; there is no fixed Conventional Commit fallback or type default.

"Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards."

Compare prefixes/package names, casing, verb tense, subject/body separation, wrapping, and issue placement; without history use explicit project/user instructions and Go guidance without inventing precedent. The following is verbatim source guidance, not a mandatory repository template:

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
