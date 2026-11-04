# Applying the PR, reporting, and the babysit handoff

**Description-only mode** — print the title and body. Stop unless the user asks to apply.

**New PR** (full workflow, no existing PR from Step 1, resolve branch and PR state) — if **Stack mode** is active, follow the Submit section of `references/stack-submit.md` instead of `gh pr create`; then report the bottom open non-draft PR URL and continue to the babysit handoff. Otherwise, immediately before creating, **always** re-run `gh pr list --head <branch> --state open --json number,url,isDraft,headRefName,headRepositoryOwner` (branch name only; target the base repo on a fork, per Context). This catches a PR that appeared since Step 1, or one the Step 1 check missed because it came back **unknown**, so you do not open a duplicate. If the list now shows a PR whose `headRepositoryOwner` and `headRefName` match the current head, switch to the existing-PR path. When several forks match, pick by head owner as in Step 1 rather than assuming index 0. If this re-check itself exits non-zero, resolve `gh auth status` or connectivity before creating; do not assume no PR exists. Otherwise apply per "Applying via gh" below using `gh pr create`. Open it as a draft only when the user or the project asks for one; verification this run could not do belongs in the body, not in draft status. Report the URL.

**Existing PR** (full workflow, found in Step 1) — stack mode follows `stack-submit.md` to submit/sync remaining layers and reports the bottom open non-draft PR. Otherwise report the PR already updated by Step 3. During authorized babysitting, apply a factual description refresh from verified run results directly, preserving unrelated user content and issue links; do not route maintenance through optional-rewrite approval. An explicit request to apply an update also authorizes it. Outside those cases, separately ask whether to perform an optional rewrite, never bundle it with alignment or monitoring.

- **No** — skip the description rewrite and continue to the babysit handoff rule below.
- **Yes** — run Step 4 (compose the PR title and body) if not already done, then preview and apply (see below).

**Apply decision** — compare proposed and existing title/body; identical content needs no edit. Authorized factual maintenance or explicit apply requests proceed without another yes/no or preview-approval question. Otherwise preview the optional rewrite (title, first two sentences, line count) and ask for approval before applying. If declined, keep the current description and continue any otherwise authorized babysit handoff; regeneration is optional, never a monitoring prerequisite. Description-only requests print a draft and stop. Respect higher-priority policy, real tool permissions, opt-outs, watch boundaries, final-merge decisions, and genuine scope-expansion/needs-human cases.

**Alignment and monitoring** — aligning a clean workspace to the exact verified pushed PR head and starting/re-arming authorized monitoring need no extra approval. Verify head repository, bookmark, remote and commit first; empty `@` directly above the head is already aligned. Preserve unrelated tracked, ignored and untracked work. Dirty/conflicted state, ambiguous head, denied permission, or unknown push authority takes the safe stop/decision path, never reset/discard or a guessed target. An optional rewrite cannot block this authorized handoff.

**Explainer archival** — runs only in the full workflow, when all of these hold: `pr_teaching_archive` is on, the composed body has a `## New concepts` section, and the apply was confirmed (a new-PR create, or an existing-PR rewrite the user accepted). A declined rewrite skips archival entirely, so no unlinked doc commit is left behind. Resolve every path from the repo root gathered in Context, never from the CWD. With two taught concepts, write one file per concept and stage both in the single commit. Resolve `<root>` first:

<!-- ce-docs-root:start -->
**Resolve the artifact root `<root>` before composing any artifact path.**

- **Read** `docs_root` from `<repo-root>/.rocketclaw/config.yaml` only (`<repo-root>` = `jj workspace root`). Do not read it from `config.local.yaml`. Unset -> `<root>` is `docs`, exactly as before.
- **Validate** a set value: a repo-relative directory whose real, symlink-resolved path stays inside the repo and is neither the repo root nor under `.git/`. Otherwise stop with an error naming `docs_root` and the value -- never fall back to `docs`.
- **Use** `<root>` as the sole artifact location: create it if absent, compose each path as `<root>/<subdir>` with this skill's own subdirectory, and never also read `docs`.
<!-- ce-docs-root:end -->

Then run these steps, in order, immediately before the `gh` call:

1. Inspect applicable repository/global ignore patterns with equivalent local ignore-rule processing for the proposed path, including a nonexistent path. Account for parent directories, nested ignore files, negation, and already-tracked paths (query those with `jj file list`). If ignored, warn and skip archival without writing; never force-track. If ignore status cannot be established, warn and skip rather than guess. Never invoke Git for this check.
2. Write the file (create the directory if needed) with YAML frontmatter `title`, `date`, `input_shape: concept`, `subject`, and the teaching content. If the file already exists from a prior run, overwrite it.
3. Read `commit-and-push.md` in full, including its verbatim Go excerpts and runtime comparison of several subjects AND bodies. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards. Read the full guide, resolve the task's verified history head, and let repository-local syntax win. Describe the taught concepts without a fixed prefix/template. Commit only those paths with `jj commit <explainer-paths> -m "<message composed from the standards above>"`. Re-apply the Project publishing gate and push the verified feature bookmark using JJ. If unchanged and already committed, keep the link and continue.
4. Add a head-branch blob URL for each doc into the `## New concepts` section before applying. Build the URL for the repo's actual host — for example `gh browse -n -b <head-branch> -- <path>` prints the link on whatever host `gh` targets, GitHub Enterprise included. Do not hardcode `github.com`, or the link 404s on GHE.

For archival message composition, these verbatim Go source excerpts are illustrative guidance, not a mandatory repository template. The runtime repository pattern above always wins:

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
mkdir -p "$workspace_root/.tmp/pr"
BODY_FILE=$(mktemp "$workspace_root/.tmp/pr/pr-body.XXXXXX")
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

**Screenshots.** When the body references local images from `references/visual-evidence.md`, create the body file in the images' directory so each `./<name>.png` reference resolves: `BODY_FILE=$(mktemp "<images-dir>/ce-pr-body.XXXXXX")`. Add one `--attach "<images-dir>/<name>.png#<alt text>"` per image to the create or edit command. `gh` uploads each file and rewrites the matching reference to its GitHub URL.

A file `gh` rejects before uploading, such as a missing file or an image over 10 MB, makes it exit non-zero without creating or editing the PR; stderr names the file. An upload that fails after others succeeded can still leave the PR created or updated, and `gh` then still prints its URL. So whatever the exit status, do not run `gh pr create` a second time. Find the PR from the printed URL, or the way the new-PR re-check above does when none was printed, and read its body with `gh pr view "<pr-url>" --json body`. If any image reference there still points at a local path, edit that PR's body on GitHub to remove those references and keep everything else. If the create or edit did not apply, apply the body again without the images that failed. Either way, report which images did not upload.
