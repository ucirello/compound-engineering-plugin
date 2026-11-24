# Grounding the POV (Phase 1 machinery)

Read this before dispatching scouts. It defines how the Ground step (SKILL.md Phase 1) runs: which model each scout uses, where scratch files go, what each scout receives, which scouts run at each tier, and how grounded facts are kept apart from unconfirmed ones.

## Model Tiers

Native OpenCode dispatch is tiered by task shape, never hardcoded to a model name:

- **Extraction tier** — the project-grounding scout and the precedent-&-activity scout: search-and-quote work. Use the platform's cheapest capable model when the harness exposes a known override; otherwise inherit.
- **Generation tier** — the external-evidence researcher: web/docs retrieval and entailment checking. Use the platform's mid-tier model when a known override exists; otherwise inherit.
- **Ceiling tier** — the final assessment stays with the agent running `ce-pov`, even when another agent delegated the task to it. That agent checks whether the evidence is sufficient, weighs skeptical findings, and produces the required result. Research subagents gather evidence; they do not make this final assessment.

Read desired scout models from active instructions and the applicable `.rocketclaw/config.yaml` and `config.local.yaml` (local overrides; `config.example.yml` documents choices). An active model instruction for a scout or tier takes precedence over the configured role, and that role takes precedence over the default tier. When an override is permitted, use `opencode.models` to resolve the exact provider/model and variant, then use the native subagent interface. Do not send a model argument merely because configuration selects one if the host requires the user to request a model explicitly. A routine tier is a cost/fit default; use a capable inherited model and retain the read budget where selection is unavailable or prohibited. Report an unmet required model/tier rather than claiming it ran, even if inherited or inline evidence is usable.

This loaded skill explicitly requests the native scout dispatch below. Under a user-or-loaded-skill rule it satisfies the skill-requested exception; no second approval is needed. Respect an unconditional higher-priority prohibition, an actual denial, and a missing native tool. Delegation permission is separate from model override permission and remaining nesting capacity.

For nesting, inspect the applicable configuration sources and precedence as in `references/cross-model-panel.md` Section 3, and check the actual tool result. Classify a failure as depth or runtime capacity, denial, model rejection, missing tool, or another launch/worker failure from observed evidence. Check whether a worker actually started. Correct a recoverable pre-launch argument once, within policy; if the model argument is forbidden, omit it only for a permissible inherited-model scout, not to retry the denied argument. Otherwise do not retry denied calls or use shell or another harness to evade the restriction. For transient capacity, wait only if the native tool queued the work and it fits the available budget. If no usable scout returns, gather its bounded evidence inline where possible, lower stated confidence for coverage lost to the failure, and disclose any remaining gap. Inline evidence is not delegated or cross-model coverage.

Resolve the absolute project directory before running the snippet. Set `project_root` to the verified result of `jj workspace root`, or to the absolute project directory for a confirmed standalone project. Create `SCRATCH_DIR` once in ignored local `.tmp/` and reuse the echoed path for all scouts and any panel:

```bash
set -eu
umask 077
case "$project_root" in /*) ;; *) exit 1 ;; esac
for dir in "$project_root/.tmp" "$project_root/.tmp/rocketclaw" "$project_root/.tmp/rocketclaw/ce-pov"; do
  if [ -L "$dir" ]; then echo "unsafe scratch symlink: $dir" >&2; exit 1; fi
  mkdir -p "$dir"
  if [ -L "$dir" ] || [ ! -O "$dir" ]; then echo "unsafe scratch owner or path: $dir" >&2; exit 1; fi
done
run_id="$(openssl rand -hex 8)"
SCRATCH_DIR="$dir/$run_id"
mkdir -m 700 "$SCRATCH_DIR"
printf '%s\n' "$SCRATCH_DIR"
```

If private local scratch is unavailable, do not switch to global storage. Use bounded inline grounding where possible; report a panel or requested write-up that cannot be completed safely.

**Scoping applies on both paths.** Use the project's active instructions already in context. If the candidate cannot be scoped from the frame and existing context, allow one targeted root or workspace probe. This holds whether this phase dispatches scouts or resolves the facts with bounded inline reads.

**Every scout prompt carries the same context.** A fresh subagent does not inherit this conversation, so fill the persona files' `{subject}` / `{scratch-dir}` placeholders at dispatch. Pass each scout the framed question (subject + intent), the named incumbent and the reversibility tier, and the resolved `<scratch-dir>` path, plus any user-supplied links for the external researcher. A scout seeded with only its generic persona grounds "some external thing" and can produce an empty or unfocused dossier.

A generic subagent is one whose whole brief is the prompt you send it. When the host's subagent tool makes you name an agent, use only a name you have seen the host list, and list its agents before the first dispatch if you have not. Pick the plain one that adds no role of its own, which still counts as a generic subagent. Never pick a specialist, such as a reviewer or worker agent, whose own role prompt, output format, or tool limits would replace or narrow your prompt.

**Which scouts run depends on the tier.** For **Tier 1** (reversible), run a single combined grounding pass: seed one subagent with `references/agents/project-grounding-scout.md` covering the candidate-specific project facts (incumbent, call-sites) at a tight read budget, and one with `references/agents/external-evidence-researcher.md`. Skip the standalone precedent scout; on this tier the project-grounding scout's **prior-decision scan** (`<root>/solutions/`, ADRs, design docs) is the precedent check, so it must run. For **Tier 2/3**, dispatch all three scouts in parallel:

- **project-grounding scout** (extraction tier) — read `references/agents/project-grounding-scout.md` and seed a generic subagent with it. Run the **candidate-specific** slice fresh: the named incumbent for *this* candidate, its call-sites/footprint, incumbent-pain, exact runtime or framework constraints that materially affect compatibility, and the project/candidate/dependency license check. Do not start with generic shape discovery; the project floor (the minimum verified project evidence a verdict needs, defined in `references/method.md`) still requires a freshly verified call-site and current compatibility evidence.
- **precedent-&-activity scout** (extraction tier) — read `references/agents/precedent-activity-scout.md` and seed a generic subagent with it. Always run its **local-doc precedent pass** (`<root>/solutions/`, ADRs, design docs — file reads, no tools needed); only its tracker/PR portion depends on a reachable tracker and is skipped, with a note, when those interfaces aren't reachable. Do **not** skip the whole scout for missing tracker access; that would drop the only path that finds a prior local adopt/reject decision.
- **external-evidence researcher** (generation tier) — read `references/agents/external-evidence-researcher.md` and seed a generic subagent with it; it runs only when web tools are reachable. **Scale its brief to the tier so Tier 3's deeper workup is real, not nominal.** At **Tier 3**, seed it with a deeper brief: a wider source net, a larger read budget, and *mandatory* two-source corroboration on every claim the verdict depends on (at Tier 3 a single-source claim cannot anchor the verdict). **Tier 2** uses the persona's standard budget and its prefer-two-sources default.

**Skip work only when nothing can reach it.** The project-grounding and local precedent passes always run, inline if the native dispatch is unavailable under the rules above; tracker/PR and external reads require a permitted reachable interface. Let a scout that loses a tool mid-run report "unavailable". Record the loss and let it lower the verdict's stated confidence, or fail the external floor in Phase 2 (Verify Grounding) when the external leg is entirely absent.

**Sort every fact by where it came from** using the returned dossiers and your own bounded inline-read observations, and keep the groups separate for Phase 2 (Verify Grounding): *observed-project-facts* and *verified-external-facts* count as grounding; *conversation-claims* and *unconfirmed-assumptions* from a warm invocation do not count until a scout or a bounded inline read of the authoritative source corroborates them. Read dossiers from their paths on demand; do not pull their bulk into this context.
