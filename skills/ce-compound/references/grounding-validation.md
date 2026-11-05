# Grounding Validation (Phase 2.45)

Read this when Phase 2.45 runs. The doc just written becomes permanent, trusted knowledge. Future agents will act on its claims without re-verifying them. This phase checks the claims against reality before they compound: a deterministic mechanical pass (bundled script) plus a semantic pass (one read-only validator subagent). Neither pass is a hard stop. You judge every flag, because solution docs legitimately cite deleted paths and pre-fix states.

## Which tree is the ground truth

Two claim categories verify against different trees:

- **Code-behavior claims** (enum values, status semantics, limits, defaults) verify against the **local working tree**. They describe what this session's work produced and verified here.
- **Merge-state claims** ("fixed in #1608", "landed", "shipped") verify against **remote truth**. The checkout may predate a merge, so `gh pr view` (or the tracker equivalent) is primary and native JJ reachability is only the fallback. The script's `INFO: worktree is N commits behind …` line tells you how much to distrust the local tree for this category.

Run every JJ command from the target workspace's absolute root. For repository-scoped `gh`, obtain and export `GIT_DIR=$(jj git root)` there before invoking it. Optionally run `jj git fetch` (best-effort; skip silently on failure or offline, because the network is never a correctness dependency). When remote state cannot be checked at all, keep the claim, add an as-of qualifier ("as of this writing"), and record degraded verification in the run report. See https://docs.jj-vcs.dev/latest/cli-reference/ .

## Capture the history inputs before validation

Resolve the intended committed-history anchor from the actual task and repository, and capture its exact commit ID with `jj log --no-graph -r '<verified-history-head>' -T commit_id` from the absolute workspace root. Pass it as `--history-head <captured-id>` on every validator invocation, including refresh, Lightweight and reruns. Prefer the task's verified committed head or the pre-edit committed revision captured before local changes; inspect full subjects AND bodies (`jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\n"'`) and task evidence when choosing. Do not blindly choose `@` (JJ snapshots may already contain a deletion), or blindly `@-` (a nonempty current change can itself be the intended committed head). Preserve the captured ID across validation reruns; a style-history sample is not a replacement for an exact reviewed base/head range. No helper should reselect that range or silently widen it.

For the actual remote default, the helper accepts only resolvable recorded remote-HEAD metadata, not `trunk()` or guessed `main`/`master` bookmarks. If that metadata is absent/ambiguous, use repository-scoped `gh repo view --json defaultBranchRef` for the verified remote repository, then resolve its exact default bookmark head in JJ and pass `--upstream-head <verified-id>`. Do not substitute a different remote or fetch another ref. Without verified remote-default evidence leave it unknown and report degraded merge-state coverage; a synthetic root commit is never a default head. Missing history-anchor evidence likewise must be reported and adjudicated, never guessed: run the mandatory mechanical validator anyway for working-tree paths, commit resolution, links and scaffold, then resolve/manual-check historical claims at the same scope before claiming full coverage. Missing inputs are not permission to skip mandatory validation.

## Step 1: Adjudicate the mechanical flags

The script reports in two tiers and you decide each item. A **FLAG** is a claim it can defend; a **NOTE** is an item it reported without being able to classify, and notes do not affect its exit code. There are three resolutions, **fix**, **annotate**, or **confirm intentional**, and never an automatic rewrite or an automatic pass:

| Flag | Likely meaning | Resolution |
|------|----------------|------------|
| path not found under the search base | Typo, drafted from memory, or a real file in a repo or store the check did not search | Keep the citation if the file exists in another repo or store you can check; otherwise fix the citation or remove the claim |
| path missing here, exists at upstream | Stale checkout | Verify the claim against upstream; annotate if the doc implies the file is present locally |
| path deliberately gone (doc says removed/renamed) | Historical citation | Confirm the surrounding prose marks it as historical ("removed by this fix", "pre-fix state"); add that marker if absent |
| SHA does not resolve, cited as a commit | Fabricated or from another repo | Replace with the PR number, or drop |
| NOTE: unresolved hex, no commit context | The script cannot tell a session id or content hash from a commit; it is reporting, not accusing | Read the line: if it was never a commit citation, nothing to do; if it was, verify it |
| SHA reachable from HEAD only | Local-only commit; SHA will change on rebase/squash merge | Replace with the PR number |
| SHA reachable from upstream only | Checkout predates the merge | Keep, with a temporal qualifier; verify the landed claim via `gh` |
| SHA exists but unreachable | Rebased-away commit | Replace with the PR number |
| scaffold ("Learning 3", `{{…}}`) | Drafting-context leak | Always fix; rewrite as a real path or link |
| relative link unresolved | Wrong target | Fix the path |

If the script cannot be resolved on this platform, apply its checks manually at the same scope: scan the body for cited paths that do not exist, hex words presented as commits anywhere in the body (in commands and code blocks as much as in prose), `Learning(s) N` / `{{…}}` scaffold, and broken relative links. Note in the run output that the check was manual. Do not silently skip.

After any body edit from this step or Step 2, re-run the script until it reports clean or every remaining flag is confirmed intentional.

## Step 2: Semantic validator subagent (Full and non-interactive; skipped in lightweight)

Dispatch **one generic read-only subagent** covering the written solution doc plus any `CONCEPTS.md` entries added or edited this run. Phase 2.4's entries are claims too; a glossary entry written from a session-level summary is exactly how wrong semantics enter the vocabulary. Use the same mid-tier model class as other reviewer subagents when the platform exposes one.

Apply `references/modes.md`'s native dispatch permission/model/depth rules. User-requested models and permitted configured roles take precedence over the default tier as intent, but never pass a model override forbidden by the host. Use suitable inherited-model reviewers when delegation is allowed; required unavailable independence is incomplete coverage. Classify actual dispatch failures and preserve this validator's coverage in any allowed fallback.

Build its prompt from this template:

```
You are a grounding validator for documentation about to enter a permanent
knowledge store. You are read-only: never edit files. Inspect with Read,
Grep, Glob, non-mutating JJ, and gh when available. Run JJ from the absolute
workspace root; export GIT_DIR=$(jj git root) there before repository-scoped gh.

Inputs: the doc content below, the CONCEPTS.md entries below (if any), and
this staleness context: <INFO line from the mechanical script, or "none">.

Check every factual claim in three categories:

1. CODE-BEHAVIOR CLAIMS — assertions about how code behaves: enum values,
   status semantics, limits, defaults, ordering, state transitions. For
   each, locate the defining source in the current tree and quote the
   defining line(s) with file:line. Verdict: verified (with quote),
   contradicted (with the quote showing otherwise), or unverifiable
   (defining source not found).

2. MERGE-STATE CLAIMS — assertions that a change landed ("fixed in",
   "merged", "shipped in", "resolved by #N"). Primary check: gh pr view
   <n> --json state,mergedAt,baseRefName (remote truth). Fallback: native JJ
   reachability from the verified upstream default bookmark: from the absolute
   workspace root use jj log --no-graph -r '<sha> & ::<verified-upstream-head>'
   -T commit_id; successful nonempty output establishes ancestry, an empty
   successful result does not, and command failure is degraded verification.
   Never substitute a guessed default ref. Verdict: verified,
   contradicted (e.g. PR open, not merged), or unverifiable (offline / no
   gh) — mark unverifiable as "degraded", do not guess.

3. INTERNAL COMPLETENESS — countable assertions ("six PRs", "three root
   causes", "all N consumers"). Count the substantiating items in the doc
   itself. Verdict: complete, or short (found M of N).

Ignore session narrative ("we first tried X") — that describes the
conversation, not the tree. Ignore style.

Return a structured list, one entry per claim checked:
  claim (verbatim) | category | verdict | evidence (quote + file:line, or
  command output) | suggested edit (only for non-verified claims)
```

**Orchestrator handling of verdicts:**

- **contradicted** → fix the doc using the quoted evidence (the quote, not the conversation, is authoritative)
- **unverifiable** (behavior) → soften or attribute ("per this session's conclusion…"), or drop the claim
- **unverifiable/degraded** (merge-state) → keep with an as-of qualifier; record degraded verification in the report
- **short** (completeness) → complete the enumeration or restate the count to match what the doc substantiates
- **verified** → no change

## Reporting

Summarize the phase in one line of the run output (non-interactive report's `Grounding:` line; interactive success output): flags adjudicated (fixed / annotated / confirmed), claims checked, claims softened or corrected, and `degraded — merge-state claims unverified offline` when applicable.
