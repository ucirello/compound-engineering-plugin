# Phase 4: wrap-up

Read this at wrap-up. The SKILL.md body states the post-completion options the user chooses from. This file carries what each one needs: the deferred-hypothesis presentation, the results summary, what is preserved and what is not, the mechanical-apply bar for review findings, and the cleanup rules.

## Phase 4: Wrap-Up

### 4.1 Present Deferred Hypotheses

If any hypotheses were deferred due to unapproved dependencies:
1. List them with their dependency requirements
2. Ask the user whether to approve, skip, or save for a future run
3. If approved: add to backlog and offer to re-enter Phase 3 for one more round

### 4.2 Summarize Results

Report from the persisted forecasts and measurements, with the final state confirmed using the configured measurement protocol. The confirmation measures the recorded original baseline revision and the verified final optimization tip as one pairing, and repeats that pairing on the holdout when one is configured; the per-keep holdout pairs compare successive states and do not stand in for it. Persist both pairings in `comparisons` (the held-out one as `kind: holdout`). If confirmation is unavailable, label the final values unconfirmed and state why. A legacy log remains reportable: missing forecasts, comparison baselines, or uncertainty stay unrecorded rather than being reconstructed from the final result.

The summary must contain:

- **Overall result:** original baseline -> final for every required objective (the primary when no objectives are declared), with units, absolute change, target status, and percentage change where meaningful. A zero baseline has no defined percentage change; an ordinal judge score is reported in score points, not as a percentage improvement.
- **Opportunity -> result:** each retained change's original expected benefit beside its measured before/after result, the comparison identity and workload, and whether the evidence supports the estimate. Identify standalone versus integrated results. If the forecast and result use different baselines or workloads, label them non-comparable instead of declaring that the forecast was met or missed.
- **Evidence quality:** measurement uncertainty and confirmation status, correctness checks and their results, and any unverified constraints, including each one a revert found the harness does not check (the change the harness needs before the next run). Each reported gain names what bounds it, such as the threshold it cleared and its sample count. Report a gain with no recorded bound as inconclusive, not as a result. Report measured incremental contributions only when the corresponding reference measurements exist. Do not add percentages from successive changes or count a standalone runner-up gain as its integrated contribution; the overall gain comes from original-to-final measurement.
- **Held-out result and regressions:** the final state's holdout comparison against the original baseline (or that no holdout was configured, so the reported gain was selected and reported on the same sample), and when `measurement.per_case` is set the list of cases the baseline passed and the final state fails. An empty regression list is reported as empty; an absent one as unrecorded.
- **Remaining opportunity:** what still costs time or resources, with current evidence and whether further work appears worthwhile. Without fresh evidence, label remaining estimates stale or unknown; do not claim a new bottleneck from the old profile alone.
- **Run accounting:** stopping reason, duration, outcome counts, judge cost when applicable, estimated whole-run cost with which parts are estimates, and the log path. Preserve the existing outcome distinctions, including `Not selected: <count>`, inconclusive, censored, deferred, errors, and timeouts. Short reports may omit individual rejected experiments, but retain required-objective results and evidence limitations.

### 4.3 Preserve and Offer Next Steps

The optimization bookmark (`optimize/<spec-name>`) is preserved with all commits from kept experiments.
The experiment log and strategy digest remain under `<state-root>` for resume and audit; they do not travel with the bookmark from either root (`.context/` is ignored, and a durable store is outside the checkout).

**Export the report.** Write the 4.2 summary to `<root>/optimize/<spec-name>-report.md` (`<root>` from the body's Artifact Root rule; the user may name another tracked path). In a clean working copy directly atop the verified optimization tip, read `references/change-descriptions.md` and commit only the report with `jj commit -m "<message composed from the standards above>" "$verified_report_path"` from the absolute workspace root. Describe the report and its purpose. Verify its parent and scoped diff, then advance the optimization bookmark from the verified old tip to that commit. Report the path with the summary; a PR from that bookmark will carry the evidence.

Present these options after the summary. When the stop was reached on an unattended wake, presenting them is the point where this turn ends: `run_state.status` stays `waiting` on the user's choice, and CP-5 is written only after that choice, as the body states.

1. **Run `ce-code-review`** on the exact cumulative range from the recorded baseline to the final optimization tip. Do not commit or push from this step.
2. **Run `ce-compound`** to document the winning strategy as an institutional learning.
3. **Create PR** from the verified optimization bookmark to the default branch, using `ce-commit-push-pr`. Run any repository-scoped `gh` from the absolute workspace root with `GIT_DIR` obtained via `jj git root`, for example `(cd "$workspace_root" && git_dir="$(jj git root)" && GIT_DIR="$git_dir" gh ...)`.
4. **Continue**: re-enter Phase 3, state re-read first.
5. **Done**: leave the bookmark for manual review.

For option 1, load `ce-code-review` against the optimization tip, interactive or `mode:agent`, and apply eligible fixes under the bar below before moving to the next option.

**Mechanical-apply bar:** apply any finding with a concrete `suggested_fix` that is a clear, reversible improvement. Push back (keep, don't apply) when the reviewer is wrong, noting why. Defer anything whose right fix needs a design or product decision (architecture direction, contract shape, behavior change needing sign-off) and any finding with no concrete fix to act on. Tell the user what was deferred. Confirm evidence still matches at `file:line` before editing. After applying, run tests (at least targeted tests for what changed; broader suite for multi-file edits). Do not commit or push from this step. Leave the fixes in the working-copy change directly atop the optimization bookmark for the Create PR option.
Option 4 (continue) re-enters Phase 3 with the current state, state re-read from disk first.

### 4.4 Cleanup

Once CP-5 is written the run is over, so leave behind only what someone will still read. Remove the working files this run created under `<state-root>`: the strategy digest, the judge cache, result markers, and any scratch payloads or decision files you wrote there. Keep `experiment-log.yaml` and `spec.yaml`, tell the user where they are, and remove them too only if the user asks. A run that is not final (`waiting` or `blocked`) keeps everything, because a resume reads it.

Remove files the way this host and the user's own rules prefer, such as moving them to the trash rather than deleting them permanently when that is available. Remove only files you can name that this run created inside `<state-root>`; never compose a path to delete from a pattern or an unresolved placeholder, and leave anything you are unsure about in place and name it in the final message. Retire only authorized, disposable experiment workspaces through `references/workspaces.md`, after their required evidence has been copied and verified outside the target.

Do NOT delete the experiment log if the user may resume or wants an audit trail. The exported report in 4.3 is the durable shared artifact; the ledger is not. Unregister any wake still registered for this run.
Do NOT delete experiment worktrees that are still being referenced.
