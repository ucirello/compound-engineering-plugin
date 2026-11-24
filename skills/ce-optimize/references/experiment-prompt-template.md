# Experiment Worker Prompt Template

This template is used by the orchestrator to dispatch experiments through permitted native OpenCode tools. Variable substitution slots are filled at spawn time.

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
5. Do NOT commit (the orchestrator finishes eligible candidate changes before integration)
6. Do NOT modify files outside the mutable scope
7. When done, run `jj diff --stat -r @` from the experiment workspace's absolute root so the orchestrator can see your changes
8. If you discover you need an unapproved dependency, note it and stop

Focus on implementing the hypothesis well. The orchestrator will measure and evaluate the results.
</instructions>
```

## Delta for `execution.backend: remote`: measure and report

A remote worker has its own checkout on its own machine, so the orchestrator cannot measure its tree. Append this block to the template above (inside the same prompt) and replace the local-only instructions 4, 5 and 7 with it. Scope, constraints and dependency rules are identical.

````
<remote-worker>
You are running detached in your own verified JJ workspace. Run JJ from the absolute root of the target workspace. Never invoke Git directly. The orchestrator will not see your tree; it sees the result bookmark and evidence you report.

Base: commit {base_sha} on bookmark {optimization_branch}. Before changing anything, fetch only the authorized base ref with `jj git fetch` from the verified remote if necessary, resolve the exact full ID with JJ, and verify that `@` is empty above that exact parent. If the base is available but the workspace isn't there, use `jj new {base_sha}` only from a clean, authorized workspace. If you cannot reach the exact base without changing unrelated work, stop and report that.

After implementing the hypothesis, finish the candidate change under the description rules below. Record only mutable-scope changes, with `jj commit -m "<message composed from the standards below>" -- <verified mutable filesets>`. Verify `@-` has the expected base and only the candidate diff; capture its full commit ID as `head_sha`.

Measure PAIRED on this machine, using the immutable harness as-is:
1. Baseline: in a clean workspace above the exact {base_sha}, run `{measurement_command}` {sample_count} time(s), record every sample.
2. Candidate: measure in a clean workspace above `head_sha`, run the same command the same number of times, record every sample.
Alternate baseline and candidate runs when {sample_count} > 1. Never edit the measurement command, its working directory, or any file in the immutable scope; a changed harness makes your result unusable.

Use `jj new` at exact revisions only when the current copy is safe to move, or use verified colocated JJ workspaces under the local `.tmp/` according to the lifecycle guidance supplied by the orchestrator. Preserve the candidate and verify that measurements haven't mutated tracked inputs.

Then write `result.yaml` at the repo root of your checkout with exactly this shape:
  experiment: {iteration}
  base_sha: {base_sha}
  head_sha: <the candidate commit's SHA>
  machine: <a stable identifier for this machine or worker>
  measured_at: <ISO 8601>
  baseline:  { gates: {...}, metrics: { <name>: { aggregate: <n>, samples: [...] } }, diagnostics: {...} }
  candidate: { gates: {...}, metrics: { <name>: { aggregate: <n>, samples: [...] } }, diagnostics: {...} }
  correctness: <checks you ran and their results, or "none">
Include the harness's per-case `cases` object and any cost, tokens, or latency fields in each snapshot only when the harness emits them; do not compute them yourself.
In the clean working-copy child of `head_sha`, commit `result.yaml` alone using `jj commit -m "<message composed from the standards below>" -- result.yaml`. Verify that the resulting tip changes only `result.yaml` and its sole parent is `head_sha`. Create the exact run-owned `{result_ref}` bookmark at that verified tip (don't overwrite a collision), then push only that bookmark with `jj git push --remote "<verified result remote>" --bookmark "{result_ref}"`. Do not push to {optimization_branch} or any other bookmark. Report push and remote verification failures; don't substitute a ref.

Description guidance for both the candidate and result:

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.

Before composing either description, read the full Go guide and compare several complete subjects and bodies from the verified base history using `jj log --no-graph -r '::{base_sha}' -n 10 -T 'description ++ "\n"'` from the absolute worker workspace root. Compare prefixes/package names, case, tense, subject/body separation, wrapping and issue placement. Repository-local instructions and observed syntax always win; use compatible Go guidance for clarity and structure. With no history, use explicit project/user instructions and compatible Go guidance without claiming a precedent. Describe the hypothesis and its implementation in the candidate message, and the evidence recorded for that experiment in the result message.

Go source guidance (illustrative, not the repository template):

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

Your final message is the structured result: the pushed ref, head_sha, machine, and the two aggregates. Report an unapproved dependency, a base mismatch, or a harness you could not run as a blocker instead of a result.
</remote-worker>
````

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
| `{base_sha}` (remote only) | Exact full commit ID of `optimize/<spec-name>` verified with JJ at dispatch | The commit the worker must start from and measure as baseline |
| `{optimization_branch}` (remote only) | `optimize/<spec-name>` | Named so the worker knows what not to push to |
| `{result_ref}` (remote only) | `optimize-exp/<spec-name>/exp-<NNN>` | The result bookmark the worker pushes; the orchestrator fetches it to collect |
| `{measurement_command}` (remote only) | Spec `measurement.command` (+ `working_directory`) | Run verbatim; the harness is immutable |
| `{sample_count}` (remote only) | `1` for the exploratory pair in `ladder` mode; `repeat_count` for `repeat`; `1` for `stable` | Paired samples per side; `decide.mjs` may ask for more via a follow-up dispatch |

## Notes

- For the `worktree` and configured `codex` model routes, pass the filled template as the native OpenCode subagent prompt. Only `remote` appends the measure-and-report delta; supply the authorized remote/bookmark information and `references/workspaces.md` lifecycle guidance along with it.
- Keep `{recent_experiment_summaries}` concise -- 2-3 lines per experiment, last 10 only. Do not include the full experiment log.
- The worker should NOT read the full experiment log or strategy digest. It receives only what the orchestrator provides.
