# Phase 0.3-1.7: prior learnings, JJ identity, and measurement scaffolding

Read this after the spec is saved and follow it through the approval gate. The body owns the two gates in here that stop the run — the baseline-state gate and the user approval gate — and this file carries the procedure around them: prior-learnings search, run identity and resume detection, JJ revisions and local state, the measurement harness, the baseline, the parallelism probe, and the workspace budget.

### 0.3 Search Prior Learnings

Read `references/agents/learnings-researcher.md` and dispatch a generic subagent seeded with that local prompt to search for prior optimization work on similar topics. Do not dispatch a standalone agent by type/name. If relevant learnings exist, incorporate them into the approach.

### 0.4 Run Identity Detection

Resolve `<workspace-root>` and check for an existing run log:

```bash
WORKSPACE_ROOT="$(jj root)";
test -f "$WORKSPACE_ROOT/.tmp/ce-optimize/runs/<spec-name>/experiment-log.yaml"
```

Present the user with a choice via the platform question tool:
- **Resume**: read all state from the experiment log on disk. Recover measured-but-unlogged experiments by scanning named experiment workspace directories for `result.yaml` markers. Resolve stored change IDs with `exactly(change_id(<id>), 1)` before use; stop if an ID is absent or divergent. Then apply the body's resume rule.
- **Fresh start**: move the old run directory under `<workspace-root>/.tmp/ce-optimize/archive/<spec-name>/<timestamp>/`, preserve any described experiment changes, and start a new log. Do not delete support or audit assets.

### 0.5 Establish Baseline And Local State

Before creating `.tmp`, ensure `/.tmp/` is present in the backing Git repository's `info/exclude`, located from `jj git root`. This local exclusion is required because JJ snapshots new files automatically; do not add run state to the working-copy change.

```bash
WORKSPACE_ROOT="$(jj root)";
mkdir -p "$WORKSPACE_ROOT/.tmp/ce-optimize/runs/<spec-name>" "$WORKSPACE_ROOT/.tmp/ce-optimize/workspaces"
```

Resolve the selected baseline to exactly one revision and record both its change ID and commit ID. Initialize `best_change_id` to that change ID. A change ID is the stable workflow identity; a commit ID is only a snapshot identifier and may change when JJ rewrites descendants.

Do not create a bookmark for a local run. JJ has no current bookmark, and bookmarks are not workspace identities. Create or move `optimize/<spec-name>` only if the user later chooses GitHub publication.

---

## Phase 1: Measurement Scaffolding

**This phase is a HARD GATE. The user must approve baseline and parallel readiness before Phase 2.**

**Bundled scripts.** Phases 1 and 3 call helper scripts that ship in this skill's `scripts/` directory (`measure.sh`, `decide.mjs`, `parallel-probe.sh`, `experiment-worktree.sh`). The last filename is retained for compatibility but manages JJ workspaces, not Git worktrees. Invoke each by the skill's own absolute path. Every runnable block below sets `SKILL_DIR` inline; replace the placeholder with the directory containing this SKILL.md.

```bash
SKILL_DIR="<absolute path of the directory containing this SKILL.md>";
bash "$SKILL_DIR/scripts/<name>"
```

### 1.1 Baseline-State Gate

The body owns this gate. Use `jj diff --summary -r @` and filter the result against `scope.mutable` and `scope.immutable`. Use `jj log -r 'conflicts() & @'` to detect first-class conflicts. JJ automatically snapshots the working copy and has no staging index, so never ask the user to stage, commit, or stash. If in-scope content exists, ask whether it is intentionally part of the baseline; otherwise ask the user to finish or move that work and start a new empty change. Stop on any unresolved conflict in the selected baseline.

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

Count existing experiment workspaces:
```bash
SKILL_DIR="<absolute path of the directory containing this SKILL.md>";
bash "$SKILL_DIR/scripts/experiment-worktree.sh" count
```

If count + `execution.max_concurrent` would exceed 12:
- Warn the user
- Suggest forgetting unused experiment workspaces or reducing `max_concurrent`
- Do NOT block -- the user may proceed at their own risk

### 1.6 Write Baseline to Disk (CP-1)

**MANDATORY CHECKPOINT.** Before presenting results to the user, write the initial experiment log with baseline metrics to disk:

1. Create the experiment log file at `<workspace-root>/.tmp/ce-optimize/runs/<spec-name>/experiment-log.yaml`
2. Include all required top-level sections from `references/experiment-log-schema.yaml`: `spec`, `run_id`, `started_at`, `baseline`, `experiments`, and `best`
3. Record `base_change_id`, `base_commit_id`, and `best_change_id`; seed `experiments` as an empty array and seed `best` from the baseline snapshot so later phases have a valid current-best revision and metric state
4. Optionally seed `hypothesis_backlog: []` here as well so the log shape is stable before Phase 2 populates it
5. **Verify**: read the file back and confirm the required sections are present and the baseline values match
6. Only THEN present results to the user

### 1.7 User Approval Gate

The body owns this gate — what is presented, the options and the condition on adjusting the spec, the uncapped-spend disclosure, and the rule that Phase 2 does not start without explicit approval. A resume that cannot prove the user cleared this gate runs it again, so this phase supplies the same payload then. What this phase supplies to it: the baseline's gate values, diagnostic values, and judge scores; the experiment log path; the probe results with any blockers and mitigations; the baseline revision and conflict confirmation; the workspace count and projection; and the estimated per-experiment judge cost against the configured cap.

---
