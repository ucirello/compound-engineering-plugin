# Applying the PR, reporting, and the babysit handoff

**Description-only mode** — print the title and body. Do not edit the PR, align the workspace, or start babysitting.

**New PR** (full workflow) — if **Stack mode** is active, follow the Submit section of `references/stack-submit.md`; then report the bottom open non-draft PR URL and continue to handoff. Otherwise, immediately before creating, **always** re-run the base-repo `gh pr list` probe in Context with the verified branch name only. A unique exact head repository/owner/branch match takes the existing-PR path, even if it appeared since Step 1; recompose against that PR if rewriting. Only exit-0 `[]` permits creation; a failed or ambiguous check blocks. Verify the exact published head and intended base again. Apply via `gh pr create` below. Open it as a draft only when the user or project asks; verification this run could not do belongs in the body, not in draft status. Report the URL.

**Existing PR** (full workflow) — if **Stack mode** is active, still follow the Submit section of `references/stack-submit.md` so the remaining stack layers submit or sync; report the bottom open non-draft PR URL and continue to handoff. Otherwise the intended commits are already on the PR. Report the URL. Keep the existing description by default in pipeline mode. Interactively, preview the optional rewrite and ask one approval question unless the user explicitly asked to apply the rewrite. Keep this decision separate from alignment or monitoring.

- **No** — keep the current description, skip explainer archival, and continue to the otherwise authorized babysit handoff.
- **Yes** (or explicit apply intent) — apply as below. The preview approval covers the edit; do not ask a second time about the same rewrite.

**Description update or optional existing-PR rewrite** — compare the proposal to the current title/body first; identical content needs no edit. Preview the title, opening summary and body length. If the user explicitly authorized the edit, apply via `gh pr edit` without another ask. Otherwise ask for approval interactively; in `mode:pipeline`, return the proposal without editing. Neither a caller's mode token nor a suppressed question grants apply intent. A skipped or declined rewrite leaves the PR description intact and does not block any otherwise authorized handoff. When applying, preserve existing issue links and required content; re-read the current body and exact head and reconcile concurrent edits or stop rather than overwriting them.

**Authorized babysitting is separate.** A factual refresh of stale claims or validation with verified results from the authorized babysit run is part of `ce-babysit-pr`. It preserves unrelated user-authored text and existing issue links and applies without a new yes/no or preview approval. Do not send it through this optional rewrite path, expand scope, or treat it as permission to merge.

**Explainer archival** — runs only in the full workflow, when all of these hold: `pr_teaching_archive` is on, the composed body has a `## New concepts` section, and applying it is authorized (a new PR or an authorized existing-PR rewrite). A declined rewrite skips archival entirely. Work from the absolute JJ workspace root gathered in Context. With two concepts, write one file per concept and include both in the single commit. Resolve `<root>` first:

<!-- ce-docs-root:start -->
**Resolve the artifact root `<root>` before composing any artifact path.**

- **Read** `docs_root` from `<repo-root>/.rocketclaw/config.yaml` only. Do not read it from `config.local.yaml`. Unset -> `<root>` is `docs`.
- **Validate** a set value: a workspace-relative directory whose real, symlink-resolved path stays inside the workspace and is neither the workspace root nor under `.jj/` or `.git/`. Otherwise stop with an error naming `docs_root` and the value -- never fall back to `docs`.
- **Use** `<root>` as the sole artifact location: create it if absent, compose each path as `<root>/<subdir>` with this skill's own subdirectory, and never also read `docs`.
<!-- ce-docs-root:end -->

Then run these steps, in order, immediately before the `gh` call:

1. Before writing, evaluate the proposed paths against the [ignore sources JJ uses](https://docs.jj-vcs.dev/latest/working-copy/#ignored-files): the applicable ancestor `.gitignore` files, global excludes and repository `info/exclude`. Use a local Git-format ignore matcher that handles anchored paths, directories, negations and ignored parents, without launching Git. If any path is ignored or the matching rules cannot be established reliably, warn and skip archival without writing. Never bypass ignore rules.
2. Verify the working-copy change is directly above the exact published feature tip and has no conflicts or unrelated edits at the archive paths. Write each file with YAML frontmatter `title`, `date`, `input_shape: concept`, `subject`, and the teaching content. Replace a prior generated explainer only when it is verified as such and has no unrelated edits.
3. Follow the **Compose each JJ change description** section of `references/commit-and-push.md`, including the full Go guide and verified history sample. Describe the archived teaching and its concepts in the repository's style. If an intended new file was not auto-tracked, use `jj file track -- <explainer-paths>` without overriding ignore checks. Commit only the explainer paths with `jj commit -m "<message composed from the standards above>" -- <explainer-paths>`. Re-run the exact-state **Project publishing gate**, verify and move only the feature bookmark to that committed tip, and push through the same reference's publish procedure. If the intended doc content was already committed at the exact published head, keep the link and do not create an empty commit.
4. Add a head-branch blob URL for each doc into the `## New concepts` section before applying. Build the URL for the repo's actual host — for example `gh browse -n -b <head-branch> -- <path>` prints the link on whatever host `gh` targets, GitHub Enterprise included. Do not hardcode `github.com`, or the link 404s on GHE.

If the doc write, commit, or push fails, warn and continue to PR creation without the link. Never leave the flow stopped between the commit and the PR.

**User-runnable invocation rendering.** For the output handoffs below, default to `/ce-explain <name>`. Use `$ce-explain <name>` only when the active host is Codex or explicitly documents dollar-prefixed skill invocation. Render only the invocation as inline code and output one form only.

**Concept trailer** — when a body applied by this run contains a `## New concepts` section, print one line after the PR URL in every mode: `New concepts: <name>[, <name>]`. In interactive full-workflow runs follow it with one line per taught concept telling the user to invoke `ce-explain <name>` using the rendering rule above. Print no trailer when this run applied no body — including a rewrite that was declined or that pipeline mode defaulted to no — or when no PR exists.

**Resolve the standing opt-out before applying the handoff rule below.** Read `auto_babysit` by the rule here, at the handoff. A config read from an earlier step does not carry over: a run that reaches the handoff without having read the key hands off against the user's standing choice, and a compacted run is the ordinary way that happens.

<!-- ce-config-layers:start -->
**Resolve ordinary YAML keys from the two repo files.**

- **Read** `<repo-root>/.rocketclaw/config.local.yaml`, then `<repo-root>/.rocketclaw/config.yaml`. Missing files are skipped. Ignore rules do not change resolution.
- **Win** with the first active (non-commented) value. For scalars, empty is unset; an invalid value continues to the next layer, then the skill default. For lists and maps, a present key — including an empty list or map — replaces the whole key.
- **Do not** use this rule for `docs_root` — that key is `config.yaml` only.
<!-- ce-config-layers:end -->

`auto_babysit` defaults **on**; a winning active value of exactly `false` opts out of automatic handoff. When the opt-out applies, report the PR URL and say babysit was skipped by standing config. This is a **successful terminal for this run**, not a blocker. Preserve known `needs-human` residuals.

**Babysit handoff — default on; completion gate.** After a newly-created PR, a successful stack submit, or new commits on an existing open PR, this run is not done until `ce-babysit-pr` owns follow-on or an explicit skip below applies. Reporting the PR URL alone is not success. Announce the automatic handoff in one non-blocking line, then invoke the skill through the host's normal skill-invocation mechanism; never ask yes/no. A request for the PR link, a report back, or no merge is not a skip: `ce-babysit-pr` never merges unless asked to land a stack.

After a stack submit, hand off the bottom open non-draft PR with the derived `posture:stack-ready`, or `posture:stack-land` when the user explicitly asked to land, plus stack-wide scope when a pipeline submitted the stack. Pass the ordered PR URLs and verified stack identity. Report that ownership transfer so an outer orchestrator does not start a second bare babysit on the current bookmark. Land intent does not bypass final merge approval.

**Exact pushed-head alignment.** In the actual monitoring workspace, verify the PR's head repository/owner, branch, exact `headRefOid`, the configured head remote and matching fetched remote bookmark, and push authority. Stop safely and report if any of these are ambiguous, denied or unknown. After the callee resolves watch-mode boundaries, an empty, conflict-free `@` directly above that single verified head is already aligned; do not create another change. A clean workspace may align to that exact head with `jj new "<verified-head-oid>"` without another approval when the workflow authorizes it. First verify the old tip and any bookmarks or nonempty draft descriptions will be retained and inspect tracked, conflicted, ignored and untracked content for collision risk. Afterwards reverify the new working copy and exact parent before arming. If dirty, conflicted, or unsafe, leave it intact and report the blocker; no reset, discard, or guessed target. Starting and re-arming authorized monitoring do not require another yes/no; use only the callee's permitted watch lifecycle and respect opt-outs.

**Success** = `ce-babysit-pr` owns the monitoring lifecycle. Load and follow its instructions before choosing the monitoring mode. If you are running it in this session, continue until its stop condition permits a final report, ending the turn only while its armed wake source will bring this agent back. In `mode:pipeline`, wait for its pipeline stop and return the structured result. Before reporting success, render every returned typed `needs-human` residual unchanged under `## Needs your decision` and pass the same objects up to the top-level coordinator. `babysit:off` disables only new monitoring; it does not suppress a typed residual already known to this run or supplied by its caller.

In `mode:pipeline`, the last thing this skill writes is its return to the caller. It ends this skill, not the turn. The caller runs in this same session, and its next step follows the return. That return is the structured result after this run waited for `ce-babysit-pr`, or the report already written when the handoff does not fire.

Never start babysit mechanics yourself: do not run `pr-snapshot`, arm a watcher, or reconstruct the loop. Never substitute `ci-watcher`, `gh pr checks --watch`, a host's own PR-watch tool on its own, ad-hoc polls, or a promise to babysit later. `ce-babysit-pr` decides how it gets woken, including through a host's tool when host instructions dictate PR waits. **Handoff blocked:** if the skill cannot be loaded or started, stop and report the failure. Do not invent a parallel or narrower watch.

`babysit:off` skips new monitoring in this run. `babysit:continuous` and `babysit:checkpoint` select a mode only where monitoring is authorized. Override a standing or per-run opt-out only when the user explicitly authorizes monitoring despite that opt-out for this PR and scope. A token silently supplied by an orchestrating caller, a stack posture, or a request to ship does not override it. If the user separately authorizes a bounded watch, pass only its PR, mode, scope and stop boundary to `ce-babysit-pr`; do not turn it into an automatic or broader handoff. Honor the callee's watch boundaries and actual tool permissions.

A draft-only stack submit is a hard residual before babysit when babysit is on.

**Do not fire (auto-detected, no flag needed):** the automatic handoff does not start in any of these cases.
- `mode:pipeline` **except** when this run completed a stack-mode submit (then hand off with the derived posture as above).
- Description-only or description-update mode.
- No PR created or updated this run.
- A non-GitHub host.
- A **draft PR** this run created or updated. A draft is the author's not-ready signal: announce the skip, and say `ce-babysit-pr` can start once the PR is ready. If the user separately authorizes watching this draft, pass the authorized `watch` or `checkpoint` mode so the callee enforces its draft boundary. This exception does not itself override a standing opt-out; a caller token alone does not authorize it.
- **A head branch you cannot push to.** Fork PRs are drivable when head push rights are verified: babysit reads the **base** repo and pushes authorized fixes to the **head** repo. Do not start a write-capable handoff on unknown authority; report it as blocked, not as an opt-out.
**Soft-degrade (after successful handoff only):** `ce-babysit-pr` decides whether checkpoint mode applies and owns its report and resume invocation. Checkpoint is not a substitute for a failed handoff.

## Applying via gh

The body **must** be written to a temp file and passed via `--body-file <path>`. Never use `--body-file -`, stdin pipes, heredoc-to-stdin, or `--body "$(cat ...)"` — wrappers and stdin handling can silently produce an empty PR body while `gh` still exits 0 and returns a URL.

Write the verbatim body to a uniquely created run directory under `<workspace-root>/.tmp/` (local `.tmp/` outside JJ). Confirm the directory is ignored in JJ. For example, after verifying the local parent path, `mktemp -d "$workspace_root/.tmp/pr-body.XXXXXX"` creates a run directory; use its absolute `body.md` as `BODY_FILE`. Put captured stderr and any fallback files under the same local `.tmp/` namespace. Use a file-write tool or a quoted heredoc to keep `$VAR` and backticks literal.

For `<TITLE>`: substitute verbatim. If it contains `"`, `` ` ``, `$`, or `\`, escape them or switch to single quotes.

```bash
gh pr create -R "<base-repo>" --base "<verified-base-branch>" --head "<verified-head-selector>" --title "<TITLE>" --body-file "$BODY_FILE"
gh pr edit "<verified-pr-url>" --title "<TITLE>" --body-file "$BODY_FILE"
```

Use the workspace and `GIT_DIR` rules from Context. For creation, `--head` is the verified branch for same-repo PRs or a supported `owner:branch` selector for forks (unlike `gh pr list`, which takes the branch only). If the fork selector is unsupported, stop rather than creating from a different head. Omit `--title` when an authorized update changes only the body.

**Screenshots.** When the body references local images from `references/visual-evidence.md`, write `BODY_FILE` in the ignored images directory so each `./<name>.png` reference resolves. Add one `--attach "<images-dir>/<name>.png#<alt text>"` per image to the create or edit command. `gh` uploads each file and rewrites the matching reference to its GitHub URL.

A file `gh` rejects before uploading, such as a missing file or an image over 10 MB, makes it exit non-zero without creating or editing the PR; stderr names the file. An upload that fails after others succeeded can still leave the PR created or updated, and `gh` then still prints its URL. So whatever the exit status, do not run `gh pr create` a second time. Find the PR from the printed URL, or the way the new-PR re-check above does when none was printed, and read its body with `gh pr view "<pr-url>" --json body`. If any image reference there still points at a local path, edit that PR's body on GitHub to remove those references and keep everything else. If the create or edit did not apply, apply the body again without the images that failed. Either way, report which images did not upload.
