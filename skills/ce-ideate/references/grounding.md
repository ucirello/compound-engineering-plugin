# Phase 1 grounding

Required read before dispatching any grounding agent. This file defines the scratch-directory resolution, the per-mode dispatch sets and their prompts, web research, user-supplied research routing, and the consolidated grounding summary.

### Phase 1: Mode-Aware Grounding

Before generating ideas, gather grounding. The dispatch set depends on the mode chosen in Phase 0.3. Web research and user-supplied research handling run in all modes (skip phrases honored). Learnings runs in repo mode and elsewhere-software, and is **skipped by default in elsewhere-non-software** — `<root>/solutions/` holds engineering patterns that do not transfer to naming, narrative, personal, or non-digital business topics.

**Surprise-me grounding depth.** In surprise-me mode, grounding goes deeper than specified mode — apply the 0.2 table's `1 grounding` row, and pass issue themes as first-class input rather than a footnote when issue intelligence runs. Specified mode keeps the shallower scan: the user's named subject anchors what is relevant.

**Pre-resolve the scratch directory.** Use the absolute root returned by [`jj workspace root`](https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace-root) as `<local-root>`. Only when outside a JJ workspace, use the absolute physical working directory (`pwd -P`) instead. Inside JJ, verify the workspace's ignore rules cover `.tmp/` before writing. Generate an 8-hex `<run-id>` and substitute both values below. Reuse the resulting private directory for the cache, dossiers, and Phase 2/4 checkpoints:

```bash
local_root="<local-root>"
scratch_root="${local_root%/}/.tmp/rocketclaw"
scratch_dir="$scratch_root/ce-ideate/<run-id>"
umask 077
for dir in "${local_root%/}/.tmp" "$scratch_root" "$scratch_root/ce-ideate"; do
  if [ -L "$dir" ] || ! mkdir -p -- "$dir" || [ -L "$dir" ] ||
     [ ! -d "$dir" ] || [ ! -O "$dir" ] || [ ! -w "$dir" ]; then
    printf 'Unsafe or unwritable scratch directory: %s\n' "$dir" >&2
    exit 1
  fi
done
chmod 700 "$scratch_root/ce-ideate" || exit 1
mkdir -- "$scratch_dir" || exit 1
printf '%s\n' "$scratch_dir"
```

If the run ID collides, choose another before dispatch; never reuse an existing run directory. If local scratch is unavailable, warn and proceed without scratch-dependent caching, checkpoints, dossiers, or issue intelligence; report the skipped grounding, and use Phase 4's write-failure path if scratch is needed for delivery. Never fall back to global temporary storage. Use the printed absolute path as `<scratch-dir>` throughout the run. It is **not** deleted on completion — the cache is reused across run IDs in a session, and in the no-repo case the deliverable itself is written here.

**Before either dispatch block, run the research-artifact routing test** from "User-Supplied Research Artifacts" below over any file the prompt or intake named. It has to run here, ahead of both blocks, because each one has a way to swallow an evidence file it was never told to skip: the repo scan reads a named root-level `*.md` into `User-named references`, and elsewhere-mode synthesis reads "any rich-prompt material". Without the test, a long survey or analytics export would be dispatched to synthesis *and* to a distiller, duplicating the file and polluting `Topic context`. Each file takes exactly one path.

**If that test routes anything to evidence, read `references/user-research-artifacts.md` now, before the batch below.** Distillers belong *in* the same parallel foreground batch as the other grounding agents; loading their dispatch spec after the batch has already run serializes the most expensive read in the phase behind everything else.

Run grounding agents in parallel in the **foreground** (do not background — results are needed before Phase 2):

**Repo mode dispatch:**

1. **Quick context scan** — dispatch a general-purpose subagent on the extraction tier under the model and permission rules below. Per the routing test above, any named file already classified as evidence goes on the prompt's research-artifacts line rather than into `User-named references`. Dispatch with this prompt:

   > **Grounding scope:** use the supplied project context and go directly to current patterns bearing on the focus, pain points, leverage points, applicable workflow constraints, and in surprise-me mode representative files plus bounded recent activity. The absolute workspace root is `{workspace_root}`: run `jj log` from there for commits; for any repository-scoped `gh` query, use that same root with `GIT_DIR=$(jj git root)` set successfully first. If the focus cannot be scoped, use one targeted root or workspace probe.
   >
   > Start with the files and areas named by the focus or caller context. Read the applicable current project instructions when operational rules affect the scan, `STRATEGY.md` when product alignment matters (a legacy `PRODUCT.md` or `VISION.md` only when `STRATEGY.md` is absent or lacks a meaning you need), and `CONCEPTS.md` when canonical vocabulary matters.
   >
   > If the focus names a root-level `*.md` file, read it and include its relevant content under `User-named references`. When that file is listed on the research-artifacts line below, leave its full distillation to the research agent and include only a one-line gist here.
   >
   > Return a concise summary (under 40 lines, longer if user-named references include substantive content) covering:
   >
   > - current patterns and conventions relevant to the focus
   > - pain points or gaps relevant to the focus
   > - likely leverage points
   > - relevant product strategy and boundaries, if a product doc was read
   > - `User-named references` section (when the focus hint named root-level `*.md` files)
   >
   > Keep the scan shallow. Do not analyze unrelated issues, templates, contribution guidelines, or code.
   >
   > Focus hint: {focus_hint}
   >
   > Research artifacts (gist-only under `Additional context` — do not fully read; a separate agent distills these): {research_artifact_files, or "none"}

2. **Learnings search** — when `<root>/solutions/` holds at least one markdown file, read `references/agents/learnings-researcher.md` and dispatch a generic subagent seeded with that local prompt plus a brief summary of the ideation focus. An empty or missing store has nothing to search, so skip it.

3. **Web research** (always-on; see "Web research" subsection below for skip-phrase and cache handling).

4. **Issue intelligence** (conditional) — only when issue-tracker intent was detected in **Phase 0.2**. Unlike the other grounding agents this one is **not** fire-and-forget: it is an ordered two-call protocol with a question in the middle that only you can ask, because a subagent cannot block for user input.

   **Read `references/issue-intelligence.md` before dispatching anything here.** It defines the payload of each call, the persistence contract, the scoping question's option construction and platform option-cap handling, and the exact fallback markers. The four steps below name the *sequence*, not the calls — do not compose either dispatch from them.

   Then run these four steps in order:

   **a. Scan** — dispatch the analyst in SCAN mode. It probes tracker access and persists what it fetched; it does **not** cluster.
   **b. Fall back or scope** — no reachable tracker, or fewer than 5 eligible issues, ends the lens here: log the reason, continue with the remaining grounding, and fall back to the six default frames — keeping the scaling this run already resolved and recomputing only what the frame count itself determines. Otherwise resolve the scope yourself, asking **at most one** blocking question and only on irreducible ambiguity.

   **c. Cluster** — dispatch the analyst again in CLUSTER mode with the resolved scope, reusing the scan's persisted set rather than re-fetching.
   **d. Await** — consolidation and Phase 1.5 depend on the returned themes. Do not close the consolidated grounding summary before the cluster result lands.

**Elsewhere mode dispatch (skip the codebase scan; user-supplied context is the primary grounding):**

1. **User-context synthesis** — dispatch a general-purpose sub-agent on the extraction tier to read the user-supplied context from Phase 0.4 intake plus any rich-prompt material — **excluding any file the routing test above classified as evidence**, which goes to a distiller instead and must not also reach synthesis — and return a structured grounding summary that mirrors the codebase-context shape (project shape → topic shape; notable patterns → stated constraints; pain points → user-named pain points; leverage points → opportunity hooks the context implies). This keeps Phase 2 sub-agents agnostic to grounding source.

2. **Learnings search** *(elsewhere-software only; skipped by default in elsewhere-non-software)* — read `references/agents/learnings-researcher.md` and dispatch a generic subagent seeded with that local prompt plus the topic summary in case relevant institutional knowledge exists (skill-design patterns, prior solutions in similar shape). As in repo mode, skip it when `<root>/solutions/` holds no markdown file. Skip for elsewhere-non-software: the CWD's `<root>/solutions/` is unlikely to be topically relevant for non-digital topics, and running it risks polluting generation with unrelated engineering patterns.

3. **Web research** — same as repo mode (see subsection below).

Issue intelligence does not apply in elsewhere mode. Slack research is opt-in for both modes (see "Slack context" below).

#### Web Research

Always-on for both modes. Skip when the user said "no external research", "skip web research", or equivalent in their prompt or earlier answers; in that case, omit the `web-researcher` local prompt from dispatch and note the skip in the consolidated grounding summary.

Reuse prior web research within a session via a sidecar cache — see `references/web-research-cache.md` for the cache file shape, reuse check, append behavior, and platform-degradation rules. Read it the first time the `web-researcher` local prompt would be dispatched in this run (and on every subsequent dispatch where the cache might apply).

When dispatching web research, read `references/agents/web-researcher.md` and seed a generic subagent with that prompt. Pass the focus hint, a brief planning context summary (one or two sentences), and the mode. Do not pass codebase content — the prompt operates externally. Target the generation tier under the model and permission rules below.

#### User-Supplied Research Artifacts

Applies in all modes whenever the prompt or intake names a file of *gathered evidence* — a social-listening or search-research report, survey export, analytics dump, interview notes — at any path, inside or outside the repo.

**Routing test (directive vs evidence) — apply it before dispatching the Phase 1 quick context scan.** A named file is *directive* when ideas that ignore or contradict it would be wrong (a spec, a TODO list, feedback the user wants addressed); in repo mode that is the User-named references path, and it rides in `<constraints>` at dispatch. A file is *evidence* when it is signal about the world that ideas may draw on and cite. Research artifacts are evidence: they enter the evidence layer, never `<constraints>` — engagement-ranked chatter must inform ideas, not veto them. Each file takes exactly one path, never both, and the test has to run *before* the scan so the scan knows which files to leave alone.

When the test routes a file here, the reference decides by size whether it needs a distiller at all: a small artifact folds into the grounding summary inline and dispatches nothing. **When it does route to a distiller, await that result** before closing the consolidated grounding summary. Either way its content lands under `User-supplied research`, kept distinct from web research so provenance stays visible.

Read `references/user-research-artifacts.md` and follow it for the distiller dispatch prompt, the small-vs-large handling, the scan-coordination line, and why this enriches rather than replaces web research. Do not compose the dispatch from this summary.

#### Consolidated Grounding Summary

Consolidate all dispatched results into a short grounding summary using these sections (omit any section that produced nothing). Phase 1.5 will append a `Topic axes` section to this same summary after consolidation completes:

- **Codebase context** *(repo mode)* — project shape, notable patterns, pain points, leverage points OR **Topic context** *(elsewhere mode)* — topic shape, stated constraints, user-named pain points, opportunity hooks
- **User-named references** *(repo mode)* — full content from directive files the user named. Phase 2 treats these as constraint
- **Additional context** *(repo mode)* — one-line gists of root-level markdown discovered but not named. Phase 2 treats these as background, not direction
- **Past learnings** — relevant institutional knowledge from `<root>/solutions/`
- **Issue intelligence** *(when present)* — theme summaries plus the cluster call's coverage accounting (see `references/issue-intelligence.md` §d)
- **External context** *(when web research ran)* — prior art, adjacent solutions, market signals, cross-domain analogies. Note "(reused from earlier dispatch)" when the web-research cache supplied the result instead of a fresh dispatch
- **User-supplied research** *(when present)* — dossier gists with paths, or inline content for small artifacts; kept distinct from External context so source provenance stays visible
- **Slack context** *(when present)* — organizational context

**Failure handling.** Grounding subagent failures follow "warn and proceed" — never block on grounding failure. If the web-research local prompt fails (network, tool unavailable), log a warning ("External research unavailable: {reason}. Proceeding with internal grounding only.") and continue. If elsewhere-mode intake produced no usable context, note in the grounding summary that context is thin so Phase 2 subagents can compensate with broader generation.

**Slack context** (opt-in, both modes) — never auto-dispatch. When the user asks for Slack context and Slack tools are available, read `references/agents/slack-researcher.md` and dispatch a generic subagent seeded with that local prompt plus the focus hint in parallel with other Phase 1 subagents. When tools are present but the user did not ask, mention availability in the grounding summary so they can opt in. When the user asked but no Slack tools are reachable, show the user the install hint instead.

## Model tiers (applies to every dispatch in this skill)

Sub-agent dispatch is tiered by task shape, never hardcoded to a model name:

- **Extraction tier** — retrieval and quoting work, such as the quick context scan and research distillers. Target the cheapest capable model; escalate to the generation tier when the repo is large or the stack obscure.
- **Generation tier** — evidence-driven ideation frames and basis verification. Target a mid-tier model.
- **Ceiling tier** — ceiling ideation frames, cross-cutting synthesis, and final arbitration. Inherit the orchestrator's model by omitting the model parameter.

If active user or project instructions or the live prompt name a model for a subagent, tier, or prompt asset, honor that choice where permitted. Otherwise resolve configured role routes using the ordinary `.rocketclaw/config.local.yaml` then `.rocketclaw/config.yaml` cascade in `SKILL.md`; `config.example.yml` documents the available choices, not an active override. Configured routes take precedence over default tier choices. If model selection is permitted, use `opencode.models` to resolve the exact available provider/model and supported tier or variant for the native subagent tool. If discovery cannot verify a route, inherit only when suitable and report the mismatch. Do not guess names or invoke another harness to fulfill a route.

**Delegation and model selection are separate permissions.** This loaded skill explicitly requests the dispatches below and in the phase references: under a user-or-skill delegation rule, no second authorization is needed. An unconditional prohibition, actual denial, or missing tool still applies. If model overrides require an explicit user request and there is none, or the tool does not support overrides, omit the model argument and inherit when suitable. Keep the read budgets and dossier caps; report any unfulfilled configured tier and mark any required fixed-model or cross-model coverage incomplete. Fresh context is not cross-model independence.

**Dispatch failures.** Check the effective OpenCode `experimental.subagent_depth` setting and remaining nesting capacity separately from permission. Use `opencode debug paths config` if needed to locate configuration, and consider higher-precedence settings rather than assuming a packaged default applies. Use the actual error to distinguish exhausted depth, transient concurrency capacity, delegation denial, unavailable tool, and model-argument rejection. Queue transient capacity limits; correct a pre-launch argument error at most once with a permitted, suitable invocation (e.g. inherit when allowed). Never retry a denial or work around depth via shell or another harness. Send unavailable work to the phase's stated degraded path and disclose which grounding, frames, or independent checks did not run; do not count queued or missing work as complete.

Two overrides raise the whole ideation fleet to the ceiling tier: surprise-me mode and the `go deep` depth override (Phase 0.5).

## Asking inside this phase

The issue-scoping question below is the only blocking question this phase may ask. Ask it through the host's blocking question tool, with the fallback SKILL.md Boundary 4 states.
