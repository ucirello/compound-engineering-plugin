# Opt-in JJ stack construction and publication

Load only for explicit stack intent or standing preference. Before ordinary Step 3 run Probe, Topology, and Retrospective construction; Step 5 alone publishes and applies descriptions. A residual is an unresolved item returned rather than guessed. Consult https://docs.jj-vcs.dev/latest/cli-reference/ and `references/gh-stack-cli.md`.

Run every JJ command from the target workspace's absolute root. Export `GIT_DIR=$(jj git root)` there for every repository-scoped `gh` call. Put every scratch, saved patch, fallback, and error artifact under that workspace's `.tmp/` and ensure it is ignored.

## Probe

Check `gh` availability/auth and installed `gh stack <command> --help`. Probe read-only stack metadata and externally managed JJ layer registration support, never Git checkout-mutating commands. If the CLI, repository stack support, or a required operation is unavailable, report a residual. Explicit stack intent or a forcing preference requires a hard stop; soft intent can fall back to ordinary single-PR creation with that limitation reported. Unknown stack state is not evidence of standalone status.

## Topology

Record original working-change ID, committed tip, bookmarks, and JJ operation ID before classification. Parent lookup must not move the workspace. Resolve a named parent PR by number and exact head SHA, validate its owner, branch, state, and base, fetch and verify its tip, then derive stack order from ancestry and PR bases. Branch-only parents are local trunks until remote identity is proven. Reject unsafe shell-interpolated branch names; require `[A-Za-z0-9._/-]+` or pass validated names as argv.

- Existing stack: preserve it. If a named parent is not top, return a residual rather than attaching to another layer.
- Standalone parent: keep it an untouched trunk; adopt it as bottom only when its PR author is the current user. Verify any existing local bookmark is at the exact parent SHA; do not reset a stale/colliding bookmark.
- Unknown, ambiguous, or unavailable parent: stop with a residual, never infer standalone.

For a directed upstack layer, use the authoritative fetched parent remote tip, or the verified local parent tip when newest work is local-only. Do not use the default base flow or hard-code origin when another remote tracks the parent. Preserve all current/excluded changes; stop on conflicts or overwrite collisions without stashing or removing paths. Use `jj new <verified-parent-tip>` only after unrelated current work is safely preserved; create the layer bookmark at its committed tip.

When only a standing preference requested stacking and the complete work is one logical change or would require artificial slices, refuse the stack and use the single-PR route. An explicit request is not refusable for those reasons.

## Retrospective construction

Inspect the complete change set against the resolved base: existing commits and all working-copy changes, including newly tracked files. Derive the smallest useful linear independently reviewable layers, foundation first. Each layer must be coherent against its parent, without dependencies on upstack layers. Use whole-file groups or existing boundaries, never hunk partitioning to force a split.

One safe topology can proceed without asking because explicit stack intent authorizes local layers. If reasonable alternatives materially change review boundaries, ask for a concise bottom-to-top choice; pipeline mode returns that proposal as a residual. Hunk partitioning or published-history rewriting requires explicit confirmation; pipeline mode does not perform it. Never rewrite published history without authorization.

When starting at the default bookmark with no named parent, follow `branch-creation.md`, including the unpushed-local-commit decision. From an existing feature bookmark, use the exact fetched base tip rather than carrying the entire feature tip into the bottom layer. A verified local parent materialized by other means need not have a remote bookmark. Preserve the original feature tip with a recovery bookmark and record operation ID before any rewriting.

Excluded paths belong to no layer and stay exactly as found: do not save, move, restore, or commit them. Preserve all other tracked/untracked work until the complete top is verified. If reparenting would affect excluded paths, stop with a residual. For whole-file working-copy groups, use explicit-path `jj split` or `jj commit`, verify each resulting change against the plan, and rebase only unpublished planned changes into dependency order. Consult installed command help before choosing split semantics. Preserve unrelated work and recovery evidence; do not perform a broad restore or abandon.

Before composing any layer description, read `references/message-standards.md` in full and perform its full-Go-guide and several-recent-subjects-AND-bodies comparison at runtime. Repository-local syntax always wins. Describe the layer's semantic content, and record an already-known applicable U-ID using observed syntax, without a fixed subject suffix; do not hunt for a plan. Omit unclear or multi-unit IDs.

```bash
jj commit -m "<message composed from the standards>" -- <layer-files>
jj bookmark create <layer-bookmark> -r <verified-layer-tip>
```

For already committed work matching layer boundaries, create/reuse bookmarks at each exact planned tip; reuse the original feature bookmark only if its unchanged tip is one of them. Keep a recovery bookmark before rearranging unpublished commits. Verify ancestry order, exact bookmark targets, and the top's complete original change set minus exclusions before submission. Never depend on undocumented `gh stack view` ordering.

## Submit (Step 5 only; ready/non-draft)

Apply the Project publishing gate to every exact commit state. Resolve the ordinary teaching archive gate first: if archival is on, stop with a residual before publication; do not silently disable it or create a post-submit explainer commit until a manager-aware route exists.

Inspect existing layer PRs and drafts. Never mark an existing draft ready without explicit authorization. Publish each verified layer bookmark bottom-to-top with `jj git push --remote <head-remote> --bookmark <layer-bookmark>`; for a new layer, create its PR with explicit `--head <layer>` and `--base <immediate-parent>` plus composed title and `--body-file <local-tmp-file>`, after the ordinary duplicate/owner checks. Use `--draft` only when requested. Existing PRs synchronize through bookmark pushes and retain titles/bodies unless an explicit rewrite is authorized; pipeline mode keeps the conservative no-rewrite default.

Register externally managed layer relationships only through the installed, verified `gh stack link` interface described in `gh-stack-cli.md`. Require a receipt for every bookmark push, PR URL/head/base mapping, and server relationship. Re-read remote PR metadata to verify coverage of every planned layer and correct topology. If any push/create/link/verification fails, stop with a bounded residual identifying completed and missing layers; never report a partially published or unregistered stack as success or blindly recreate PRs on retry. If the repository cannot support externally managed stack registration/landing, hard-stop required intent before external writes.

After submission, compose descriptions for each PR created this run using its explicit URL, so PR mode uses its immediate parent and exact head. Apply with `gh pr edit <pr-url>` and a body file; never use the current working-copy bookmark implicitly. Existing PRs retain descriptions unless rewrite was requested. Draft-only outcomes are hard residuals before babysit when babysit is on.

Hand off the bottom open non-draft PR with `posture:stack-ready` by default or `posture:stack-land` only on explicit land intent, and stack-wide scope for pipeline submissions. Managed members must not land through `gh pr merge`; the callee/user owns verified stack landing. Step 5 exclusively owns submission, description application, receipts, and handoff.

## Layer message composition standard

"Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards."

Before composing, read the full Go guide at runtime and compare several recent subjects AND bodies with `(cd "$workspace_root" && GIT_DIR=$(jj git root) git log -10 --format=%B)`, from the absolute target workspace root. Compare prefixes/package names, casing, verb tense, subject/body separation, wrapping, and issue placement. Repository-local instructions and observed syntax ALWAYS win; apply compatible Go guidance within that pattern. Without history, use explicit project/user instructions and Go guidance without inventing precedent. The following is verbatim source guidance, not a mandatory repository template:

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
