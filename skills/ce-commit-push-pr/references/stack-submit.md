# Opt-in JJ-native stack construction and submit

Load only when stack intent or standing preference applies. Explicit stack requests require a stack; do not reinterpret them as one PR with a custom base. A standing preference alone does not justify artificial slices of one logical change. All commands use Context's absolute-root JJ and repository-scoped gh environment. Never invoke `gh stack` or another Git-backed branch/workspace bridge.

Before ordinary Step 3, probe metadata, resolve topology, and construct layers only. Step 5 exclusively owns publishing and description application. Unresolved requirements are residuals, not guesses; pipeline mode returns decisions rather than asking.

## Topology

Resolve a named parent by PR number when available, using `gh-stack-cli.md`'s metadata contract. Verify exact head repository, bookmark, remote, and commit, fetching with JJ. A branch-only parent must be verified directly and serves as an untouched trunk unless adoption is authorized. Preserve existing stack topology. Record the original work head and preserve recovery bookmarks before any rewrite; metadata probes must not switch the work to the parent.

Each new layer must descend from its exact authoritative parent tip: use the verified current remote tip when authoritative, or verified local parent when its latest work is unpublished. Never assume origin or silently use a stale remote parent. Validate ref arguments and pass them as argv data, never interpolate untrusted names into shell code. If the named parent is ambiguous, shared, or not safely usable, stop rather than parent onto another layer.

## Construction

Inspect the complete original change set against the resolved base: existing commits plus tracked and untracked working changes. Exclude `exclude:<paths>` entirely; never save, move, restore, or commit them. Plan the smallest independently reviewable linear layers, foundation first, using whole-file groups or existing commit boundaries. Each layer must work against its parent without depending on later layers.

When one safe topology is clear, explicit stack intent authorizes local bookmarks and commits. Ask about materially different review boundaries, hunk-level splitting, or published-history rewriting; pipeline mode returns the proposal as a residual without rewriting. Never rewrite published history without explicit authorization.

On the default with no named parent, follow `branch-creation.md`'s fresh-base and unpushed-local-commit decision. On a feature bookmark, verify the resolved base or exact local parent, not the entire feature tip as the bottom parent. For existing coherent commit boundaries create bookmarks at the verified layer tips. Otherwise use native JJ commit/split/rebase on owned unpublished changes only, preserving recovery references and all original tracked/untracked work until the complete top is verified. Stop if excluded or ignored content could be overwritten. Do not stash, discard, or reset unrelated work.

Before composing each layer description read `commit-and-push.md` in full, including its verbatim Go source guidance and runtime history comparison. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards. Read the full guide and several subjects AND bodies at the task's verified history head; repository-local syntax always wins. Known plan U-IDs are semantic content, not fixed syntax. Use neutral `jj describe -r <owned-layer> -m "<message composed from the standards above>"` or path-scoped `jj commit` as appropriate.

Go source guidance below is illustrative, not a required repository template; the runtime repository pattern above wins:

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

Verify ancestry, each parent-relative diff, planned layer order, and that the top contains the complete original change set minus excluded paths. Preserve original recovery references until verification succeeds.

## Submit — Step 5 only

Apply the Project publishing gate to every exact layer state. Resolve teaching archival first: if archival is requested and a safe layer-aware archival route is unavailable, stop with a residual before publishing; do not silently disable it or add surprise post-submit commits.

Push each verified layer bookmark with `jj git push --remote <verified-remote> --bookmark <layer>`; explicitly selected new bookmarks are automatically tracked. Re-query matching head owner/bookmark before each create to prevent duplicates. Use `gh pr create --base <immediate-parent-bookmark> --head <verified-head-bookmark> --title <composed-title> --body-file <local-body-file>` for each new layer. Preserve existing drafts; mark them ready only when explicitly authorized. Respect user/project draft requests. Otherwise open new PRs ready for review. A draft-only outcome is a residual before babysit when monitoring requires ready PRs.

Map each PR URL to its verified head and immediate parent. Compose each new description in explicit PR mode, never from whichever working-copy change happens to be current. Existing descriptions receive authorized factual maintenance directly, preserving user content and issue links; optional rewrites require separate approval and pipeline mode defaults to no optional rewrite. Declining a rewrite never blocks authorized handoff.

Report the bottom open non-draft PR and hand off with `posture:stack-ready`, or `posture:stack-land` only on explicit landing intent. Preserve stack-wide pipeline scope. Never merge a member independently. If server-side stack linkage beyond explicit PR bases is required but unavailable through permitted APIs, report incomplete stack coverage, not a successfully managed stack.
