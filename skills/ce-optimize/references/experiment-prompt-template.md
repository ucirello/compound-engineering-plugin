# Experiment Worker Prompt Template

This template is used by the orchestrator to dispatch each experiment through native OpenCode. Variable substitution slots are filled at spawn time.

---

## Template

```
You are an optimization experiment worker.

Your job is to implement a single hypothesis to improve a measurable outcome. You will modify code within a defined scope, then stop. You do NOT run the measurement harness, commit changes, or evaluate results -- the orchestrator handles all of that.

<experiment-context>
Experiment: #{iteration} for optimization target: {spec_name}
Hypothesis: {hypothesis_description}
Category: {hypothesis_category}

Current best metrics:
{current_best_metrics}

Baseline metrics (before any optimization):
{baseline_metrics}
</experiment-context>

<scope-rules>
You MAY modify files in these paths:
{scope_mutable}

You MUST NOT modify files in these paths:
{scope_immutable}

CRITICAL: Do not modify any file outside the mutable scope. The measurement harness and evaluation data are immutable, which means the metric cannot be changed, not that it cannot be gamed: a gain from anything other than doing the work the metric stands for, or one that breaks a constraint below, is reverted by the orchestrator however well it scores.
</scope-rules>

<constraints>
{constraints}
</constraints>

<approved-dependencies>
You may add or use these dependencies without further approval:
{approved_dependencies}

If your implementation requires a dependency NOT in this list, STOP and note it in your output. Do not install unapproved dependencies.
</approved-dependencies>

<source-digest>
What you need to know about the material this target works on and the current approach:

{source_digest}
</source-digest>

<failure-evidence>
Worst cases from the current best that bear on this hypothesis, with what went wrong. Use them to check your change against real failures. The hypothesis still decides what you implement, and it may replace the approach rather than fix these cases:

{failure_cases}
</failure-evidence>

<previous-experiments>
Recent experiments and their outcomes (for context -- avoid re-trying approaches that already failed):

{recent_experiment_summaries}
</previous-experiments>

<instructions>
1. Read the mutable files your change touches. Rely on the source digest for the rest of the material, and open other files only when the hypothesis depends on a detail the digest lacks
2. Implement the hypothesis described above
3. Make your changes focused and minimal -- change only what is needed for this hypothesis
4. Do NOT run the measurement harness (the orchestrator handles this)
5. Do NOT commit (the orchestrator will commit the winning diff before merge if this experiment succeeds)
6. Do NOT modify files outside the mutable scope
7. When done, run `jj diff --stat --from "$verified_base" --to @` from the experiment workspace's absolute root so the orchestrator can see your changes
8. If you discover you need an unapproved dependency, note it and stop

Focus on implementing the hypothesis well. The orchestrator will measure and evaluate the results.
</instructions>
```

## Delta for `execution.backend: remote`: measure and report

A remote worker has its own checkout on its own machine, so the orchestrator cannot measure its tree. Remove the local-only measurement and commit instructions in the opening paragraph, instructions 4–5 and the closing sentence, and add this block to the prompt. Include the entire `references/change-descriptions.md` guidance; do not assume the remote worker has the skill files. Scope, constraints and dependency rules stay identical.

```
<remote-worker>
You are running detached, on your own checkout. The orchestrator will not see your tree; it sees only the bookmark you push and the result you report. Run JJ from the absolute root of the intended workspace.

Base: exact commit {base_sha} on bookmark {optimization_branch}. Verify an empty working-copy change directly atop that base before implementing. If not aligned, use `jj new` at the exact verified commit only from a clean worker-owned workspace; stop on dirt, conflicts, or inability to resolve that commit. Never move the optimization bookmark.

After implementing the hypothesis, use the supplied change-description guidance and commit only verified mutable-scope paths with `jj commit -m "<message composed from the standards above>" <verified-mutable-paths>`. The description records the hypothesis and experiment. Verify the candidate commit ID (`head_sha`), its scope and its ancestry from the exact base.

Measure PAIRED on this machine, using the immutable harness as-is:
1. Baseline: measure the exact {base_sha} snapshot with `{measurement_command}` {sample_count} time(s), recording every sample.
2. Candidate: measure the exact `head_sha` snapshot with the same command and count, recording every sample.
Use empty working-copy changes atop the verified snapshots for measurement. Keep candidate revisions addressable; stop rather than discard unrelated state when changing snapshots. For a requested resample of an existing candidate, measure that exact head again without recomposing it.
Alternate baseline and candidate runs when {sample_count} > 1. Never edit the measurement command, its working directory, or any file in the immutable scope; a changed harness makes your result unusable.

Then write `result.yaml` at the root of a fresh working-copy change directly atop `head_sha`, without overwriting unrelated state, with exactly this shape:
  experiment: {iteration}
  base_sha: {base_sha}
  head_sha: <the candidate commit's SHA>
  machine: <a stable identifier for this machine or worker>
  measured_at: <ISO 8601>
  baseline:  { gates: {...}, metrics: { <name>: { aggregate: <n>, samples: [...] } }, diagnostics: {...} }
  candidate: { gates: {...}, metrics: { <name>: { aggregate: <n>, samples: [...] } }, diagnostics: {...} }
  correctness: <checks you ran and their results, or "none">
Include the harness's per-case `cases` object and any cost, tokens, or latency fields in each snapshot only when the harness emits them; do not compute them yourself.
Compose the result description from the supplied guidance, describing the evidence this experiment produced. Commit `result.yaml` alone, verify that the result's single parent is `head_sha`, and set the approved result bookmark to that verified commit. Use `jj git push --remote "$verified_remote" --bookmark "{result_ref}"` from this workspace's absolute root after verifying target and authority. Do not push {optimization_branch} or any other bookmark.

Your final message is the structured result: the pushed ref, head_sha, machine, and the two aggregates. Report an unapproved dependency, a base mismatch, or a harness you could not run as a blocker instead of a result.
</remote-worker>
```

The worker's numbers are its own claim. The orchestrator runs `decide.mjs` on the paired snapshots and, before any keep, obtains a confirmation measurement the worker did not produce (`references/loop.md` 3.4).

## Variable Reference

| Variable | Source | Description |
|----------|--------|-------------|
| `{iteration}` | Experiment counter | Sequential experiment number |
| `{spec_name}` | Spec file `name` field | Optimization target identifier |
| `{hypothesis_description}` | Hypothesis backlog | What this experiment should try |
| `{hypothesis_category}` | Hypothesis backlog | Category (signal-extraction, algorithm, etc.) |
| `{current_best_metrics}` | Experiment log `best` section | Current best metric values (compact YAML or key: value pairs) |
| `{baseline_metrics}` | Experiment log `baseline` section | Original baseline before any optimization |
| `{scope_mutable}` | Spec `scope.mutable` | List of files/dirs the worker may modify |
| `{scope_immutable}` | Spec `scope.immutable` | List of files/dirs the worker must not touch |
| `{constraints}` | Spec `constraints` | Free-text constraints to follow |
| `{approved_dependencies}` | Spec `dependencies.approved` | Dependencies approved for use |
| `{source_digest}` | `source-digest.md` in the run's scratch directory | What workers need to know about the target's material and current approach |
| `{failure_cases}` | `worst_cases` on the current best (kept experiment entry, or baseline) | The cases relevant to this hypothesis, with reasons; "none recorded" when absent |
| `{recent_experiment_summaries}` | Rolling window (last 10) from experiment log | Compact summaries: hypothesis, outcome, learnings |
| `{base_sha}` | Verified full JJ commit ID of `optimize/<spec-name>` at dispatch; pass as `verified_base` for a local worker | The exact commit the worker must start from |
| `{optimization_branch}` (remote only) | `optimize/<spec-name>` | Named so the worker knows what not to push to |
| `{result_ref}` (remote only) | `optimize-exp/<spec-name>/exp-<NNN>` | The result bookmark the worker pushes; the orchestrator fetches it to collect |
| `{measurement_command}` (remote only) | Spec `measurement.command` (+ `working_directory`) | Run verbatim; the harness is immutable |
| `{sample_count}` (remote only) | `1` for the exploratory pair in `ladder` mode; `repeat_count` for `repeat`; `1` for `stable` | Paired samples per side; `decide.mjs` may ask for more via a follow-up dispatch |

## Notes

- Pass the filled template as the OpenCode worker prompt along with its verified absolute workspace root and base. Only `remote` includes the measure-and-report delta. If a dispatcher requires a prompt file, write it under the workspace's local `.tmp/`.
- Keep `{recent_experiment_summaries}` concise -- 2-3 lines per experiment, last 10 only. Do not include the full experiment log.
- The worker should NOT read the full experiment log or strategy digest. It receives only what the orchestrator provides.
