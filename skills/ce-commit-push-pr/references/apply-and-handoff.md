# Applying the PR, reporting, and the babysit handoff

**Description-only mode** — print the title and body. Stop unless the user asks to apply.

**New PR** (full workflow, no existing PR from Step 1) — if **Stack mode** is active, follow the Submit section of `references/stack-submit.md` instead of `GIT_DIR="$(jj git root)" gh pr create`; then report the bottom open non-draft PR URL and continue to babysit handoff. Otherwise, immediately before creating, re-run `GIT_DIR="$(jj git root)" gh pr list --head <bookmark> --state open --json number,url,isDraft,headRefName,headRepositoryOwner` with the bookmark name only and target the base repository on a fork. Match owner and the API `headRefName`; do not assume index 0. A matching PR switches to the existing-PR path, exit-0 `[]` permits creation, and non-zero blocks until authentication or connectivity is resolved. Apply with `GIT_DIR="$(jj git root)" gh pr create` and report the URL.

**Existing PR** (full workflow, found in Step 1) — if **Stack mode** is active, still follow the Submit section of `references/stack-submit.md` so remaining stack layers submit / sync (mid-stack ship is normal); then report the bottom open non-draft PR URL and continue to babysit handoff with derived posture. Otherwise the new commits are already on the PR from Step 3. Report the PR URL, then ask whether to rewrite the description.

- **No** — done.
- **Yes** — run Step 4 if not already done, then preview and apply (see below).

**Description update mode, or existing-PR rewrite confirmed** — preview before applying. First compare the proposed title and body with the existing PR. If they are identical, keep them and do not call `GIT_DIR="$(jj git root)" gh pr edit`. Otherwise ask: "New title: `<title>` (`<N>` chars). Summary leads with: `<first two sentences>`. Total body: `<L>` lines. Apply?" If declined, the user may pass focus text back for a regenerate; do not apply. If confirmed, apply with `GIT_DIR="$(jj git root)" gh pr edit` and report the URL.

**Explainer archival** — runs only in full workflow, with `pr_teaching_archive` on, a composed `## New concepts` section, and the apply confirmed (new-PR create, or existing-PR rewrite accepted); a declined rewrite skips archival entirely so no unlinked change is left behind. All paths resolve from the workspace root gathered in Context, never the CWD. With two taught concepts, write one file per concept and include both in one JJ change. Execute as explicit transitions immediately before the `gh` call:

1. Verify with the project's ignore rules that `<root>/explainers/YYYY-MM-DD-<concept-slug>.md` can be tracked. If ignored, print a one-line warning and skip archival entirely, writing nothing; never force-track it.
2. Write the file (create the directory if needed) with YAML frontmatter `title`, `date`, `input_shape: concept`, `subject`, and the teaching content. If the file already exists from a prior run, overwrite it.
3. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Project instructions and runtime `git log` syntax win. Describe and commit only those files with `jj commit <explainer-filesets> -m "<message composed from the standards above>"`, move the feature bookmark to `@-`, and push it with `jj git push --bookmark <bookmark> --remote <remote>`. If the files produce no change, they were already committed; keep the link and continue.
4. Splice a head-bookmark blob URL per document into the `## New concepts` section before applying. Build the URL for the repository's actual host, for example `GIT_DIR="$(jj git root)" gh browse -n -b <head-bookmark> -- <path>`; do not hardcode `github.com`.

If the document write, JJ commit, bookmark move, or push fails, warn and continue to PR creation without the link; never strand the flow between commit and PR.

**User-runnable invocation rendering.** For the output handoffs below, default to `/ce-explain <name>`. Use `$ce-explain <name>` only when the active host is Codex or explicitly documents dollar-prefixed skill invocation. Render only the invocation as inline code and output one form only.

**Concept trailer** — when a body applied by this run contains a `## New concepts` section, print one line after the PR URL in every mode: `New concepts: <name>[, <name>]`. In interactive full-workflow runs follow it with one line per taught concept telling the user to invoke `ce-explain <name>` using the rendering rule above. No trailer when this run applied no body — including a rewrite that was declined or pipeline-defaulted to no — or no PR exists.

**Babysit handoff — default on; completion gate.** After a newly-created PR, a successful stack submit, or new commits on an existing open PR, this run is not done until `ce-babysit-pr` owns follow-on or an explicit skip below applies. Reporting the PR URL alone is not success. Announce the automatic handoff in one non-blocking line, then invoke the skill through the host's normal skill-invocation mechanism; never ask yes/no.

After a stack submit, hand off the bottom open non-draft PR with the derived `posture:stack-ready` or explicitly requested `posture:stack-land`, plus stack-wide scope when a pipeline submitted the stack. Report that ownership transfer so an outer orchestrator does not start a second bare babysit on the current bookmark.

**Success** = `ce-babysit-pr` has started in an interactive run. In `mode:pipeline`, started-only is not enough for completion: wait for its pipeline stop and return the structured result. Before reporting success, render every returned typed `needs-human` residual unchanged under `## Needs your decision` and propagate the same objects to the top-level coordinator. `babysit:off` disables only new monitoring; it does not suppress a typed residual already known to this run or supplied by its caller.

Never start babysit mechanics yourself: do not run `pr-snapshot`, arm a watcher, or reconstruct the loop. Never substitute `ci-watcher`, `GIT_DIR="$(jj git root)" gh pr checks --watch`, ad-hoc polls, or a promise to babysit later. **Handoff blocked:** if the skill cannot be loaded or started, stop and report the failure. Do not invent a parallel or narrower watch.

`babysit:off` is the per-run skip. `babysit:continuous` and `babysit:checkpoint` force that mode. An active `auto_babysit: false` in configuration is the standing opt-out; only the exact winning `false` disables the default, and `babysit:off` overrides for this run.

A draft-only stack submit is a hard residual before babysit when babysit is on.

**Do not fire (auto-detected, no flag needed):** `mode:pipeline` except when this run completed a stack-mode submit, description-only or description-update, no PR created or updated this run, non-GitHub, a draft PR this run created or updated, or a head bookmark you cannot push. Fork PRs are drivable when the head bookmark is pushable: babysit reads state on the base repository and pushes fixes to the head repository. Explicit `babysit:continuous` or `babysit:checkpoint` still forces draft watching with the corresponding mode. A checkpoint-only run after successful handoff is not a substitute for a failed handoff.

## Applying via gh

The body **must** be written under the workspace root's `.tmp` directory and passed via `--body-file <path>`. Outside a JJ workspace, use `.tmp` under the current directory. Never use `--body-file -`, stdin pipes, heredoc-to-stdin, or `--body "$(cat ...)"`; wrappers and stdin handling can silently produce an empty PR body while `gh` still exits 0 and returns a URL.

```bash
WORKSPACE_ROOT="$(jj workspace root 2>/dev/null || pwd)";
mkdir -p "$WORKSPACE_ROOT/.tmp";
BODY_FILE="$WORKSPACE_ROOT/.tmp/pr-body-$$.md";
cat > "$BODY_FILE" <<'__PR_BODY_END__'
<the composed body markdown goes here, verbatim>
__PR_BODY_END__
```

The quoted sentinel keeps `$VAR`, backticks, and any literal `EOF` inside the body from being expanded.

For `<TITLE>`: substitute verbatim. If it contains `"`, `` ` ``, `$`, or `\`, escape them or switch to single quotes.

```bash
GIT_DIR="$(jj git root)" gh pr create --title "<TITLE>" --body-file "$BODY_FILE"   # new PR
GIT_DIR="$(jj git root)" gh pr edit   --title "<TITLE>" --body-file "$BODY_FILE"   # existing PR
```
