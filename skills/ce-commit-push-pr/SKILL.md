---
name: ce-commit-push-pr
description: Describe changes, push a bookmark, and open a PR. Use when asked to ship/open a PR, or for PR-description-only flows like writing, rewriting, or describing a PR body.
argument-hint: "[PR ref] [mode:pipeline] [archive:on|off] [babysit:off|continuous|checkpoint]"
---

# Jujutsu Change, Push, and PR

**Asking the user:** When this skill says "ask the user", use the available blocking question interface. Fall back to the user-visible chat surface only when no blocking interface exists or the call errors. Never silently skip the question.

## Mode

- **Description-only** — user wants *just* a description ("write/draft a PR description", "describe this PR", or pasted a PR URL/number alone). Run Step 4 only; print the result. Apply only if the user asks. If a PR ref was pasted, pass it to Step 4 so Pre-A resolves the right range.
- **Description update** — user wants to refresh/rewrite an existing PR's description with no change/push intent. Determine PR presence with the same rule used everywhere: only an exit-0 `[]` from the existing-PR check means "no open PR" (report and stop); a non-zero check is **unknown** (resolve `gh auth status` / connectivity first — never treat it as "no PR"). With an open PR, run Step 4 (PR mode using the existing PR's URL), then Step 5 to preview, confirm, and apply via `gh pr edit`.
- **Full workflow** — otherwise. Run Steps 1-5 in order. When user intent or standing preference wants a **PR stack**, enter **Stack mode** (below) instead of ordinary single-PR create in Step 5; do not add `posture:` to this skill's argument-hint.

**`mode:pipeline` modifier** — set by orchestrated callers (e.g., `lfg`). Run the resolved mode non-interactively: suppress every blocking ask. Step 5's existing-PR rewrite question defaults to **not rewriting**; in description-update mode the preview ask is skipped and the rewrite applies directly (the update invocation itself is the apply intent); any other suppressed ask takes its conservative documented default (keep the current bookmark; if Pre-A cannot resolve a base, stop and report rather than guess). Pipeline stack mode uses only intent/scope already on the invocation — never ask; pass posture into the babysit handoff args when stacking.

## Stack mode (opt-in)

**Opt-in only.** Enter stack mode when user intent or standing preference wants a multi-PR stack. An explicit stack request is **required intent** — do not re-read it as a single PR with a custom `--base`. **Do not** proactively suggest PR stacks. When the user did **not** ask for one, **refuse** nonsense stacks (one logical change, artificial slices) and stay on the single-PR path.

When stack mode is active, load `references/stack-submit.md` **before Step 3**. At this point follow only its Probe, Topology, and, when needed, Retrospective construction sections; do not submit. When that reference constructs a retrospective stack, its layer-by-layer change flow replaces ordinary Step 3. Step 5 exclusively owns stack submission and the reference's post-submit metadata route for PRs created in this run. Soft-depend on `gh stack` CLI only. On missing/unavailable CLI: required stack intent → hard-stop with residual; soft intent → residual + ordinary single-PR create.

After successful submit with ready (non-draft) PRs, continue to the babysit handoff below using the **bottom open non-draft** PR. Derive babysit posture from ship intent: default `posture:stack-ready`; use `posture:stack-land` only when land/merge-when-green intent is explicit. Pass that posture on the `ce-babysit-pr` invocation (do not put `posture:` on this skill's argument-hint). Draft-only submit → hard residual before babysit when babysit is on.

## Context

Gather the repository context by running each command below as its **own** shell tool call — a single argv-style invocation (just the program and its arguments). Do **not** join them with `;`, `&&`, `||`, pipes, `$(...)`, or redirects like `2>/dev/null`: that syntax parses only under POSIX shells and aborts under Windows PowerShell. Read each command's exit status directly — a non-zero exit is a normal state to interpret (no PR yet, no `origin/HEAD`, detached HEAD), not a failure to suppress.

Run them in order — the existing-PR check needs the bookmark attached to the working-copy change:

| Command | Purpose | Non-zero exit / empty output means |
| --- | --- | --- |
| `jj workspace root` | Workspace root | Not a Jujutsu workspace — report and stop |
| `jj status` | Working-copy and bookmark state | Fails outside a workspace |
| `jj diff` | Current change | Empty output means the working-copy change has no file changes |
| `jj bookmark list -r @ -T 'name ++ "\n"'` | Bookmark attached to the current change (`<bookmark>`) | Empty output means the change has no bookmark; multiple names require disambiguation (Step 1 handles it) |
| `jj bookmark list -r 'heads(::@ & bookmarks())' -T 'name ++ "\n"'` | Nearest ancestor bookmarks | Used to distinguish feature work from work directly above the default bookmark |
| `jj log -r ::@ -n 10` | Recent change-description / PR-title style | No meaningful history yet |
| `gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'` | Remote default bookmark | Non-zero means default lookup is unavailable; resolve per Step 1 |
| `gh pr list --head <bookmark> --state open --json number,url,title,body,state,isDraft,headRefName,headRepositoryOwner` | Open PR for this bookmark (run only once `<bookmark>` is non-empty) | Exit 0 with `[]` = no open PR. Non-zero = `gh` missing, unauthenticated, or offline — PR state is **unknown**, not "none"; never treat a non-zero check as "no PR"; re-check before creating (Step 5) |

Substitute `<bookmark>` with the uniquely selected local name from `jj bookmark list -r @ -T 'name ++ "\n"'`, and pass the bookmark **name only**. Two traps:

- **No bookmark:** skip the PR check entirely — `gh pr list` with an empty `--head` drops the filter and lists unrelated PRs. Resolve it after Step 1 creates a bookmark.
- **Fork checkout:** do **not** pass `<owner>:<bookmark>` — `gh pr list --head` does not accept that syntax and silently returns `[]` for it, which reads as "no PR" and opens a duplicate. The PR lives on the base repo, so make `gh` target the base: rely on its default-repo resolution, or pass `-R <base-owner>/<repo>` explicitly when the default is the fork.

Everything gathered here is a snapshot taken before any action — treat it as a hint, not ground truth. Re-verify the bookmark, remote, and existing-PR state immediately before each consequential step (push in Step 3, `gh pr create` in Step 5), since they can change between gathering and acting.

---

## Artifact Root

When PR concept-teaching archival is on, this skill writes an explainer under `<root>/explainers/`. Resolve `<root>` once before that write and use it everywhere a `<root>/` path appears below.

**Resolve the artifact root `<root>` before composing any artifact path.**

- **Read** `docs_root` from `<workspace-root>/.workflow/config.yaml` only (`<workspace-root>` = `jj workspace root`). Do not read it from `config.local.yaml`. Unset -> `<root>` is `docs`.
- **Validate** a set value: a workspace-relative directory whose real, symlink-resolved path stays inside the workspace and is neither the workspace root nor under `.jj/`. Otherwise stop with an error naming `docs_root` and the value -- never fall back to `docs`.
- **Use** `<root>` as the sole artifact location: create it if absent, compose each path as `<root>/<subdir>` with this skill's own subdirectory, and never also read `docs`.
## Step 1: Resolve bookmark and PR state

Use the default bookmark returned by `gh repo view`. If lookup fails, inspect remote bookmarks with `jj bookmark list --all-remotes`; use a uniquely identifiable repository default, otherwise ask rather than guessing. For the existing-PR check: an empty `[]` array means no open PR for this bookmark; a non-zero exit means `gh` is missing, unauthenticated, or offline — treat PR state as **unknown** (not "no PR") and re-run the check, or `gh auth status`, before creating a new PR in Step 5 rather than assuming none exists.

Bookmark routing:

- **No attached bookmark** — if the unique nearest ancestor bookmark is the default, derive a feature bookmark name and continue at Step 3 so the remote base is resolved safely. Otherwise create the derived feature bookmark at `@` with `jj bookmark create <bookmark-name> -r @`. If ancestry is ambiguous, stop rather than choosing a base; if the name exists, choose a non-conflicting suffix or ask only if the conflict cannot be resolved safely.
- **Default bookmark with work to do** — derive a feature bookmark and continue at Step 3, which roots it safely. Pushing the default directly is not supported.
- **Default bookmark with no work** — report no feature work and stop.
- **Feature bookmark** — continue.

If the PR check returned a non-empty array, do **not** blindly take index 0 — in a base repo with multiple forks, another contributor's PR can share the same head name (`--head` filters by name only, not `<owner>:<name>`). Select the entry whose `headRepositoryOwner` and `headRefName` match the bookmark and remote this workflow is pushing. Note the URL and body from that entry. If exactly one entry matches, use it; if ownership cannot disambiguate matches, stop rather than acting on the wrong PR. Step 5 uses the URL to route between new-PR and existing-PR application. Step 4 uses the existing body as preservation context when rewriting.

## Step 2: Determine conventions

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. The project's active instructions and the description syntax observed at runtime in `jj log` win. Apply compatible Go guidance only to quality, clarity, and structure; it does not prescribe imperative mood, casing, punctuation, line wrapping, subject/body shape, or any fixed syntax. Derive PR titles independently from the project's PR conventions and the change outcome.

## Step 3: Describe changes and push

If the stack reference constructed retrospective layers before this step, skip ordinary single-bookmark description/push and continue to Step 4; `gh stack submit` in Step 5 pushes the stack.

If on the default bookmark, feature-bookmark creation needs to preserve local-only changes while rooting new work on a fresh remote base. Read `references/bookmark-creation.md` and follow its decision flow before continuing.

Scan changed files for naturally distinct concerns. If they clearly group into separate logical changes, create separate changes (2-3 max). Group at file level only; when ambiguous, one change is fine.

Partition each group with filesets. **Honor `exclude:<paths>` when the invocation carries it:** excluded files belong to no described change; leave them in the working-copy change and report that they were omitted. Preserve semantic requirements already in hand, such as a plan unit association, without forcing any fixed prefix, type, scope, subject, body, or suffix syntax.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. The project's active instructions and the description syntax observed at runtime in `jj log` win. Apply compatible Go guidance only to quality, clarity, and structure; it does not prescribe imperative mood, casing, punctuation, line wrapping, subject/body shape, or any fixed syntax. Apply the composed description to each selected group:

```bash
jj commit -m "<message composed from the standards above>" file1 file2 file3
```

The filesets are load-bearing: they retain only the selected paths in the described change and move remaining work into the new child working-copy change. Verify each resulting change with `jj show`; if partitioning changed dependencies, fix the topology before pushing.

Then push. Immediately before pushing, re-confirm the intended feature bookmark and move it to the final described change, normally `@-` after `jj commit` created an empty child. Never move it to an undescribed working-copy change:

```bash
jj bookmark set <bookmark> -r @-
jj git push --bookmark <bookmark> --remote origin
```

If the working-copy change is empty and the bookmark already matches its remote counterpart, this step is a no-op.

## Step 4: Compose the PR title and body

**You MUST read `references/pr-description-writing.md`** in full — it owns value-first framing, sizing, program altitude, related-work references (preserve existing `Related:` / `Fixes` on rewrite), project-required metadata, and the pre-apply audit. The only input it needs from this skill is the PR ref, if one was identified by mode dispatch (description-only with a pasted URL, description update, or confirmed existing-PR rewrite in full workflow). If Step 1 found an existing PR, pass its URL to Step 4 when rewriting so PR mode fetches the existing body. In Stack mode, Step 5 follows the post-submit route in `references/stack-submit.md` instead of composing one default-base body here.

**Evidence decision** before composition. This skill does not own a capture workflow — use available capture tools or user-supplied artifacts, and never invent or upload evidence.

1. **User supplied** (URL, markdown image/embed, local path) — incorporate as `## Demo`, `## Screenshots`, or `## Evidence`.
2. **User asked for evidence but supplied none** — ask for the artifact or tell them to capture it with an available interface and return.
3. **No material observable claim** (internal plumbing, type-only, pure refactor, inert docs) — skip without asking. Classify by runtime purpose, not extension (runtime agent instructions / config / product content / policy YAML is not auto-skippable as "docs").
4. **Otherwise** (UI, CLI, API, workflow, ranking, deploy/config behavior) — concise validation note of what was exercised; if a real run was impossible (credentials, paid services, deploy-only, hardware, missing setup), say so. Do not block PR creation for missing visuals; test/manual notes are fine — never label test output "Demo" or "Screenshots."

**Concept teaching gate** before composition. Use the workspace root gathered in Context (resolving it with `jj workspace root` if you don't already have it — description-only/update can skip the Context snapshot) and apply the ordinary-key rule below.

**Resolve ordinary workflow YAML keys from the two workspace files.**

- **Read** `<workspace-root>/.workflow/config.local.yaml`, then `config.yaml` (`<workspace-root>` = `jj workspace root`). Missing files are skipped. Ignore rules do not change resolution.
- **Win** with the first active (non-commented) value. For scalars, empty is unset; an invalid value continues to the next layer, then the skill default. For lists and maps, a present key — including an empty list or map — replaces the whole key.
- **Do not** use this rule for `docs_root` — that key is `config.yaml` only.
Only an **active (non-commented)** `pr_teaching_section:` key counts — lines starting with `#` are YAML comments; matching commented template keys would silently flip the gate. Off only when the winning active value is exactly `false`; missing key or any other value → default **on**. Same cascade resolves `pr_teaching_archive:` — on only when the winning active value is exactly `true`, else **off**; per-run `archive:on|off` overrides for this invocation.

- Gate **on** — judge novelty and compose per **Step B2** of the reference. When off, skip judgment, section, Step 5 trailer/offer, and archival entirely.
- Gate **off** — compose without concept handling.

Then continue with the reference (Steps A–E, including Step B2 when the teaching gate is on). Step E must run before the body is returned.

## Step 5: Apply and report

**Description-only mode** — print the title and body. Stop unless the user asks to apply.

**New PR** (full workflow, no existing PR from Step 1) — if **Stack mode** is active, follow the Submit section of `references/stack-submit.md` instead of `gh pr create`; then report the bottom open non-draft PR URL and continue to babysit handoff. Otherwise, immediately before creating, **always** re-run `gh pr list --head <bookmark> --state open --json number,url,isDraft,headRefName,headRepositoryOwner` (bookmark name only; target the base repo on a fork, per Context) so a PR that appeared since Step 1, or was missed because the Step 1 check came back **unknown**, is not duplicated. If it now shows a PR whose `headRepositoryOwner`/`headRefName` match the current head, switch to the existing-PR path; disambiguate multi-fork matches by head owner as in Step 1 rather than assuming index 0. If this re-check itself exits non-zero, resolve `gh auth status` / connectivity before creating rather than assuming none exists. Otherwise apply per "Applying via gh" below using `gh pr create`. Report the URL.

**Existing PR** (full workflow, found in Step 1) — if **Stack mode** is active, still follow the Submit section of `references/stack-submit.md` so remaining stack layers submit / sync (mid-stack ship is normal); then report the bottom open non-draft PR URL and continue to babysit handoff with derived posture. Otherwise the new changes are already on the PR from Step 3. Report the PR URL, then ask whether to rewrite the description.

- **No** — done.
- **Yes** — run Step 4 if not already done, then preview and apply (see below).

**Description update mode, or existing-PR rewrite confirmed** — preview before applying. First compare the proposed title and body with the existing PR. If they are identical, keep the existing title and body and do not call `gh pr edit`. If the only difference removes generated promotional metadata, also keep the existing title and body unless the user explicitly requested that cleanup; metadata cleanup alone never creates apply intent. Otherwise ask: "New title: `<title>` (`<N>` chars). Summary leads with: `<first two sentences>`. Total body: `<L>` lines. Apply?" If declined, the user may pass focus text back for a regenerate; do not apply. If confirmed, apply per "Applying via gh" below using `gh pr edit` and report the URL.

**Explainer archival** — runs only in full workflow, with `pr_teaching_archive` on, a composed `## New concepts` section, and the apply confirmed (new-PR create, or existing-PR rewrite accepted); a declined rewrite skips archival entirely so no unlinked document change is left behind. All paths resolve from the workspace root gathered in Context, never the CWD. With two taught concepts, write one file per concept in one change. Execute as explicit transitions immediately before the `gh` call:

1. Confirm that `<root>/explainers/YYYY-MM-DD-<concept-slug>.md` is eligible for tracking under the workspace's ignore rules. If ignored, print a one-line warning and skip archival entirely, writing nothing.
2. Write the file (create the directory if needed) with YAML frontmatter `title`, `date`, `input_shape: concept`, `subject`, and the teaching content. If the file already exists from a prior run, overwrite it.
3. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. The project's active instructions and the description syntax observed at runtime in `jj log` win. Apply compatible Go guidance only to quality, clarity, and structure; it does not prescribe imperative mood, casing, punctuation, line wrapping, subject/body shape, or any fixed syntax. Run `jj commit -m "<message composed from the standards above>" <doc-files>`, move `<bookmark>` to `@-`, and run `jj git push --bookmark <bookmark> --remote origin`. If the files produce no new change, keep the existing link and continue.
4. Splice a head-bookmark blob URL per document into the `## New concepts` section before applying. Build the URL for the repository's actual host, for example `gh browse -n -b <bookmark> -- <path>`, and do not hardcode a public host.

If the document write, description, or push fails, warn and continue to PR creation without the link — never strand the flow between change creation and PR.

**User-runnable invocation rendering.** For the output handoffs below, default to `/ce-explain <name>`. Use `$ce-explain <name>` only when the active host is Codex or explicitly documents dollar-prefixed skill invocation. Render only the invocation as inline code and output one form only.

**Concept trailer** — when a body applied by this run contains a `## New concepts` section, print one line after the PR URL in every mode: `New concepts: <name>[, <name>]`. In interactive full-workflow runs follow it with one line per taught concept telling the user to invoke `ce-explain <name>` using the rendering rule above. No trailer when this run applied no body — including a rewrite that was declined or pipeline-defaulted to no — or no PR exists.

**Babysit handoff — default on; completion gate.** After reporting a newly-created PR URL, a successful **stack submit**, or new changes landing on an existing open PR (interactive full workflow **or** `mode:pipeline` when stack mode submitted this run), this run is **not done** until `ce-babysit-pr` owns follow-on for that PR — or an explicit skip below applies. Reporting the PR URL alone is not success. **Auto-hand off by default:** announce in one non-blocking line (e.g. "Babysitting toward merge-ready — pass `babysit:off` to skip"), then invoke `ce-babysit-pr` through the active skill mechanism with the PR URL — never ask yes/no. After **stack submit**, hand off the **bottom open non-draft** PR and include the derived posture (`posture:stack-ready` by default; `posture:stack-land` when land intent was explicit) plus stack-wide scope for `mode:pipeline` when applicable. Announce that stack babysit ownership transferred so an outer orchestrator does not start a second bare babysit on the current bookmark. **Success** = `ce-babysit-pr` has started on that PR; in `mode:pipeline`, wait for its pipeline stop and return the structured result to the caller. Never start babysit mechanics yourself (`pr-snapshot`, arming a watcher, reconstructing its loop). **Never substitute** `ci-watcher`, `gh pr checks --watch`, ad-hoc polls, or "I'll babysit later." **Handoff blocked:** if `ce-babysit-pr` cannot be loaded or started, stop and report blocked. Do not invent a parallel or narrower watch. *Off is the explicit choice:* **`babysit:off`** skips this run; **`babysit:continuous`** / **`babysit:checkpoint`** forces that mode; **`auto_babysit: false`** in workflow config (local then tracked) is a standing opt-out (same active-key semantics as `pr_teaching_section`: only exact winning active `false` disables; missing/other → default **on**; `babysit:off` overrides for this run).

**Do not fire (auto-detected, no flag needed):** `mode:pipeline` **except** when this run completed a stack-mode submit (then hand off with derived posture as above), description-only / description-update, no PR created or updated this run, non-GitHub, **draft PR** this run created/updated (author not-ready signal — announce skip; can start `ce-babysit-pr` once ready; explicit `babysit:continuous` / `babysit:checkpoint` still forces watch — pass `watch` / `checkpoint` into the invocation so its draft boundary arms), or **a head bookmark you cannot push to**. **Fork PRs are drivable — not a hard-off** when you can push the head: babysit reads state on the **base** repository and pushes fixes to the **head** repository. Hard-off only when the head is not pushable. **Soft-degrade (after successful handoff only):** checkpoint-only execution runs one tick plus a resume command; it is not a substitute for a failed handoff.

---

## Applying via gh

The body **must** be written under the Jujutsu workspace's `.tmp/` directory and passed via `--body-file <path>`. If the workspace root cannot be resolved in description-only mode, use `.tmp/` under the current project directory. Ensure `.tmp/` is ignored, remove the body file after the `gh` call, and never use `--body-file -`, stdin pipes, heredoc-to-stdin, or `--body "$(cat ...)"`.

```bash
WORKSPACE_ROOT="$(jj workspace root)"
mkdir -p "${WORKSPACE_ROOT:-.}/.tmp"
BODY_FILE="${WORKSPACE_ROOT:-.}/.tmp/pr-body.md"
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
