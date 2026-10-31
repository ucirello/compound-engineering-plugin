# Applying the PR, reporting, and the babysit handoff

**Description-only mode** — print the title and body. Stop unless the user asks to apply.

**New PR** (full workflow, no existing PR from Step 1, resolve branch and PR state) — if **Stack mode** is active, follow the Submit section of `references/stack-submit.md` instead of `gh pr create`; then report the bottom open non-draft PR URL and continue to the babysit handoff. Otherwise, immediately before creating, **always** re-run `gh pr list --head <branch> --state open --json number,url,isDraft,headRefName,headRepositoryOwner` (branch name only; target the base repo on a fork, per Context). This catches a PR that appeared since Step 1, or one the Step 1 check missed because it came back **unknown**, so you do not open a duplicate. If the list now shows a PR whose `headRepositoryOwner` and `headRefName` match the current head, switch to the existing-PR path. When several forks match, pick by head owner as in Step 1 rather than assuming index 0. If this re-check itself exits non-zero, resolve `gh auth status` or connectivity before creating; do not assume no PR exists. Otherwise apply per "Applying via gh" below using `gh pr create`. Report the URL.

**Existing PR** (full workflow, found in Step 1) — if **Stack mode** is active, follow Submit in `references/stack-submit.md` and continue to the handoff. Otherwise Step 3 already pushed the commits. Report the URL. Authorized factual maintenance or an explicit apply request follows Description application below without asking again. Outside those paths, offer an optional rewrite separately from monitoring:

- **No** — skip the description rewrite and continue to the babysit handoff rule below.
- **Yes** — run Step 4 (compose the PR title and body) if not already done, then preview and apply (see below).

**Description application** — compare first; identical content needs no edit. During already-authorized babysitting, apply a factual refresh with verified results without another approval, preserving unrelated human content and existing issue links. An explicit request to apply also needs no repeated confirmation. Outside those paths, preview an optional existing-description rewrite and ask approval before applying with `gh pr edit`; a declined rewrite keeps the description and continues any otherwise authorized monitoring. Never bundle rewrite approval with alignment or monitoring. Description-only stays draft-only.

**Explainer archival** — runs only in the full workflow, when all of these hold: `pr_teaching_archive` is on, the composed body has a `## New concepts` section, and the apply was confirmed (a new-PR create, or an existing-PR rewrite the user accepted). A declined rewrite skips archival entirely, so no unlinked doc commit is left behind. Resolve every path from the repo root gathered in Context, never from the CWD. With two taught concepts, write one file per concept and stage both in the single commit. Run these steps, in order, immediately before the `gh` call:

1. From the absolute root run `jj file list` to establish existing tracked paths. Before writing, inspect the candidate's ancestor directories and evaluate the repository's effective ignore rules (including global excludes, nested `.gitignore`, negation and directory exclusions) using local processing, never the Git executable. If ignored or uncertain, warn and skip archival without writing. Never force-track ignored content.
2. Write the file (create the directory if needed) with YAML frontmatter `title`, `date`, `input_shape: concept`, `subject`, and the teaching content. If the file already exists from a prior run, overwrite it.
3. Read the full guide and runtime history and follow all source excerpts and standards in `commit-and-push.md`. Dynamically compose a message describing the taught concepts, with no fixed prefix. Commit only those files using `jj commit -m "<message composed from the standards above>" <explainer-paths>`. Re-apply the **Project publishing gate**, move only the owned head bookmark to the verified completed revision, and push with `jj git push --remote <verified-remote> --bookmark <head-branch>`. If the files are unchanged and already committed, keep the link and continue.
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

Clean exact-head alignment and starting/re-arming authorized monitoring need no further approval. Verify the head repository, bookmark, remote and exact pushed commit first; empty `@` directly above it is already aligned. Otherwise only a clean, conflict-free workspace may use `jj new <verified-pushed-head>`. Inspect tracked, ignored and untracked content and preserve unrelated work. Dirty/conflicted state, uncertain targets, denied permission or unknown push authority takes the existing safe stop/decision path, never reset/discard or a guessed head. Declining an optional description rewrite never blocks this handoff. Respect monitoring opt-outs, draft boundaries, final-merge and scope-expansion decisions.

After a stack submit, hand off the bottom open non-draft PR with the derived `posture:stack-ready`, or `posture:stack-land` when the user explicitly asked to land, plus stack-wide scope when a pipeline submitted the stack. Report that ownership transfer so an outer orchestrator does not start a second bare babysit on the current branch.

**Success** = `ce-babysit-pr` owns the monitoring lifecycle. Load and follow its instructions before choosing the monitoring mode. If you are running it in this session, continue until its stop condition permits a final report. In `mode:pipeline`, wait for its pipeline stop and return the structured result. Before reporting success, render every returned typed `needs-human` residual unchanged under `## Needs your decision` and pass the same objects up to the top-level coordinator. `babysit:off` disables only new monitoring; it does not suppress a typed residual already known to this run or supplied by its caller.

In `mode:pipeline`, the last thing this skill writes is its return to the caller. It ends this skill, not the turn. The caller runs in this same session, and its next step follows the return. That return is the structured result after this run waited for `ce-babysit-pr`, or the report already written when the handoff does not fire.

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

The body **must** be written under the target workspace's ignored local `.tmp/` and passed via `--body-file <path>`. Follow `context.md` even in description-update mode: run from the absolute target root and export `GIT_DIR=$(jj git root)` for every scoped `gh` call. Never use `--body-file -`, stdin pipes, heredoc-to-stdin, or `--body "$(cat ...)"` — wrappers can silently produce an empty body while returning success.

```bash
mkdir -p "$workspace_root/.tmp"
BODY_FILE=$(mktemp "$workspace_root/.tmp/pr-body.XXXXXX")
cat > "$BODY_FILE" <<'__PR_BODY_END__'
<the composed body markdown goes here, verbatim>
__PR_BODY_END__
```

The quoted sentinel keeps `$VAR`, backticks, and any literal `EOF` inside the body from being expanded.

For `<TITLE>`: substitute verbatim. If it contains `"`, `` ` ``, `$`, or `\`, escape them or switch to single quotes.

```bash
gh pr create --title "<TITLE>" --body-file "$BODY_FILE"   # new PR
gh pr edit   --title "<TITLE>" --body-file "$BODY_FILE"   # existing PR
```
