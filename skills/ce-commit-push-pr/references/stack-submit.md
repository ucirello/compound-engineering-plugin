# Opt-in stack construction and submission

Load only for explicit stack intent or a standing stack preference. Before Step 3 run Probe, Topology and Construction only. Step 5 exclusively owns publishing, submission and per-new-PR description application. Use native JJ, never Git or a Git-backed branch dispatcher. All commands follow `context.md`'s absolute cwd, gh environment and local `.tmp/` requirements. Read `gh-stack-cli.md` for managed-topology and capability safeguards.

## Probe

Verify gh availability/authentication and query complete server-manager membership/order through the GraphQL discovery contract in `skills/ce-babysit-pr/references/stack.md`, following `gh-stack-cli.md`'s classification rules. Preserve exact errors: probe-error, absent membership and unavailable registration are distinct. Do not invoke the Git-backed stack extension, even for view. Determine which operation is actually needed: maintenance of confirmed existing members is supported by native JJ; creation/import/structural edits may require a separate documented registration API. Only a genuinely missing required capability blocks its dependent action. Required intent returns a precise residual for that action; soft preference may use the ordinary single-PR path. Do not install a tool or invoke a different harness.

## Topology

Record original task bookmark, exact tip and working-copy state before probing. Resolve named parents by PR number where possible; verify repository, author, bookmark, remote and exact fetched `headRefOid`. Validate externally obtained bookmark names before interpolation and prefer argv calls. Never reset an unrelated/stale local bookmark sharing a name.

Fetch each exact affected head with `jj git fetch --remote "<verified-remote>" --branch "exact:<bookmark>"`, resolving the fetched remote bookmark to a full OID and comparing it to fresh API metadata. Retain manager ID, complete order, trunk, exact head/base repositories and names, draft/closed state, every affected old remote tip and old immediate parent. Preserve recovery bookmarks and evidence outside any disposable workspace before mutations.

Preserve existing managed topology. A parent already in a stack must be the permitted top for a new layer; never move to a different top just to clear a failure. A standalone parent may remain an untouched trunk, or be adopted as the bottom only when its author is the current user and that adoption is authorized. Unknown topology is a residual, not “standalone.”

For an explicit new upstack layer, use the authoritative confirmed parent tip: fetched remote when current, otherwise its verified unpublished local tip. Never apply the default-base recipe to a named/upstack parent. Do not move bookmarks or working state merely to inspect metadata.

When no topology exists, derive the smallest useful linear, independently reviewable layers from the complete original range plus working changes. Foundation first; each layer must work against its immediate parent without later-layer prerequisites. Standing preference alone does not justify artificial slices or splitting one logical change; explicit stack requests are not refusable on that ground.

## Construction

Use whole-file groups or existing change boundaries, never forced hunk partitioning. A clear safe split needs no further approval under explicit stack intent. Materially different boundaries require an interactive proposal; pipeline mode returns that proposal as a residual. Hunk-level splits or published-history rewrites require explicit confirmation; pipeline mode stops rather than rewriting.

On the default bookmark without a named parent follow `branch-creation.md`, including the local-only-commit decision. On an existing feature bookmark resolve and fetch the actual base remote and verify its tip; do not treat all feature commits as default-branch unpushed work. A verified local parent tip may be used when no remote bookmark exists.

Preserve the original tip with a recovery bookmark before rearranging unpublished work. Existing coherent commit boundaries can be adopted by creating one nonconflicting bookmark at each planned tip. Otherwise use path-scoped `jj commit <owned-paths> -m "<message composed from the standards above>"` and native JJ rearrangement only after verifying each parent and preserving recovery. Before **each** message composition read and follow `commit-and-push.md`'s strongest instruction, full runtime Go-guide read, several complete JJ descriptions at that layer's actual history anchor, and labeled source excerpts. Repository-local syntax wins. Record applicable known U-IDs semantically using local conventions, never a fixed suffix template.

Excluded files belong to no layer: never save, move, commit or restore them. Preserve tracked, ignored and untracked user work. If a required operation collides with excluded/unrelated files or cannot safely preserve them, stop with a residual. Keep any saved run-owned evidence under local `.tmp/` until the reconstructed top is verified against the complete original change set minus exclusions. Verify linear parent order, each bookmark's exact tip, file coverage and full top content before submission.

## Submit — Step 5 only

Apply the Project publishing gate to every exact layer being sent. Resolve archival first: if `pr_teaching_archive` is on, stop before submit with a residual rather than silently disabling it or adding a post-submit explainer change outside the stack manager.

Inspect existing draft layers. Never mark someone else's draft ready without explicit opening intent. Create ready PRs when authorized; retain existing drafts otherwise. A draft-only result is a hard residual before babysit when babysit is on, not a successfully shipped stack.

Re-probe complete manager membership/order and affected API/remote heads before each transaction. For **unchanged existing managed membership**, publish each verified owned bookmark with `jj git push --remote <verified-remote> --bookmark <layer>` using the captured remote-tracking lease. Do not force over movement. No separate registration operation is needed merely to preserve existing member identities and PR/base relationships.

When a changed parent requires dependent propagation, use the native recipe in `skills/ce-babysit-pr/references/stack-commands.md`. Require clean authorized workspace/isolation with no unrelated tracked, ignored, untracked or conflicted content. An empty `@` directly above the verified head is already aligned; otherwise clean alignment to the verified head uses `jj new "<verified-head>"` without repeat approval. Preserve the already-pushed active target unchanged. For each open dependent bottom-to-top, verify its old tip still matches baseline, select only `"<old-parent>..<old-tip>"`, and run `jj rebase --revisions "<verified-layer-revset>" --destination "<new-immediate-parent>"`. Verify the range excludes lower/unrelated work, inspect the interdiff, confirm ancestry and reapply publishing gates before moving only that layer's bookmark and lease-pushing. A conflict stops propagation without pushing the conflicted tip.

After every success or rejection, fetch/re-probe affected remote/API heads and manager/base relationships against baseline and expected new tips. Unexpected movement is a residual, never force permission. Native pushes may be non-atomic: report updated layers, remaining layers and the first rejected/divergent layer; never require unavailable multi-ref atomicity as a blanket prerequisite or report partial progress as all-or-none success.

For **new PRs/adoption/changed structure**, use `--allow-new` only for authorized new bookmarks and create PRs through repository-scoped `gh pr create` with exact verified head/base identities and local body files. This alone does not establish managed membership. Perform any required creation/import/registration through the provider's documented API-native operation, then verify complete manager membership/order and PR URLs. If that server operation is unavailable, return the exact capability residual before its dependent publication where possible. If earlier actions already succeeded, retain recovery state and report their concrete bookmarks/PR URLs rather than rerunning create or silently claiming a managed stack. A required manager-specific atomic operation remains a genuine residual when the native transaction cannot satisfy it.

For each new PR, use its explicit URL for ordinary Step 4 composition, deriving its immediate parent and exact head. Apply its title/body through `gh pr edit` with a local body file under `apply-and-handoff.md`. Never rely on a current branch to select the PR. Existing PR descriptions remain unchanged unless explicitly requested, approved as an optional rewrite, or receiving an already-authorized factual maintenance refresh. Pipeline defaults to no optional rewrite.

Report the bottom open non-draft PR and hand off with `posture:stack-ready`; only explicit land intent allows `posture:stack-land`. Pipeline callers also pass stack-wide scope. Never use `gh pr merge` on managed members; the babysitter owns landing through the verified supported stack interface.
