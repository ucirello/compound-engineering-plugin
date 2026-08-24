# Phase 0.3-1.7: prior learnings, identity, and measurement scaffolding

Read this after the spec is saved and follow it through the approval gate. The body owns the two gates in here that stop the run — the baseline gate and the user approval gate — and this file carries the procedure around them: prior-learnings search, run identity and resume detection, the optimization bookmark and scratch space, the measurement harness, the baseline, the parallelism probe, and the workspace budget.

### 0.3 Search Prior Learnings

Read `references/agents/learnings-researcher.md` and dispatch a generic subagent seeded with that local prompt to search for prior optimization work on similar topics. Do not dispatch a standalone agent by type/name. If relevant learnings exist, incorporate them into the approach.

### 0.4 Run Identity Detection

Check whether the exact local bookmark `optimize/<spec-name>` exists with `jj bookmark list`, then check for `<workspace-root>/.tmp/rocketclaw/optimize/<spec-name>/experiment-log.yaml`.

Present the user with a choice via the platform question tool:
- **Resume**: read and normalize ALL state from the experiment log on disk using the schemas' `read_compatibility` rules. Verify that its baseline, current-best, and optimization revisions resolve. For a legacy log that lacks the top-level JJ IDs, recover them as `references/persistence.md` requires rather than rejecting the log. If the log came from the legacy location, atomically publish the normalized state and sibling spec, when present, under the current state directory before continuing; leave the legacy files untouched. Recover any measured-but-unlogged experiments by scanning managed experiment workspaces for `result.yaml` markers. Then apply the body's resume rule to decide what is skipped and which gates are re-entered.
- **Fresh start**: rename any existing optimization bookmark to a timestamped `optimize-archive/<spec-name>/archived-<timestamp>` bookmark, atomically move the old local state to a timestamped sibling archive, and start from the current working-copy revision. Stop for user direction if the recorded revisions or workspace paths cannot be identified safely.

### 0.5 Create Optimization Bookmark and Scratch Space

Snapshot with `jj status`. Record the full change ID from `jj log -r @ --no-graph -T 'change_id ++ "\n"'` as `baseline_change_id`, set `optimize/<spec-name>` to that revision, and create a new empty orchestration change on top:
```bash
jj bookmark set "optimize/<spec-name>" -r @
jj new "optimize/<spec-name>"
```

Resolve scratch to `<workspace-root>/.tmp/rocketclaw/optimize/<spec-name>/`; outside Jujutsu, use `.tmp/rocketclaw/optimize/<spec-name>/` relative to the current directory. Reject symlinks at every managed path component, require current-user ownership, use mode `0700`, and stop unless `.tmp/` is ignored. Reserve transient names without overwrite and publish state updates by atomic rename within the same directory. Then create the state directory:
```bash
mkdir -p "<workspace-root-or-dot>/.tmp/rocketclaw/optimize/<spec-name>/"
```

---

## Phase 1: Measurement Scaffolding

**This phase is a HARD GATE. The user must approve baseline and parallel readiness before Phase 2.**

**Bundled scripts.** Phases 1 and 3 call helper scripts that ship in this skill's `scripts/` directory (`measure.sh`, `decide.mjs`, `parallel-probe.sh`, `experiment-workspace.sh`). The Bash tool's working directory is the user's project, not the skill directory, so a bare `scripts/<name>` path will not resolve — invoke each by the skill's own absolute path. Every runnable block below already sets `SKILL_DIR` inline (shell state does not persist between Bash tool calls, so each block must carry it); just replace the `<absolute path …>` placeholder with the directory you loaded this `ce-optimize` SKILL.md from before running. The shape:

```bash
SKILL_DIR="<absolute path of the directory containing this SKILL.md>";
bash "$SKILL_DIR/scripts/<name>"
```

### 1.1 Baseline Gate

The body owns this gate. Use `jj status` and `jj diff --summary -r <baseline_change_id>` to identify scoped edits in the recorded baseline. If any are accidental or their inclusion is ambiguous, name them and ask the user whether to keep them in the baseline or move them to a separate Jujutsu change. Do not dispatch experiments until the baseline content is intentional and the orchestration change is empty.

### 1.2 Build or Validate Measurement Harness

**If user provides a measurement harness** (the `measurement.command` already exists):
1. Run it once via the measurement script:
   ```bash
   SKILL_DIR="<absolute path of the directory containing this SKILL.md>";
   bash "$SKILL_DIR/scripts/measure.sh" "<measurement.command>" <timeout_seconds> "<measurement.working_directory or .>"
   ```
2. Validate the JSON output:
   - Contains keys for all degenerate gate metric names
   - Contains keys for all diagnostic metric names
   - Contains keys for every required hard objective (`metric.primary` when it is hard, plus every `metric.objectives` entry)
   - Values are numeric or boolean as expected
3. If validation fails, report what is missing and ask the user to fix the harness

**If agent must build the harness:**
1. Analyze the codebase to understand the current approach and what should be measured
2. Build an evaluation script (e.g., `evaluate.py`, `evaluate.sh`, or equivalent)
3. Add the evaluation script path to `scope.immutable` -- the experiment agent must not modify it
4. Run it once and validate the output
5. Present the harness and its output to the user for review

### 1.3 Establish Baseline

Run the measurement harness on the current code. Baseline and final confirmation always use the full configured protocol (`repeat_count` samples when mode is `repeat` or `ladder`; one run when mode is `stable`). Exploratory experiments later may spend less; the baseline must not.

**If stability mode is `repeat` or `ladder`:**
Do not start this protocol until the counts that mode uses are coherent. Repeat needs a positive `repeat_count`. Ladder needs positive `exploratory_pairs` and `confirmation_repeats` (falling back to `repeat_count`) with confirmation at least the exploratory count — the same rule `scripts/decide.mjs` uses. A repeat-mode spec does not need ladder fields.
1. Run the harness that many times (`repeat_count` in repeat mode; the coherent confirmation count in ladder mode)
2. Aggregate results using the configured aggregation method (median, mean, min, max)
3. Calculate variance across runs
4. If variance exceeds the configured comparison threshold, warn the user and suggest increasing `repeat_count`

**Spend only the measurement the current decision needs.** After Phase 1, a smoke failure is degenerate; one paired exploratory sample can reject a clearly worse candidate or mark it inconclusive; add samples only while the result is promising or inconclusive; run the full configured protocol only before keeping a candidate and for the run's final confirmation. `scripts/decide.mjs` returns that next step. When mode is `stable` or `repeat`, keep the existing full-protocol behavior.

Record the baseline in the experiment log. Persist every required hard objective under `metrics` (or `judge` when the primary is a judge score) so `decide.mjs` can load the same snapshot shape later experiments use. Gates and diagnostics stay in their own containers.
```yaml
baseline:
  timestamp: "<current ISO 8601 timestamp>"
  gates:
    <gate_name>: <value>
    ...
  metrics:
    <required_hard_objective>: { aggregate: <value>, samples: [<value>, ...] }
    ...
  diagnostics:
    <diagnostic_name>: <value>
    ...
```

If primary type is `judge`, also run the judge evaluation on baseline output to establish the starting judge score.

### 1.4 Parallelism Readiness Probe

Run the parallelism probe script:
```bash
SKILL_DIR="<absolute path of the directory containing this SKILL.md>";
bash "$SKILL_DIR/scripts/parallel-probe.sh" "<project_directory>" "<measurement.command>" "<measurement.working_directory>" <shared_files...>
```

Read the JSON output. Present any blockers to the user with suggested mitigations. Treat the probe as intentionally narrow: it should inspect the measurement command, the measurement working directory, and explicitly declared shared files, not the entire repository.

### 1.5 Workspace Budget Check

Count managed experiment workspaces:
```bash
SKILL_DIR="<absolute path of the directory containing this SKILL.md>";
bash "$SKILL_DIR/scripts/experiment-workspace.sh" count
```

If count + `execution.max_concurrent` would exceed 12:
- Warn the user
- Suggest cleaning up existing experiment workspaces or reducing `max_concurrent`
- Do NOT block -- the user may proceed at their own risk

### 1.6 Write Baseline to Disk (CP-1)

**MANDATORY CHECKPOINT.** Before presenting results to the user, write the initial experiment log with baseline metrics to disk:

1. Create the experiment log file at `<workspace-root>/.tmp/rocketclaw/optimize/<spec-name>/experiment-log.yaml`
2. Include all required top-level sections from `references/experiment-log-schema.yaml`: `spec`, `run_id`, `started_at`, `baseline_change_id`, `optimization_change_id`, `baseline`, `experiments`, and `best`
3. Seed `experiments` as an empty array and seed `best` from the baseline snapshot (use `iteration: 0`, `change_id: <baseline_change_id>`, baseline metrics, and baseline judge scores if present) so later phases have a valid current-best state to compare against
4. Optionally seed `hypothesis_backlog: []` here as well so the log shape is stable before Phase 2 populates it
5. **Verify**: read the file back and confirm the required sections are present and the baseline values match
6. Only THEN present results to the user

### 1.7 User Approval Gate

The body owns this gate — what is presented, the options and the condition on adjusting the spec, the uncapped-spend disclosure, and the rule that Phase 2 does not start without explicit approval. A resume that cannot prove the user cleared this gate runs it again, so this phase supplies the same payload then. What this phase supplies to it: the baseline's gate values, diagnostic values, and judge scores; the experiment log path; the probe results with any blockers and mitigations; the intentional-baseline confirmation; the workspace count and projection; and the estimated per-experiment judge cost against the configured cap.

---
