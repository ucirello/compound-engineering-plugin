---
name: ce-commit-push-pr
description: Describe changes, push a bookmark, and open a PR. Use when asked to ship/open a PR, or for PR-description-only flows like writing, rewriting, or describing a PR body.
argument-hint: "[PR ref] [mode:pipeline] [archive:on|off] [babysit:off|continuous|checkpoint]"
---

# Jujutsu Change, Push, and PR

**Asking the user:** When this skill says "ask the user", use the platform's blocking question tool: `AskUserQuestion` in Claude Code (call `ToolSearch` with `select:AskUserQuestion` first if its schema isn't loaded), `request_user_input` in Codex, `ask_question` in Antigravity CLI (`agy`), `ask_user` in Pi (requires the `pi-ask-user` extension). Fall back to presenting the question on the host's user-visible chat surface only when no blocking tool exists in the harness or the call errors (e.g., Codex edit modes) — not because a schema load is required. Never silently skip the question.

## Mode

- **Description-only** — user wants *just* a description ("write/draft a PR description", "describe this PR", or pasted a PR URL/number alone). Run Step 4 only; print the result. Apply only if the user asks. If a PR ref was pasted, pass it to Step 4 so Pre-A resolves the right range.
- **Description update** — user wants to refresh/rewrite an existing PR's description with no commit/push intent. Determine PR presence with the same rule used everywhere: only an exit-0 `[]` from the existing-PR check means "no open PR" (report and stop); a non-zero check is **unknown** (resolve `gh auth status` / connectivity first — never treat it as "no PR"). With an open PR, run Step 4 (PR mode using the existing PR's URL), then Step 5 to preview, confirm, and apply via `gh pr edit`.
- **Full workflow** — otherwise. Run Steps 1-5 in order. When user intent or standing preference wants a **PR stack**, enter **Stack mode** (below) instead of ordinary single-PR create in Step 5; do not add `posture:` to this skill's argument-hint.

**`mode:pipeline` modifier** — set by orchestrated callers (e.g., `lfg`). Run the resolved mode non-interactively: suppress every blocking ask. Step 5's existing-PR rewrite question defaults to **not rewriting**; in description-update mode the preview ask is skipped and the rewrite applies directly (the update invocation itself is the apply intent); any other suppressed ask takes its conservative documented default (keep the current bookmark; if Pre-A cannot resolve a base, stop and report rather than guess). Pipeline stack mode uses only intent/scope already on the invocation — never ask; pass posture into the babysit handoff args when stacking.

## Stack mode (opt-in)

**Opt-in only.** Enter stack mode when user intent or standing preference wants a multi-PR stack. An explicit stack request is **required intent** — do not re-read it as a single PR with a custom `--base`. **Do not** proactively suggest PR stacks. When the user did **not** ask for one, **refuse** nonsense stacks (one logical change, artificial slices) and stay on the single-PR path.

When stack mode is active, load `references/stack-submit.md` **before Step 3**. At this point follow only its Probe, Topology, and, when needed, Retrospective construction sections; do not submit. When that reference constructs a retrospective stack, its layer-by-layer change flow replaces ordinary Step 3. Step 5 exclusively owns stack submission and the reference's post-submit metadata route for PRs created in this run. Soft-depend on `gh stack` CLI only. On missing/unavailable CLI: required stack intent → hard-stop with residual; soft intent → residual + ordinary single-PR create.

After successful submit with ready (non-draft) PRs, continue to the babysit handoff below using the **bottom open non-draft** PR. Derive babysit posture from ship intent: default `posture:stack-ready`; use `posture:stack-land` only when land/merge-when-green intent is explicit. Pass that posture on the `ce-babysit-pr` invocation (do not put `posture:` on this skill's argument-hint). Draft-only submit → hard residual before babysit when babysit is on.

## Context

Gather the repository context by running each command below as its **own** shell tool call — a single argv-style invocation (just the program and its arguments). Do **not** join them with shell operators, pipes, substitutions, or redirects. Read each exit status directly; unavailable PR metadata or an unbookmarked working-copy change is state to interpret, not a failure to suppress.

Run them in order — the existing-PR check needs the bookmark associated with the working-copy change:

| Command | Purpose | Non-zero exit / empty output means |
| --- | --- | --- |
| `jj workspace root` | Workspace root | Not a Jujutsu workspace — use the current directory only for temporary paths; report and stop for repository operations |
| `jj status` | Working-copy state | Fails outside a Jujutsu repository |
| `jj diff` | Current change | Empty output = no content changes in `@` |
| `jj bookmark list -r @ -T 'name ++ "\n"'` | Local bookmarks targeting `@` | Empty output = no bookmark; multiple lines = ambiguous (Step 1 handles either) |
| `jj log -r ::@ -n 10` | Recent change-description / PR-title style | Empty history = no prior descriptions |
| `gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'` | Remote default branch | Resolve per Step 1 if unavailable |
| `gh pr list --head <bookmark> --state open --json number,url,title,body,state,isDraft,headRefName,headRepositoryOwner` | Open PR for this bookmark (run only once `<bookmark>` is unambiguous) | Exit 0 with `[]` = no open PR. Non-zero = `gh` missing, unauthenticated, or offline — PR state is **unknown**, not "none"; never treat a non-zero check as "no PR"; re-check before creating (Step 5) |

Substitute `<bookmark>` with the single local bookmark targeting `@`, and pass its **name only**. Two traps:

- **No bookmark or multiple bookmarks at `@`:** skip the PR check entirely — an empty `--head` drops the filter and guessing can target an unrelated PR. Resolve one feature bookmark in Step 1.
- **Fork checkout:** do **not** pass `<owner>:<bookmark>` — `gh pr list --head` does not accept that syntax and silently returns `[]` for it. Target the base repo through default-repo resolution or `-R <base-owner>/<repo>`.

Everything gathered here is a snapshot taken before any action — treat it as a hint, not ground truth. Re-verify the bookmark, remote, and existing-PR state immediately before each consequential step.

---

## Artifact Root

When PR concept-teaching archival is on, this skill writes an explainer under `<root>/explainers/`. Resolve `<root>` once before that write and use it everywhere a `<root>/` path appears below.

**Resolve the artifact root `<root>` before composing any artifact path.**

- **Read** `docs_root` from `<workspace-root>/.rocketclaw/config.yaml` only (`<workspace-root>` = `jj workspace root`). Do not read it from `config.local.yaml`. Unset -> `<root>` is `docs`.
- **Validate** a set value: a workspace-relative directory whose real, symlink-resolved path stays inside the workspace and is neither the workspace root nor under `.jj/`. Otherwise stop with an error naming `docs_root` and the value -- never fall back to `docs`.
- **Use** `<root>` as the sole artifact location: create it if absent, compose each path as `<root>/<subdir>` with this skill's own subdirectory, and never also read `docs`.

## Step 1: Resolve branch and PR state

Use `gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'` for the remote default branch. If it fails, inspect remote bookmarks with `jj bookmark list --all-remotes`; if no unique default can be established, ask rather than guessing. For the existing-PR check, exit 0 with `[]` means no open PR for this bookmark; a non-zero exit means PR state is unknown and must be resolved before creation.

Bookmark routing:

- **No bookmark at `@`** — derive a feature name from the change content, run `jj bookmark create <bookmark-name> -r @`, and use the unique resulting bookmark. Choose a non-conflicting suffix when safe; ask only when ambiguity remains.
- **Multiple bookmarks at `@`** — resolve the intended GitHub head from user intent, tracked remote bookmarks, and open-PR metadata; stop and ask if it is not unique.
- **On the default bookmark with work to do** — create a feature bookmark; pushing the default directly is unsupported. Continue at Step 3 for safe base handling.
- **On the default bookmark with no work** — report no feature work and stop.
- **Feature bookmark** — continue.

If the PR check returned a non-empty array, do not blindly take index 0. Match `headRepositoryOwner` and `headRefName` to the bookmark's push target; stop if the owner cannot be confirmed uniquely. Step 5 uses the selected URL to route application, and Step 4 uses its body as rewrite context.

## Step 2: Determine conventions

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Runtime project instructions and conventions already in context win, followed by history read with `jj log`; the quoted rule is quality guidance, not permission to run Git. Preserve established project syntax. Without a stronger convention, use a short first line that completes “this change modifies the project to ...”, starts its action in lowercase after any established scope, has no trailing period, and adds a plain-text body when the reason is not obvious. Do not add Markdown or sign-off lines to a Jujutsu description.

## Step 3: Commit and push

If the stack reference constructed retrospective layers before this step, skip ordinary single-bookmark describe/push and continue to Step 4; `gh stack submit` in Step 5 pushes the stack.

If on the default bookmark, feature-bookmark creation needs to handle a stale local `<base>`, unpushed changes on local `<base>`, and working-copy changes relative to the fresh remote base. Read `references/branch-creation.md` and follow its decision flow before continuing.

Scan changed files for naturally distinct concerns. If they clearly group into separate logical changes, create separate Jujutsu changes (2-3 max). Group at file level only; do not use interactive hunk selection. When ambiguous, one change is fine.

Commit each group by passing only its whole-file fileset to `jj commit`; Jujutsu has no staging area. **Honor `exclude:<paths>` when the invocation carries it:** never include those files, and report that they remain in the working-copy change. When a plan Implementation Unit ID is already in hand for this change, append its U-ID in parentheses. Do not hunt for a plan. Omit it when the change spans units, the unit is unclear, or no plan is in hand.

```bash
jj commit -m "<description derived from current standards>" <group-files>
```

The fileset is load-bearing: a bare `jj commit` selects the entire working-copy change. Naming the group keeps every other path, including `exclude:` paths, in the new working-copy change.

After the final `jj commit`, move the intended feature bookmark to the last completed change (`@-`). Immediately before pushing, confirm it is the intended bookmark and inspect its local and remote targets. Push only that bookmark:

```bash
jj bookmark move <bookmark> --to @-
jj git push --remote <remote> --bookmark <bookmark>
```

If the working-copy change is empty and the bookmark already matches its remote bookmark, this step is a no-op.

## Step 4: Compose the PR title and body

**You MUST read `references/pr-description-writing.md`** in full — it owns value-first framing, sizing, program altitude, related-work references (preserve existing `Related:` / `Fixes` on rewrite), and the pre-apply audit. The only input it needs from this skill is the PR ref, if one was identified by mode dispatch. If Step 1 found an existing PR, pass its URL to Step 4 when rewriting so PR mode fetches the existing body. In Stack mode, Step 5 follows the post-submit route in `references/stack-submit.md` instead of composing one default-base body here.

**Evidence decision** before composition. This skill does not own a capture workflow — use harness capture tools or user-supplied artifacts, never invent/upload evidence or launch another skill.

1. **User supplied** (URL, markdown image/embed, local path) — incorporate as `## Demo`, `## Screenshots`, or `## Evidence`.
2. **User asked for evidence but supplied none** — ask for the artifact or tell them to capture with the harness and return.
3. **No material observable claim** (internal plumbing, type-only, pure refactor, inert docs) — skip without asking. Classify by runtime purpose, not extension (runtime agent instructions / config / product content / policy YAML is not auto-skippable as "docs").
4. **Otherwise** (UI, CLI, API, workflow, ranking, deploy/config behavior) — concise validation note of what was exercised; if a real run was impossible (credentials, paid services, deploy-only, hardware, missing setup), say so. Do not block PR creation for missing visuals; test/manual notes are fine — never label test output "Demo" or "Screenshots."

**Concept teaching gate** before composition. Use the workspace root gathered in Context (resolving it with `jj workspace root` if needed) and apply the ordinary-key rule below.

**Resolve ordinary YAML keys from the two workspace files.**

- **Read** `<workspace-root>/.rocketclaw/config.local.yaml`, then `config.yaml` (`<workspace-root>` = `jj workspace root`). Missing files are skipped. Ignore rules do not change resolution.
- **Win** with the first active (non-commented) value. For scalars, empty is unset; an invalid value continues to the next layer, then the skill default. For lists and maps, a present key — including an empty list or map — replaces the whole key.
- **Do not** use this rule for `docs_root` — that key is `config.yaml` only.

Only an **active (non-commented)** `pr_teaching_section:` key counts — lines starting with `#` are YAML comments; matching commented template keys would silently flip the gate. Off only when the winning active value is exactly `false`; missing key or any other value → default **on**. Same cascade resolves `pr_teaching_archive:` — on only when the winning active value is exactly `true`, else **off**; per-run `archive:on|off` overrides for this invocation.

- Gate **on** — judge novelty and compose per **Step B2** of the reference. When off, skip judgment, section, Step 5 trailer/offer, and archival entirely.
- Gate **off** — compose without concept handling.

Then continue with the reference (Steps A–E, including Step B2 when the teaching gate is on). Step E must run before the body is returned.

## Step 5: Apply and report

**Description-only mode** — print the title and body. Stop unless the user asks to apply.

**New PR** (full workflow, no existing PR from Step 1) — if **Stack mode** is active, follow the Submit section of `references/stack-submit.md` instead of `gh pr create`; then report the bottom open non-draft PR URL and continue to babysit handoff. Otherwise, immediately before creating, **always** re-run `gh pr list --head <bookmark> --state open --json number,url,isDraft,headRefName,headRepositoryOwner` (bookmark name only; target the base repo on a fork, per Context). Match the current push target by owner and head name, and resolve a non-zero check before creation. Apply per "Applying via gh" only after absence is confirmed.

**Existing PR** (full workflow, found in Step 1) — if **Stack mode** is active, still follow the Submit section of `references/stack-submit.md` so remaining stack layers submit / sync; then report the bottom open non-draft PR URL and continue to babysit handoff. Otherwise the new revisions are already on the PR from Step 3. Report the PR URL, then ask whether to rewrite the description.

- **No** — done.
- **Yes** — run Step 4 if not already done, then preview and apply (see below).

**Description update mode, or existing-PR rewrite confirmed** — preview before applying. First compare the proposed title and body with the existing PR. If they are identical, keep them and do not call `gh pr edit`. Otherwise ask: "New title: `<title>` (`<N>` chars). Summary leads with: `<first two sentences>`. Total body: `<L>` lines. Apply?" If declined, do not apply. If confirmed, apply per "Applying via gh" and report the URL.

**Explainer archival** — runs only in full workflow, with `pr_teaching_archive` on, a composed `## New concepts` section, and the apply confirmed. All paths resolve from the workspace root. With two concepts, write one file per concept and include both in one Jujutsu change:

1. Evaluate the workspace's effective ignore rules for each proposed `<root>/explainers/<date>-<concept-slug>.md` path before writing. If any path is ignored, warn and skip archival without force-tracking it.
2. Write the file (create the directory if needed) with YAML frontmatter `title`, `date`, `input_shape: concept`, `subject`, and the teaching content. If the file already exists from a prior run, overwrite it.
3. Commit only those files with `jj commit -m "<description derived from current standards>" <explainer-files>`, move the feature bookmark to `@-`, and push it. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. If there is no content change, keep the existing link and continue.
4. Splice a head-bookmark blob URL per doc into `## New concepts` with `gh browse -n -b <head-bookmark> -- <path>`; do not hardcode a host.

If the doc write, commit, or push fails, warn and continue to PR creation without the link — never strand the flow between commit and PR.

**User-runnable invocation rendering.** For the output handoffs below, default to `/ce-explain <name>`. Use `$ce-explain <name>` only when the active host is Codex or explicitly documents dollar-prefixed skill invocation. Render only the invocation as inline code and output one form only.

**Concept trailer** — when a body applied by this run contains a `## New concepts` section, print one line after the PR URL in every mode: `New concepts: <name>[, <name>]`. In interactive full-workflow runs follow it with one line per taught concept telling the user to invoke `ce-explain <name>` using the rendering rule above. No trailer when this run applied no body — including a rewrite that was declined or pipeline-defaulted to no — or no PR exists.

**Babysit handoff — default on; completion gate.** After reporting a newly-created PR URL, a successful **stack submit**, or new changes landing on an existing open PR (interactive full workflow **or** `mode:pipeline` when stack mode submitted this run), this run is **not done** until `ce-babysit-pr` owns follow-on for that PR — or an explicit skip below applies. Reporting the PR URL alone is not success. **Auto-hand off by default:** announce in one non-blocking line (e.g. "Babysitting toward merge-ready — pass `babysit:off` to skip"), then invoke `ce-babysit-pr` through the host's normal skill-invocation mechanism with the PR URL — never ask yes/no. After **stack submit**, hand off the **bottom open non-draft** PR and include the derived posture (`posture:stack-ready` by default; `posture:stack-land` when land intent was explicit) plus stack-wide scope for `mode:pipeline` when applicable. Announce that stack babysit ownership transferred so an outer orchestrator (e.g. `lfg` step 9) does not start a second bare babysit on the current bookmark. **Success** = `ce-babysit-pr` has started on that PR; in `mode:pipeline`, wait for its pipeline stop and return the structured result to the caller. Never start babysit mechanics yourself or substitute another watcher. If the handoff cannot start, stop and report blocked. **`babysit:off`** skips this run; **`babysit:continuous`** / **`babysit:checkpoint`** forces that mode; **`auto_babysit: false`** in `.rocketclaw` config is a standing opt-out.

**Do not fire (auto-detected, no flag needed):** `mode:pipeline` **except** after stack submit, description-only / description-update, no PR changed this run, non-GitHub, a draft PR unless explicitly forced, or a head bookmark that cannot be pushed. Fork PRs remain drivable when the head bookmark is pushable.

---

## Applying via gh

The body **must** be written under `<workspace-root>/.tmp/rocketclaw/` and passed via `--body-file <path>`. Resolve the root with `jj workspace root`; use the current directory only if that fails. Create the directory if absent. Never use OS-global temp, `$TMPDIR`, `--body-file -`, stdin pipes, heredoc-to-stdin, or command-substituted body text.

```bash
BODY_FILE="<workspace-root>/.tmp/rocketclaw/pr-body-<unique-run-id>.md"
cat > "$BODY_FILE" <<'<neutral-sentinel>'
<the composed body markdown goes here, verbatim>
<neutral-sentinel>
```

The quoted sentinel keeps `$VAR`, backticks, and any literal `EOF` inside the body from being expanded.

For `<TITLE>`: substitute verbatim. If it contains `"`, `` ` ``, `$`, or `\`, escape them or switch to single quotes.

```bash
gh pr create --title "<TITLE>" --body-file "$BODY_FILE"   # new PR
gh pr edit   --title "<TITLE>" --body-file "$BODY_FILE"   # existing PR
```
