# Phase 4: wrap-up

Read this at wrap-up. The body owns the post-completion options the user chooses from; this file carries what each one needs — the deferred-hypothesis presentation, the results summary, what is preserved and what is not, the mechanical-apply bar for review findings, and the cleanup rules.

## Phase 4: Wrap-Up

### 4.1 Present Deferred Hypotheses

If any hypotheses were deferred due to unapproved dependencies:
1. List them with their dependency requirements
2. Ask the user whether to approve, skip, or save for a future run
3. If approved: add to backlog and offer to re-enter Phase 3 for one more round

### 4.2 Summarize Results

Present a comprehensive summary:

```
Optimization: <spec-name>
Duration: <wall-clock time>
Total experiments: <count>
  Kept: <count> (including <runner_up_kept_count> rebased runners-up)
  Reverted: <count>
  Not selected: <count>
  Inconclusive: <count>
  Censored: <count>
  Degenerate: <count>
  Errors: <count>
  Deferred: <count>

Baseline -> Final:
  <primary_metric>: <baseline_value> -> <final_value> (<delta>)
  <gate_metrics>: ...
  <diagnostics>: ...

Judge cost: $<total_judge_cost_usd> (if applicable)

Key improvements:
  1. <kept experiment 1 hypothesis> (+<delta>)
  2. <kept experiment 2 hypothesis> (+<delta>)
  ...
```

### 4.3 Preserve and Offer Next Steps

The accepted stack is `change_id(<base_change_id>)..change_id(<best_change_id>)`. Preserve its change IDs and descriptions. The experiment log and strategy digest remain under `<workspace-root>/.tmp/ce-optimize/runs/<spec-name>/` for local resume and audit; they do not travel through Git remote interop.

Present these options after the summary:

1. **Run `ce-code-review`** on the cumulative diff selected by the stored base and best revisions. Do not describe, bookmark, or push from this step.
2. **Run `ce-compound`** to document the winning strategy as an institutional learning.
3. **Create PR** by publishing the accepted JJ stack through a Git bookmark and opening it with `gh`.
4. **Continue** — re-enter Phase 3, state re-read first.
5. **Done** — leave the JJ changes and local run state for manual review.

For option 1, load `ce-code-review` against the accepted revset, interactive or `mode:agent`, and land eligible fixes under the bar below before moving to the next option.

**Mechanical-apply bar:** apply any finding with a concrete `suggested_fix` that is a clear, reversible improvement; push back when the reviewer is wrong, noting why. Defer anything whose right fix needs a design or product decision and any finding with no concrete fix to act on. Confirm evidence still matches at `file:line` before editing. After applying, run the appropriate validation. Do not publish from this step; leave the revised JJ changes for the Create PR option.

For option 3, first ensure every revision in the accepted revset is described and conflict-free. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Repository-local active instructions and syntax observed in `git log` always win over Go guidance. Apply compatible Go guidance only to message quality, clarity, and structure; do not impose a fixed message syntax or example. Then run `jj bookmark set "optimize/<spec-name>" -r "change_id(<best_change_id>)"`. JJ maps that local bookmark to the same Git branch name, and no other local namespace is created.

Fetch the selected remote with `jj git fetch --remote <remote>`. If the local or remote bookmark is conflicted, stop and resolve the bookmark target before pushing. Push only the publication bookmark with `jj git push --remote <remote> --bookmark "optimize/<spec-name>"`. Preserve `gh` for GitHub operations. In a non-colocated JJ workspace, run `gh` with `GIT_DIR` set to the path from `jj git root`; in a colocated workspace, invoke `gh` normally. Recheck the bookmark, remote state, and existing PR immediately before creating a PR.
Option 4 (continue) re-enters Phase 3 with the current state, state re-read from disk first.

### 4.4 Cleanup

Clean up disposable local state:
```bash
# Keep the experiment log for local resume/audit on this machine.
# Remove only disposable batch artifacts after the user confirms they are no longer needed.
rm -f "$(jj root)/.tmp/ce-optimize/runs/<spec-name>/strategy-digest.md"
```

Do NOT delete the experiment log if the user may resume locally or wants a local audit trail. If they need a durable shared artifact, summarize or export the results into a tracked path before cleanup.
Do not forget an experiment workspace that is still running or is the only location of an unrecorded result marker. Forgetting a workspace does not abandon its described change; treat those as separate decisions.
