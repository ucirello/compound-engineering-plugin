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
  Kept: <count> (including <runner_up_kept_count> combined runners-up)
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

The optimization bookmark (`optimize/<spec-name>`) is preserved at the stack of kept experiment changes.
The experiment log and strategy digest remain in local `.context/...` state for resume and audit on this machine only; they do not travel with the bookmark because `.context/` is ignored.

Present these options after the summary:

1. **Run `ce-code-review`** on `jj diff --from '<baseline-change>' --to 'optimize/<spec-name>'`. Do not describe changes, move bookmarks, or push from this step.
2. **Run `ce-compound`** to document the winning strategy as an institutional learning.
3. **Create PR** from the optimization bookmark to the provider's default bookmark. Keep `gh` interoperability by exporting the colocated repository with `jj git export`, pushing the bookmark with `jj git push --bookmark 'optimize/<spec-name>'`, and creating the PR with `gh`.
4. **Continue** — re-enter Phase 3, state re-read first.
5. **Done** — leave the bookmark for manual review.

For option 1, load `ce-code-review` against the optimization bookmark, interactive or `mode:agent`, and land eligible fixes under the bar below before moving to the next option.

**Mechanical-apply bar:** apply any finding with a concrete `suggested_fix` that is a clear, reversible improvement; push back (keep, don't apply) when the reviewer is wrong, noting why. Defer anything whose right fix needs a design or product decision (architecture direction, contract shape, behavior change needing sign-off) and any finding with no concrete fix to act on — surface what was deferred. Confirm evidence still matches at `file:line` before editing. After applying, run tests (at least targeted tests for what changed; broader suite for multi-file edits). Leave the working-copy change undescribed and unpushed for the Create PR option.

Before option 3 describes or validates any review-fix change, apply this rule: Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Runtime-local description syntax and conventions win; apply Go message quality only where compatible, derive the description dynamically from the actual change, and impose no fixed prefix, type, scope, template, or example. Verify the resulting description with `jj log` before export or push.
Option 4 (continue) re-enters Phase 3 with the current state, state re-read from disk first.

### 4.4 Cleanup

Clean up scratch space:
```bash
# Keep the experiment log for local resume/audit on this machine
# Remove temporary batch artifacts
rm -f .context/ce-optimize/<spec-name>/strategy-digest.md
```

Do NOT delete the experiment log if the user may resume locally or wants a local audit trail. If they need a durable shared artifact, summarize or export the results into a tracked path before cleanup.
Do NOT delete experiment workspaces that are still being referenced.
