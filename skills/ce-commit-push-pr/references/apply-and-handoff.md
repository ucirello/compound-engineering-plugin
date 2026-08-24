# Applying the PR, reporting, and the babysit handoff

**Description-only mode** — print the title and body. Stop unless the user asks to apply.

**New PR** (full workflow, no existing PR from Step 1) — if **Stack mode** is active, follow Submit in `references/stack-submit.md`; then report the bottom open non-draft PR URL and continue to babysit handoff. Otherwise, immediately before creating, re-run `gh pr list --head <branch> --state open --json number,url,isDraft,headRefName,headRepositoryOwner` using the publication bookmark's same-named Git branch. Target the base repo on a fork. Match owner and branch rather than assuming index 0. A non-zero re-check blocks creation until auth or connectivity is resolved. Otherwise apply with `gh pr create` and report the URL.

**Existing PR** (full workflow, found in Step 1) — if **Stack mode** is active, still follow Submit in `references/stack-submit.md` so remaining layer bookmarks and PRs synchronize. Then report the bottom open non-draft PR URL and continue to babysit handoff with derived posture. Otherwise the new changes are already on the PR from Step 3. Report the PR URL, then ask whether to rewrite the description.

- **No** — done.
- **Yes** — run Step 4 if not already done, then preview and apply (see below).

**Description update mode, or existing-PR rewrite confirmed** — preview before applying. Compare the proposed title and body with the existing PR. If identical, do not call `gh pr edit`. Otherwise report the proposed title, opening, and body length, then ask whether to apply. If declined, accept focus text for regeneration and do not apply. If confirmed, apply with `gh pr edit` and report the URL.

**Explainer archival** — runs only in full workflow, with `pr_teaching_archive` on, a composed `## New concepts` section, and the apply confirmed (new-PR create, or existing-PR rewrite accepted); a declined rewrite skips archival entirely so no unlinked document change is left behind. Resolve all paths from the workspace root gathered in Context. With two taught concepts, write one file per concept and include both in one Jujutsu change. Execute these transitions immediately before the `gh` call:

1. Check the proposed path against repository ignore rules before writing. If ignored, warn and skip archival; never force-track it.
2. Write the file (create the directory if needed) with YAML frontmatter `title`, `date`, `input_shape: concept`, `subject`, and the teaching content. If the file already exists from a prior run, overwrite it.
3. Put only those files into one Jujutsu change using explicit filesets, describe it, move the publication bookmark to include it, and push. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Repository instructions and the syntax established by `git log` always win; apply compatible Go guidance without forcing a type, scope, prefix, subject, or body. If no diff remains, the document is already part of the published history; keep the link and continue.
4. Splice a head-branch blob URL per doc into the `## New concepts` section before applying. Build the URL for the repo's actual host — e.g. `gh browse -n -b <head-branch> -- <path>` (prints the link on whatever host `gh` targets, GitHub Enterprise included) — do not hardcode `github.com`, or the link 404s on GHE.

If the document write, change creation, or push fails, warn and continue to PR creation without the link. Never strand the flow between publication and PR creation.

**User-runnable invocation rendering.** For the output handoffs below, default to `/ce-explain <name>`. Use `$ce-explain <name>` only when the active host is Codex or explicitly documents dollar-prefixed skill invocation. Render only the invocation as inline code and output one form only.

**Concept trailer** — when a body applied by this run contains a `## New concepts` section, print one line after the PR URL in every mode: `New concepts: <name>[, <name>]`. In interactive full-workflow runs follow it with one line per taught concept telling the user to invoke `ce-explain <name>` using the rendering rule above. No trailer when this run applied no body — including a rewrite that was declined or pipeline-defaulted to no — or no PR exists.

**Babysit handoff — default on; completion gate.** After a newly-created PR, a successful stack submit, or new changes on an existing open PR, this run is not done until `ce-babysit-pr` owns follow-on or an explicit skip below applies. Reporting the PR URL alone is not success. Announce the automatic handoff in one non-blocking line, then invoke the skill through the available skill-invocation mechanism; never ask yes/no.

After a stack submit, hand off the bottom open non-draft PR with the derived `posture:stack-ready` or explicitly requested `posture:stack-land`, plus stack-wide scope when a pipeline submitted the stack. Report that ownership transfer so an outer orchestrator does not start a second bare babysit for the current bookmark.

**Success** = `ce-babysit-pr` has started in an interactive run. In `mode:pipeline`, started-only is not enough for completion: wait for its pipeline stop and return the structured result. Before reporting success, render every returned typed `needs-human` residual unchanged under `## Needs your decision` and propagate the same objects to the top-level coordinator. `babysit:off` disables only new monitoring; it does not suppress a typed residual already known to this run or supplied by its caller.

Never start babysit mechanics yourself: do not run `pr-snapshot`, arm a watcher, or reconstruct the loop. Never substitute `ci-watcher`, `gh pr checks --watch`, ad-hoc polls, or a promise to babysit later. **Handoff blocked:** if the skill cannot be loaded or started, stop and report the failure. Do not invent a parallel or narrower watch.

`babysit:off` is the per-run skip. `babysit:continuous` and `babysit:checkpoint` force that mode. An active `auto_babysit: false` in `.rocketclaw` config is the standing opt-out; only the exact winning `false` disables the default, and `babysit:off` overrides for this run.

A draft-only stack submit is a hard residual before babysit when babysit is on.

**Do not fire (auto-detected, no flag needed):** `mode:pipeline` **except** when this run completed a stack-mode submit, description-only / description-update, no PR created or updated this run, non-GitHub, a draft PR this run created or updated, or a head bookmark you cannot push. Explicit `babysit:continuous` / `babysit:checkpoint` still forces draft watching. Fork PRs are drivable when the head bookmark is pushable: babysit reads the base repo and pushes fixes to the head repo. After successful handoff only, a checkpoint-limited runtime may run one tick and return a resume command; this is not a substitute for failed handoff.

## Applying via gh

The body **must** be written under `<workspace-root>/.tmp/` and passed with `--body-file`. Resolve `<workspace-root>` with `jj root`. If no Jujutsu repository exists in a description-only flow, use `.tmp/` under the current directory. Use no other storage root, stdin, or command substitution for the body; those paths can silently produce an empty body while `gh` exits 0.

Create `.tmp` if needed and write the composed Markdown verbatim to a collision-resistant file such as `<workspace-root>/.tmp/ce-pr-body-<run-id>.md`. Do not overwrite another run's file. Remove the file after the `gh` call succeeds; retain it and report its path when the call fails so recovery can reuse the exact body.

Pass the composed title as one argv value and the body path as the `--body-file` value to `gh pr create` or `gh pr edit`. Do not interpolate either through a shell command placeholder.
