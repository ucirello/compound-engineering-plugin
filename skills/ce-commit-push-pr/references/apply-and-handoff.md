# Applying the PR, reporting, and the babysit handoff

**Description-only mode** — print the title and body. Stop unless the user asks to apply.

**New PR** (full workflow, no existing PR from Step 1, resolve branch and PR state) — if **Stack mode** is active, follow the Submit section of `references/stack-submit.md` instead of `gh pr create`; then report the bottom open non-draft PR URL and continue to the babysit handoff. Otherwise, immediately before creating, **always** re-run `gh pr list --head <branch> --state open --json number,url,isDraft,headRefName,headRepositoryOwner` (branch name only; target the base repo on a fork, per Context). This catches a PR that appeared since Step 1, or one the Step 1 check missed because it came back **unknown**, so you do not open a duplicate. If the list now shows a PR whose `headRepositoryOwner` and `headRefName` match the current head, switch to the existing-PR path. When several forks match, pick by head owner as in Step 1 rather than assuming index 0. If this re-check itself exits non-zero, resolve `gh auth status` or connectivity before creating; do not assume no PR exists. Otherwise apply per "Applying via gh" below using `gh pr create`. Report the URL.

**Existing PR** (full workflow, found in Step 1) — if **Stack mode** is active, follow the Submit section of `references/stack-submit.md` so remaining layers publish or sync; then report the bottom open non-draft PR URL and continue to the babysit handoff. Otherwise the new commits are already on the PR from Step 3. Report the URL. Apply an already-authorized factual maintenance refresh directly; only an optional rewrite outside that path asks whether to rewrite the description.

- **No** — skip the description rewrite and continue to the babysit handoff rule below.
- **Yes** — run Step 4 if not already done, then use the separate optional-rewrite preview/apply flow below.

**Authorized maintenance or explicit apply request** — factual refresh of a stale description during already-authorized babysitting is part of the job, not the standalone rewrite approval flow. Apply verified results of this run without another yes/no or preview-approval question; preserve unrelated user-authored content and existing issue links. An explicit description-update apply request likewise needs no duplicate approval. Compare before editing and skip an identical result.

**Optional existing-PR rewrite** — outside those authorized paths, preview and obtain approval before applying. Ask: "New title: `<title>` (`<N>` chars). Summary leads with: `<first two sentences>`. Total body: `<L>` lines. Apply?" If declined, keep the existing description and proceed to any otherwise authorized babysit handoff. Never bundle this question with permission to align the workspace or monitor, and never make rewriting a prerequisite for monitoring. Description-only remains draft-only unless the user asks to apply.

**Explainer archival** — runs only in the full workflow, when all of these hold: `pr_teaching_archive` is on, the composed body has a `## New concepts` section, and the apply was confirmed (a new-PR create, or an existing-PR rewrite the user accepted). A declined rewrite skips archival entirely, so no unlinked doc commit is left behind. Resolve every path from the repo root gathered in Context, never from the CWD. With two taught concepts, write one file per concept and stage both in the single commit. Run these steps, in order, immediately before the `gh` call:

1. Inspect ignore rules for `<root>/explainers/YYYY-MM-DD-<concept-slug>.md` from the workspace root before writing. If ignored, warn and skip archival entirely; never force-track it.
2. Write the file (create the directory if needed) with YAML frontmatter `title`, `date`, `input_shape: concept`, `subject`, and the teaching content. If the file already exists from a prior run, overwrite it.
3. Commit only those files using path-limited `jj commit`. Read and apply the complete runtime message standards in `references/commit-and-push.md` (full Go guide plus recent backend subjects AND bodies; repository syntax wins). Describe the taught concepts without imposing a fixed message. Re-apply the **Project publishing gate** to the exact resulting state and push only the verified head bookmark. If no file changes remain, keep the link and continue.
4. Add a head-branch blob URL for each doc into the `## New concepts` section before applying. Build the URL for the repo's actual host — for example `gh browse -n -b <head-branch> -- <path>` prints the link on whatever host `gh` targets, GitHub Enterprise included. Do not hardcode `github.com`, or the link 404s on GHE.

If the doc write, commit, or push fails, warn and continue to PR creation without the link. Never leave the flow stopped between the commit and the PR.

**User-runnable invocation rendering.** For the output handoffs below, default to `/ce-explain <name>`. Use `$ce-explain <name>` only when the active host is Codex or explicitly documents dollar-prefixed skill invocation. Render only the invocation as inline code and output one form only.

**Concept trailer** — when a body applied by this run contains a `## New concepts` section, print one line after the PR URL in every mode: `New concepts: <name>[, <name>]`. In interactive full-workflow runs follow it with one line per taught concept telling the user to invoke `ce-explain <name>` using the rendering rule above. Print no trailer when this run applied no body — including a rewrite that was declined or that pipeline mode defaulted to no — or when no PR exists.

**Resolve the standing opt-out before applying the handoff rule below.** Read `auto_babysit` by the rule here, at the handoff. A config read from an earlier step does not carry over: a run that reaches the handoff without having read the key hands off against the user's standing choice, and a compacted run is the ordinary way that happens.

<!-- ce-config-layers:start -->
**Resolve ordinary yaml keys from the two repo files.**

- **Read** `<repo-root>/.rocketclaw/config.local.yaml`, then `config.yaml` (`<repo-root>` = `jj workspace root`). Missing files are skipped. Ignore rules do not change resolution.
- **Win** with the first active (non-commented) value. For scalars, empty is unset; an invalid value continues to the next layer, then the skill default. For lists and maps, a present key — including an empty list or map — replaces the whole key.
- **Do not** use this rule for `docs_root` — that key is `config.yaml` only.
<!-- ce-config-layers:end -->

Babysit is off only when the winning active value is exactly `false`; a missing key or any other value leaves the default **on**. A handoff the user opted out of is a **successful terminal for this run**, not a blocked one — report the PR URL, say in one line that babysit was skipped by standing config, and stop.

**Babysit handoff — default on; completion gate.** After a newly-created PR, a successful stack submit, or new commits on an existing open PR, this run is not done until `ce-babysit-pr` owns follow-on or an explicit skip below applies. Reporting the PR URL alone is not success. Announce the automatic handoff in one non-blocking line, then invoke the skill through the host's normal skill-invocation mechanism; never ask yes/no.

After a stack submit, hand off the bottom open non-draft PR with the derived `posture:stack-ready`, or `posture:stack-land` when the user explicitly asked to land, plus stack-wide scope when a pipeline submitted the stack. Report that ownership transfer so an outer orchestrator does not start a second bare babysit on the current branch.

**Success** = `ce-babysit-pr` owns the monitoring lifecycle. Load and follow its instructions before choosing the monitoring mode. If you are running it in this session, continue until its stop condition permits a final report. In `mode:pipeline`, wait for its pipeline stop and return the structured result. Before reporting success, render every returned typed `needs-human` residual unchanged under `## Needs your decision` and pass the same objects up to the top-level coordinator. `babysit:off` disables only new monitoring; it does not suppress a typed residual already known to this run or supplied by its caller.

Clean JJ head alignment and starting/re-arming authorized monitoring need no extra approval. Verify the head repository, bookmark, remote and exact pushed commit first. An empty `@` directly above that commit is already aligned. Otherwise inspect tracked changes, conflicts and ignored/untracked work; only a clean, verified-safe workspace may use `jj new <verified-pushed-head>` from its absolute root. Preserve unrelated work. Dirty/conflicted state, uncertain targets, denied permissions or unknown push authority take the existing safe stop/decision path, never reset, discard or guessed alignment. Respect watch-mode boundaries, standing opt-outs, final-merge authorization and genuine needs-human decisions.

Never start babysit mechanics yourself: do not run `pr-snapshot`, arm a watcher, or reconstruct the loop. Never substitute `ci-watcher`, `gh pr checks --watch`, ad-hoc polls, or a promise to babysit later. **Handoff blocked:** if the skill cannot be loaded or started, stop and report the failure. Do not invent a parallel or narrower watch.

A `babysit:` token on this invocation decides this run whatever the config says — `off` skips, `continuous` and `checkpoint` force that mode and run even under a standing opt-out. With no such token, the resolved `auto_babysit` above decides.

A draft-only stack submit is a hard residual before babysit when babysit is on.

**Do not fire (auto-detected, no flag needed):** the automatic handoff does not start in any of these cases.
- `mode:pipeline` **except** when this run completed a stack-mode submit (then hand off with the derived posture as above).
- Description-only or description-update mode.
- No PR created or updated this run.
- A non-GitHub host.
- A **draft PR** this run created or updated. A draft is the author's not-ready signal: announce the skip, and say `ce-babysit-pr` can start once the PR is ready. An explicit `babysit:continuous` or `babysit:checkpoint` still forces the watch — pass `watch` or `checkpoint` into the invocation so its draft boundary arms.
- **A head branch you cannot push to.** **Fork PRs are drivable — not a hard-off** when you can push the head (common for a branch this skill just pushed): babysit reads state on the **base** repo and pushes fixes to the **head** repo. Hard-off only when the head is not pushable.
**Soft-degrade (after successful handoff only):** `ce-babysit-pr` decides whether checkpoint mode applies and owns its report and resume invocation. Checkpoint is not a substitute for a failed handoff.

## Applying via gh

The body **must** be written to a temp file and passed via `--body-file <path>`. Never use `--body-file -`, stdin pipes, heredoc-to-stdin, or `--body "$(cat ...)"` — wrappers and stdin handling can silently produce an empty PR body while `gh` still exits 0 and returns a URL.

```bash
cd "$workspace_root"
export GIT_DIR=$(jj git root)
mkdir -p "$workspace_root/.tmp"
BODY_FILE=$(mktemp "$workspace_root/.tmp/pr-body.XXXXXX")
cat >> "$BODY_FILE" <<'__PR_BODY_END__'
<the composed body markdown goes here, verbatim>
__PR_BODY_END__
```

The quoted sentinel keeps `$VAR`, backticks, and any literal `EOF` inside the body from being expanded.

For `<TITLE>`: substitute verbatim. If it contains `"`, `` ` ``, `$`, or `\`, escape them or switch to single quotes.

```bash
gh pr create --title "<TITLE>" --body-file "$BODY_FILE"   # new PR
gh pr edit   --title "<TITLE>" --body-file "$BODY_FILE"   # existing PR
```
