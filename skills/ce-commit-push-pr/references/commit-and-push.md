# Committing and pushing

If stack construction already committed layers, skip ordinary commit/push and continue to Step 4; Step 5 submits the stack. For default-bookmark work, first follow `branch-creation.md`.

Before composing, read https://go.dev/wiki/CommitMessage in full and follow `context.md` to inspect several complete historical messages anchored to the verified task history head. Project instructions/history override illustrative Go style.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.

## Exact Go excerpts — illustrative source, not a repository template

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

> Please *don’t* use alternate GitHub-supported aliases like `Close` or `Resolves` instead of `Fixes`.

These Go-specific examples do not impose prefixes, issue keywords, or body syntax on this repository. The full runtime read remains mandatory.

> To link a commit to an issue without marking it fixed—for example, if the commit is working toward a fix but not yet a complete fix—GitHub requires only that the issue is mentioned by number in the commit message. By convention, Go commits mention this at the bottom of the message using `For`, where `Fixes` might be expected, even if the number is also mentioned in the body of the commit message.

```text
Refactor func Foo.
This will make the handling of <corner case>
shorter and easier to test.

For #12345
```

> It is common in other Git projects to use `Updates` instead of `For`, and that is acceptable too, even though it makes little sense (the commit does not update the issue). More precise phrasings are fine too. Don’t be too pedantic in code reviews: it’s not worth asking people to change from `Updates` or something else to `For`, or vice versa.

> For non-“go” repos (“crypto”, “tools”, “net”, etc), the subject is still the name of the package, but you need to fully-qualify the issue number with the GitHub org/repo syntax:

```text
cipher/rot13: add new super secure cipher

Fixes golang/go#1234
```

> Notably, the first line subject should **not** contain the `x/crypto/` prefix. We only do that for the issue tracker.

> The CL description is a public document that explains to the future what has been done and why.

## Owned commits

Scan changed files for distinct concerns; use 2–3 whole-file groups at most, or one when ambiguous. Honor `exclude:<paths>` and unrelated changes exactly. JJ has no staging index: inspect tracked, ignored, and untracked paths explicitly. Track only intended new paths with `jj file track <paths>` when needed; do not sweep in secrets or artifacts. Preserve other people's commits and authors; never squash their work into yours. Credit human contributors in prose, without attribution trailers.

Separate owned whole-file work using `jj split -m "<message composed from the standards above>" <owned-paths>` after reviewing the exact diff and completing the message standards read. This avoids an editor prompt; selected changes normally become the parent, with unrelated remainder current. Capture and verify the selected owned revision explicitly; never assume it is `@`. An already isolated owned revision needs no split. Describe that selected revision explicitly with `jj describe -r <verified-owned-revision> -m "<message composed from the standards above>"`. Only when the verified owned revision is already current is this equivalent:

```bash
jj describe -m "<message composed from the standards above>"
```

When already supplied and unambiguous for this one commit, retain the plan unit ID as a semantic requirement only if compatible with project standards; never hunt for a plan. Verify descriptions and exact revision IDs afterward. Move/create only the intended feature bookmark at the verified owned tip; do not publish the unrelated remainder or empty working-copy child.

Apply the **Project publishing gate**, recheck bookmark/remote/PR identity and push permission, and push only that bookmark:

```bash
jj git push --remote <verified-head-remote> --bookmark <feature-bookmark>
```

Track the intended remote bookmark first when required by current JJ help. Clean, already-pushed work is a no-op. A denied or uncertain push stops; never use a Git fallback.
