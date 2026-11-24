# Applying the PR, reporting, and the babysit handoff

**Description-only mode** — print the title and body. Stop unless the user asks to apply.

**Stack mode** — follow the Submit section of `references/stack-submit.md` for both new and existing layers. After verifying the submitted stack, report the bottom open non-draft PR URL and continue to the babysit handoff.

**New single PR** — immediately before creating, repeat the open-PR lookup and exact head match in `references/context.md`. If a match appeared, switch to the existing-PR path; a nonzero or ambiguous response blocks creation. Otherwise apply via `gh pr create` below. Use a draft only when the user or project asks for one; verification this run could not do belongs in the body. Report the URL.

**Existing single PR** — Step 3 already pushed any new commits. Report the URL. If the invocation explicitly requests applying a rewrite, run Step 4 and apply it without asking again. Otherwise, an optional interactive rewrite requires a preview and affirmative approval before editing: show the proposed title, the first two sentences, and the body line count. If declined or suppressed by `mode:pipeline`, keep the current description, skip archival, and continue to any otherwise authorized handoff. Do not combine preview approval with workspace alignment or monitoring, or make the rewrite a prerequisite for either.

**Apply only an authorized rewrite.** In description update mode, an explicit apply request is approval; compare the proposed title and body with the current PR and skip a no-op. Re-verify the exact PR and preserve existing issue links before editing via `gh pr edit`; report the URL. A mere draft request returns text without editing. A run already authorized to babysit a PR refreshes stale description facts from its verified run results in `ce-babysit-pr` without a new preview or yes/no. That maintenance is not a standalone rewrite; preserve unrelated user-authored text and existing issue links.

**Explainer archival** — runs only in the full workflow, when all of these hold: `pr_teaching_archive` is on, the composed body has a `## New concepts` section, and applying it is authorized (a new-PR create, or an authorized existing-PR rewrite). A declined rewrite skips archival entirely, so no unlinked doc commit is left behind. Resolve every path from the absolute JJ workspace root gathered in Context. With two taught concepts, write one file per concept and include both in the single commit. Resolve `<root>` first:

<!-- ce-docs-root:start -->
**Resolve the artifact root `<root>` before composing any artifact path.**

- **Read** `docs_root` from `<repo-root>/.rocketclaw/config.yaml` only (`<repo-root>` = `jj workspace root`). Do not read it from `config.local.yaml`. Unset -> `<root>` is `docs`, exactly as before.
- **Validate** a set value: a repo-relative directory whose real, symlink-resolved path stays inside the workspace and is neither its root nor under `.jj/` or `.git/`. Otherwise stop with an error naming `docs_root` and the value -- never fall back to `docs`.
- **Use** `<root>` as the sole artifact location: compose each path as `<root>/<subdir>` with this skill's own subdirectory, create the directory only after the ignore check below, and never also read `docs`.
<!-- ce-docs-root:end -->

Then run these steps, in order, immediately before the `gh` call:

1. Before writing, verify each prospective file's real path stays within the selected artifact root. Evaluate it with a local gitignore-compatible matcher using JJ's effective [ignore sources and precedence](https://docs.jj-vcs.dev/latest/working-copy/#ignored-files), including parent-directory exclusions, negation, and whether the path is already tracked. Check that a new file is eligible for snapshot under `snapshot.auto-track` too. If any path is ignored or its status cannot be proven, warn and skip archival entirely, writing nothing. Never force-track it.
2. Write the file (create the directory if needed) with YAML frontmatter `title`, `date`, `input_shape: concept`, `subject`, and the teaching content. If this was already archived, update only a verified prior explainer with no unrelated edits. Never overwrite an unowned file.
3. Follow `references/commit-and-push.md`, including its full Go and recent JJ history guidance, to compose a description identifying the archived concepts. Commit only the explainer path(s) using its exact path-scoped `jj commit`; keep excluded or unrelated work out. If those paths have no changes and the documents are already on the verified pushed head, keep the links without creating an empty change. Otherwise re-apply the **Project publishing gate** to the resulting commit state and publish only the verified feature bookmark.
4. Add a head-branch blob URL for each doc into the `## New concepts` section before applying. Build the URL for the repo's actual host — for example `gh browse -n -b <head-branch> -- <path>` prints the link on whatever host `gh` targets, GitHub Enterprise included. Do not hardcode `github.com`, or the link 404s on GHE.

If the doc write, commit, or push fails, warn and continue to PR creation without the link. Never leave the flow stopped between the commit and the PR.

**User-runnable invocation rendering.** For the output handoffs below, default to `/ce-explain <name>`. Use `$ce-explain <name>` only when the active host is Codex or explicitly documents dollar-prefixed skill invocation. Render only the invocation as inline code and output one form only.

**Concept trailer** — when a body applied by this run contains a `## New concepts` section, print one line after the PR URL in every mode: `New concepts: <name>[, <name>]`. In interactive full-workflow runs follow it with one line per taught concept telling the user to invoke `ce-explain <name>` using the rendering rule above. Print no trailer when this run applied no body — including a rewrite that was declined or that pipeline mode defaulted to no — or when no PR exists.

**Resolve the standing opt-out before applying the handoff rule below.** Read `auto_babysit` by the rule here, at the handoff. A config read from an earlier step does not carry over: a run that reaches the handoff without having read the key hands off against the user's standing choice, and a compacted run is the ordinary way that happens.

<!-- ce-config-layers:start -->
**Resolve ordinary YAML keys from the two repo files.**

- **Read** `<repo-root>/.rocketclaw/config.local.yaml`, then `config.yaml` in the same directory (`<repo-root>` = `jj workspace root`). Missing files are skipped. Gitignore does not change resolution.
- **Win** with the first active (non-commented) value. For scalars, empty is unset; an invalid value continues to the next layer, then the skill default. For lists and maps, a present key — including an empty list or map — replaces the whole key.
- **Do not** use this rule for `docs_root` — that key is `config.yaml` only.
<!-- ce-config-layers:end -->

Without a per-run `babysit:` token, the winning active value `false` opts out; a missing key or any other value leaves the default **on**. An opt-out is a **successful terminal for this run**, not a blocked one — report the PR URL and the reason babysit was skipped.

**Babysit handoff — default on; completion gate.** After a newly-created PR, a successful stack submit, or new commits on an existing open PR, this run is not done until `ce-babysit-pr` owns follow-on or an explicit skip below applies. Reporting the PR URL alone is not success. Announce the automatic handoff in one non-blocking line, then invoke the skill through the host's normal skill-invocation mechanism; never ask yes/no. A request for the PR link, a report back, or no merge is not a skip: `ce-babysit-pr` never merges unless asked to land a stack.

After resolving eligibility below and before handing over a writable checkout, verify the exact pushed commit against the PR's head repository, bookmark, and remote. A clean checkout at that head, including an empty `@` directly above it, is already aligned. When safe to move, align a clean JJ checkout to that exact commit with `jj new <verified-head-id>` from the absolute workspace root; no extra approval is needed for alignment or to start/re-arm authorized monitoring. Do not switch away from an unpushed local change, or overwrite unrelated tracked, ignored, or untracked files. On dirty/conflicted state, uncertain identity or push authority, a collision, or a permission denial, leave the workspace as found and report the blocker through the callee's safe decision path. Do not reset, discard, guess, or work around denied permissions.

After a stack submit, pass the verified stack identity and topology and the bottom open non-draft PR with the derived `posture:stack-ready`, or `posture:stack-land` when the user explicitly asked to land, plus stack-wide scope when a pipeline submitted the stack. Report that ownership transfer so an outer orchestrator does not start a second bare babysit on the current branch.

**Success** = `ce-babysit-pr` owns the monitoring lifecycle. Load and follow its instructions before choosing the monitoring mode. If you are running it in this session, continue until its stop condition permits a final report, ending the turn only while its armed wake source will bring this agent back. In `mode:pipeline`, wait for its pipeline stop and return the structured result. Before reporting success, render every returned typed `needs-human` residual unchanged under `## Needs your decision` and pass the same objects up to the top-level coordinator. `babysit:off` disables only new monitoring; it does not suppress a typed residual already known to this run or supplied by its caller.

In `mode:pipeline`, the last thing this skill writes is its return to the caller. It ends this skill, not the turn. The caller runs in this same session, and its next step follows the return. That return is the structured result after this run waited for `ce-babysit-pr`, or the report already written when the handoff does not fire.

Never start babysit mechanics yourself: do not take over its snapshots, arm a watcher, or reconstruct the loop. Never substitute `ci-watcher`, `gh pr checks --watch`, a host's own PR-watch tool on its own, ad-hoc polls, or a promise to babysit later. `ce-babysit-pr` decides how it gets woken, including through a host's tool when host instructions dictate PR waits. **Handoff blocked:** if the skill cannot be loaded or started, stop and report the failure. Do not invent a parallel or narrower watch.

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

The body **must** be written to a temp file under `$workspace_root/.tmp/` and passed via `--body-file <path>`. Verify this scratch location is ignored and resolves inside the workspace; create it if needed. If unavailable, report the blocker; do not use an OS-global fallback. Never use `--body-file -`, stdin pipes, heredoc-to-stdin, or `--body "$(cat ...)"` — wrappers and stdin handling can silently produce an empty PR body while `gh` still exits 0 and returns a URL.

```bash
BODY_FILE=$(mktemp "$workspace_root/.tmp/pr-body.XXXXXX") && cat >> "$BODY_FILE" <<'__PR_BODY_END__'
<the composed body markdown goes here, verbatim>
__PR_BODY_END__
```

The quoted sentinel keeps `$VAR`, backticks, and any literal `EOF` inside the body from being expanded.

Pass the title as a literal argument. Run each example with the scoped `gh` environment from Context; always name the verified base repository and exact head for create, or the verified PR URL for edit.

```bash
gh pr create -R "$base_repo" --base "$base_branch" --head "$head_arg" --title "$title" --body-file "$BODY_FILE"
gh pr edit "$pr_url" --title "$title" --body-file "$BODY_FILE"
```

For a fork use the verified `<owner>:<bookmark>` for `--head` at create time, but pass only the bookmark to `pr list --head`. **Screenshots.** When the body references local images from `references/visual-evidence.md`, create the body file in the images' directory under `$workspace_root/.tmp/` so each `./<name>.png` reference resolves: `BODY_FILE=$(mktemp "<images-dir>/pr-body.XXXXXX")`. Add one `--attach "<images-dir>/<name>.png#<alt text>"` per image. `gh` uploads each file and rewrites the matching reference to its GitHub URL.

A file `gh` rejects before uploading, such as a missing file or an image over 10 MB, makes it exit non-zero without creating or editing the PR; stderr names the file. An upload that fails after others succeeded can still leave the PR created or updated, and `gh` then still prints its URL. So whatever the exit status, do not run `gh pr create` a second time. Find the PR from the printed URL, or the way the new-PR re-check above does when none was printed, and read its body with `gh pr view "<pr-url>" --json body`. If any image reference there still points at a local path, edit that PR's body on GitHub to remove those references and keep everything else. If the create or edit did not apply, apply the body again without the images that failed. Either way, report which images did not upload.
