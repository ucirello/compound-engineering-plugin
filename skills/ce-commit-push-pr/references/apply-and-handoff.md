# Applying the PR, reporting, and the babysit handoff

**Description-only mode** — print the title and body. Stop unless the user asks to apply.

**New PR** (full workflow, no existing PR from Step 1, resolve branch and PR state) — if **Stack mode** is active, follow the Submit section of `references/stack-submit.md` instead of `gh pr create`; then report the bottom open non-draft PR URL and continue to the babysit handoff. Otherwise, immediately before creating, **always** re-run `gh pr list --head <branch> --state open --json number,url,isDraft,headRefName,headRepositoryOwner` (branch name only; target the base repo on a fork, per Context). This catches a PR that appeared since Step 1, or one the Step 1 check missed because it came back **unknown**, so you do not open a duplicate. If the list now shows a PR whose `headRepositoryOwner` and `headRefName` match the current head, switch to the existing-PR path. When several forks match, pick by head owner as in Step 1 rather than assuming index 0. If this re-check itself exits non-zero, resolve `gh auth status` or connectivity before creating; do not assume no PR exists. Otherwise apply per "Applying via gh" below using `gh pr create`. Open it as a draft only when the user or the project asks for one; verification this run could not do belongs in the body, not in draft status. Report the URL.

**Existing PR** (full workflow, found in Step 1) — stack mode follows `stack-submit.md`. Otherwise new commits already reach the PR from Step 3. Authorized babysitting includes factual description maintenance and verified clean-head alignment without redundant approval. Preserve user prose, links and unrelated work, respect edit/push permissions and watch opt-outs. Empty `@` above the verified PR head is aligned; dirty/conflicted/uncertain heads stop safely. A standalone optional editorial rewrite still requires approval; offer it independently of monitoring.

- **No** — skip the description rewrite and continue to the babysit handoff rule below.
- **Yes** — run Step 4 (compose the PR title and body) if not already done, then preview and apply (see below).

**Description-only requests remain draft-only** unless the user explicitly asks to apply, even when phrased as a rewrite. For an explicit description update or approved optional rewrite, preview title/body and skip identical results. Confirm optional editorial application when not already authorized. Authorized babysit factual maintenance needs no redundant ask. If a rewrite is declined, do not apply it, but continue authorized monitoring; declining rewriting never cancels babysit. Respect a separate explicit monitoring decline.

**Explainer archival** — runs only in the full workflow, when all of these hold: `pr_teaching_archive` is on, the composed body has a `## New concepts` section, and the apply was confirmed (a new-PR create, or an existing-PR rewrite the user accepted). A declined rewrite skips archival entirely, so no unlinked doc commit is left behind. Resolve every path from the repo root gathered in Context, never from the CWD. With two taught concepts, write one file per concept and stage both in the single commit. Resolve `<root>` first:

<!-- ce-docs-root:start -->
**Resolve the RocketClaw artifact root `<root>` before composing any artifact path.**

- **Read** `docs_root` from `<repo-root>/.rocketclaw/config.yaml` only (`<repo-root>` = `jj root`). Do not read it from `config.local.yaml`. Unset -> `<root>` is `docs`.
- **Validate** a set value: a repo-relative directory whose real, symlink-resolved path stays inside the repo and is neither the repo root nor under `.git/`. Otherwise stop with an error naming `docs_root` and the value -- never fall back to `docs`.
- **Use** `<root>` as the sole artifact location: create it if absent, compose each path as `<root>/<subdir>` with this skill's own subdirectory, and never also read `docs`.
<!-- ce-docs-root:end -->

Then run these steps, in order, immediately before the `gh` call:

1. Check tracked membership with `jj --ignore-working-copy file list "<planned-repo-relative-path>"` from the absolute workspace root before writing the planned path. This lists tracked files, not ignored files. Inspect applicable ignore policy separately; the retained `ce-setup/scripts/check-ignore.py` may be called as `python3 "<absolute-ce-setup-skill-path>/scripts/check-ignore.py" "$workspace_root" "<planned-repo-relative-path>"` from that root. Exit 0 means its conservative parser found ignore coverage; exit 1 is unknown/not proven ignored (including already-tracked paths), not proof that archival is safe. Manually verify ancestor/nested rules, negations and repository/global exclusions when needed. If ignored or uncertain, warn and skip archival without forcing tracking. Never use a Git fallback.
2. Write the file (create the directory if needed) with YAML frontmatter `title`, `date`, `input_shape: concept`, `subject`, and the teaching content. If the file already exists from a prior run, overwrite it.
3. Read `commit-and-push.md`'s full runtime Go/history contract; compose a repository-style description of the teaching outcome, not a fixed message. Commit only those explicit paths using JJ and verify the result. Reapply the **Project publishing gate** before JJ publication. An unchanged already-committed document keeps its link without a duplicate commit.
4. Add a head-branch blob URL for each doc into the `## New concepts` section before applying. Build the URL for the repo's actual host — for example `gh browse -n -b <head-branch> -- <path>` prints the link on whatever host `gh` targets, GitHub Enterprise included. Do not hardcode `github.com`, or the link 404s on GHE.

If the doc write, commit, or push fails, warn and continue to PR creation without the link. Never leave the flow stopped between the commit and the PR.

**User-runnable invocation rendering.** Use `/ce-explain <name>` through the host's documented skill invocation; output one supported form only.

**Concept trailer** — when a body applied by this run contains a `## New concepts` section, print one line after the PR URL in every mode: `New concepts: <name>[, <name>]`. In interactive full-workflow runs follow it with one line per taught concept telling the user to invoke `ce-explain <name>` using the rendering rule above. Print no trailer when this run applied no body — including a rewrite that was declined or that pipeline mode defaulted to no — or when no PR exists.

**Resolve the standing opt-out before applying the handoff rule below.** Read `auto_babysit` by the rule here, at the handoff. A config read from an earlier step does not carry over: a run that reaches the handoff without having read the key hands off against the user's standing choice, and a compacted run is the ordinary way that happens.

<!-- ce-config-layers:start -->
**Resolve ordinary RocketClaw yaml keys from the two repo files.**

- **Read** `<repo-root>/.rocketclaw/config.local.yaml`, then `config.yaml` (`<repo-root>` = `jj root`). Missing files are skipped. Ignore rules do not change resolution.
- **Win** with the first active (non-commented) value. For scalars, empty is unset; an invalid value continues to the next layer, then the skill default. For lists and maps, a present key — including an empty list or map — replaces the whole key.
- **Do not** use this rule for `docs_root` — that key is `config.yaml` only.
<!-- ce-config-layers:end -->

Babysit is off only when the winning active value is exactly `false`; a missing key or any other value leaves the default **on**. A handoff the user opted out of is a **successful terminal for this run**, not a blocked one — report the PR URL, say in one line that babysit was skipped by standing config, and stop.

**Babysit handoff — default on; completion gate.** After a newly-created PR, a successful stack submit, or new commits on an existing open PR, this run is not done until `ce-babysit-pr` owns follow-on or an explicit skip below applies. Reporting the PR URL alone is not success. Announce the automatic handoff in one non-blocking line, then invoke the skill through the host's normal skill-invocation mechanism; never ask yes/no. A request for the PR link, a report back, or no merge is not a skip: `ce-babysit-pr` never merges unless asked to land a stack.

After a stack submit, hand off the bottom open non-draft PR with the derived `posture:stack-ready`, or `posture:stack-land` when the user explicitly asked to land, plus stack-wide scope when a pipeline submitted the stack. Report that ownership transfer so an outer orchestrator does not start a second bare babysit on the current branch.

**Success** = `ce-babysit-pr` owns the monitoring lifecycle. Load and follow its instructions before choosing the monitoring mode. If you are running it in this session, continue until its stop condition permits a final report, ending the turn only while its armed wake source will bring this agent back. In `mode:pipeline`, wait for its pipeline stop and return the structured result. Before reporting success, render every returned typed `needs-human` residual unchanged under `## Needs your decision` and pass the same objects up to the top-level coordinator. `babysit:off` disables only new monitoring; it does not suppress a typed residual already known to this run or supplied by its caller.

In `mode:pipeline`, the last thing this skill writes is its return to the caller. It ends this skill, not the turn. The caller runs in this same session, and its next step follows the return. That return is the structured result after this run waited for `ce-babysit-pr`, or the report already written when the handoff does not fire.

Never start babysit mechanics yourself: do not run `pr-snapshot`, arm a watcher, or reconstruct the loop. Never substitute `ci-watcher`, `gh pr checks --watch`, a host's own PR-watch tool on its own, ad-hoc polls, or a promise to babysit later. `ce-babysit-pr` decides how it gets woken, including through a host's tool when host instructions dictate PR waits. **Handoff blocked:** if the skill cannot be loaded or started, stop and report the failure. Do not invent a parallel or narrower watch.

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
mkdir -p "$workspace_root/.tmp"
BODY_FILE=$(mktemp "$workspace_root/.tmp/ce-pr-body.XXXXXX")
cat >> "$BODY_FILE" <<'__CE_PR_BODY_END__'
<the composed body markdown goes here, verbatim>
__CE_PR_BODY_END__
```

The quoted sentinel keeps `$VAR`, backticks, and any literal `EOF` inside the body from being expanded.

For `<TITLE>`: substitute verbatim. If it contains `"`, `` ` ``, `$`, or `\`, escape them or switch to single quotes.

```bash
gh pr create --title "<TITLE>" --body-file "$BODY_FILE"   # new PR
gh pr edit   --title "<TITLE>" --body-file "$BODY_FILE"   # existing PR
```

**Screenshots.** When the body references local images from `references/visual-evidence.md`, create the body file in the images' directory so each `./<name>.png` reference resolves: `BODY_FILE=$(mktemp "<images-dir>/ce-pr-body.XXXXXX")`. Add one `--attach "<images-dir>/<name>.png#<alt text>"` per image to the create or edit command. `gh` uploads each file and rewrites the matching reference to its GitHub URL.

A file `gh` rejects before uploading, such as a missing file or an image over 10 MB, makes it exit non-zero without creating or editing the PR; stderr names the file. An upload that fails after others succeeded can still leave the PR created or updated, and `gh` then still prints its URL. So whatever the exit status, do not run `gh pr create` a second time. Find the PR from the printed URL, or the way the new-PR re-check above does when none was printed, and read its body with `gh pr view "<pr-url>" --json body`. If any image reference there still points at a local path, edit that PR's body on GitHub to remove those references and keep everything else. If the create or edit did not apply, apply the body again without the images that failed. Either way, report which images did not upload.
