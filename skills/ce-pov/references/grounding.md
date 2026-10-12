# Grounding the POV (Phase 1 machinery)

Read this before dispatching scouts. It defines how the Ground step (SKILL.md Phase 1) runs: which model each scout uses, where scratch files go, what each scout receives, which scouts run at each tier, and how grounded facts are kept apart from unconfirmed ones.

## Model Tiers

Dispatch is tiered by task shape, never hardcoded to a model name:

- **Extraction tier** — the project-grounding scout and the precedent-&-activity scout: search-and-quote work. Use the platform's cheapest capable model only when a known override is permitted; otherwise inherit.
- **Generation tier** — the external-evidence researcher: web/docs retrieval and entailment checking. Use the platform's mid-tier model only when a known override is permitted; otherwise inherit.
- **Ceiling tier** — the final assessment stays with the agent running `ce-pov`, even when another agent delegated the task to it. That agent checks whether the evidence is sufficient, weighs skeptical findings, and produces the required result. Research subagents gather evidence; they do not make this final assessment.

**Permission and capability are separate.** This skill explicitly requests scout delegation: under a host rule allowing the user OR a loaded skill to request subagents, these instructions satisfy the skill exception without another approval. Respect an unconditional higher-priority prohibition, missing tool, or actual denial. Use OpenCode-native subagents; consult `opencode.models` and project configuration for model intent, not permission. If model overrides require an explicit user model request, omit the optional `model` argument unless that request exists. If overrides are unavailable or forbidden, use a suitable inherited model and retain read budgets; disclose any unmet tier requirement. Do not present separate same-model scouts as cross-model independence.

Verify effective nesting capacity from the runtime's discovered configuration and actual depth; a package default is not proof the consuming project adopted it. When dispatch is rejected, check whether an agent launched and classify the actual error as depth/capacity, permission, model-argument rejection, or missing tool. Correct a bad argument once before launch; do not retry a denial or evade a depth limit through shell or another harness. Capacity-limited work may remain queued or return to the parent coordinator. Bounded inline grounding is permitted here with lower stated confidence, but is not an independent peer pass; disclose unmet coverage.

Create the scratch dir once, and reuse the echoed path for every scout this run:

```bash
PROJECT_ROOT="<verified absolute target workspace root, or local project root without JJ>";
SCRATCH_ROOT="$PROJECT_ROOT/.tmp/rocketclaw";
if [ -L "$PROJECT_ROOT/.tmp" ]; then echo "unsafe local temporary parent" >&2; exit 1; fi;
if [ -L "$SCRATCH_ROOT" ]; then echo "unsafe scratch root symlink: $SCRATCH_ROOT" >&2; exit 1; fi;
(umask 077; mkdir -p "$SCRATCH_ROOT") || exit 1;
if [ -L "$SCRATCH_ROOT" ] || [ ! -O "$SCRATCH_ROOT" ]; then echo "scratch root is not owned by the current user: $SCRATCH_ROOT" >&2; exit 1; fi;
chmod 700 "$SCRATCH_ROOT" || exit 1;
SCRATCH_PARENT="$SCRATCH_ROOT/ce-pov";
[ ! -L "$SCRATCH_PARENT" ] || exit 1;
(umask 077; mkdir -p "$SCRATCH_PARENT") || exit 1;
[ ! -L "$SCRATCH_PARENT" ] && [ -O "$SCRATCH_PARENT" ] || exit 1;
chmod 700 "$SCRATCH_PARENT" || exit 1;
SCRATCH_DIR="";
for attempt in 1 2 3; do
  candidate="$SCRATCH_PARENT/$(openssl rand -hex 4)";
  if (umask 077; mkdir "$candidate"); then SCRATCH_DIR="$candidate"; break; fi;
  [ -e "$candidate" ] || exit 1;
done;
[ -n "$SCRATCH_DIR" ] || exit 1; chmod 700 "$SCRATCH_DIR" || exit 1;
echo "$SCRATCH_DIR";
```

Resolve a JJ root with `(cd "$workspace_root" && jj workspace root)`; always run JJ from the target workspace's absolute root, not with repository selection alone. Keep fallback/error artifacts under the same local `.tmp/` and ensure `.tmp/` is ignored. For repository-scoped tracker calls use `(cd "$workspace_root" && export GIT_DIR=$(jj git root) && gh ...)`. See https://docs.jj-vcs.dev/latest/cli-reference/ and https://docs.jj-vcs.dev/latest/git-experts/ . A refused or unsafe scratch directory is a blocker, not permission to use global temporary storage.

Verify the scratch path's resolved containment beneath the local project `.tmp/`
and current-user ownership/private permissions before dispatch and every artifact
read; refuse symlink redirection. Allocate a fresh run directory exclusively and
retry an allocation collision without reusing existing state.

**Scoping applies on both paths.** Use the project's active instructions already in context. If the candidate cannot be scoped from the frame and existing context, allow one targeted root or workspace probe. This holds whether this phase dispatches scouts or resolves the facts with bounded inline reads.

**Every scout prompt carries the same context.** A fresh subagent does not inherit this conversation, so fill the persona files' `{subject}` / `{scratch-dir}` placeholders at dispatch. Pass each scout the framed question (subject + intent), the named incumbent and the reversibility tier, and the resolved `<scratch-dir>` path, plus any user-supplied links for the external researcher. A scout seeded with only its generic persona grounds "some external thing" and can produce an empty or unfocused dossier.

**Which scouts run depends on the tier.** For **Tier 1** (reversible), run a single combined grounding pass: seed one subagent with `references/agents/project-grounding-scout.md` covering the candidate-specific project facts (incumbent, call-sites) at a tight read budget, and one with `references/agents/external-evidence-researcher.md`. Skip the standalone precedent scout; on this tier the project-grounding scout's **prior-decision scan** (`<root>/solutions/`, ADRs, design docs) is the precedent check, so it must run. For **Tier 2/3**, dispatch all three scouts in parallel:

- **project-grounding scout** (extraction tier) — read `references/agents/project-grounding-scout.md` and seed a generic subagent with it. Run the **candidate-specific** slice fresh: the named incumbent for *this* candidate, its call-sites/footprint, incumbent-pain, exact runtime or framework constraints that materially affect compatibility, and the project/candidate/dependency license check. Do not start with generic shape discovery; the project floor (the minimum verified project evidence a verdict needs, defined in `references/method.md`) still requires a freshly verified call-site and current compatibility evidence.
- **precedent-&-activity scout** (extraction tier) — read `references/agents/precedent-activity-scout.md` and seed a generic subagent with it. Always run its **local-doc precedent pass** (`<root>/solutions/`, ADRs, design docs — file reads, no tools needed); only its tracker/PR portion depends on a reachable tracker and is skipped, with a note, when those interfaces aren't reachable. Do **not** skip the whole scout for missing tracker access; that would drop the only path that finds a prior local adopt/reject decision.
- **external-evidence researcher** (generation tier) — read `references/agents/external-evidence-researcher.md` and seed a generic subagent with it; it runs only when web tools are reachable. **Scale its brief to the tier so Tier 3's deeper workup is real, not nominal.** At **Tier 3**, seed it with a deeper brief: a wider source net, a larger read budget, and *mandatory* two-source corroboration on every claim the verdict depends on (at Tier 3 a single-source claim cannot anchor the verdict). **Tier 2** uses the persona's standard budget and its prefer-two-sources default.

**Skip work only when nothing can reach it.** Skip a scout, or a portion of one, only when it has **no reachable interface at all**. The project-grounding scout and the precedent scout's local-doc pass are file reads and always run; the tracker/PR reads and the external researcher need tools and are skipped when those tools are absent. Let a scout that loses a tool mid-run report "unavailable" itself. Never block on a missing interface. Record it and let it lower the verdict's stated confidence, or fail the external floor in Phase 2 (Verify Grounding) when the external leg is entirely absent.

**Sort every fact by where it came from** using the returned dossiers and your own bounded inline-read observations, and keep the groups separate for Phase 2 (Verify Grounding): *observed-project-facts* and *verified-external-facts* count as grounding; *conversation-claims* and *unconfirmed-assumptions* from a warm invocation do not count until a scout or a bounded inline read of the authoritative source corroborates them. Read dossiers from their paths on demand; do not pull their bulk into this context.
