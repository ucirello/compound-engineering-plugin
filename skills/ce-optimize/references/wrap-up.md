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
  Kept: <count> (including <runner_up_kept_count> runner-up merges)
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

The optimization stack is preserved with all retained experiment changes and a recorded current head.
The experiment log and strategy digest remain in local `.context/...` scratch space for resume and audit on this machine only; they do not travel with the changes because `.context/` is excluded through `.gitignore`.

Present these options after the summary:

1. **Run `ce-code-review`** on the cumulative diff (baseline to final), on the optimization stack. Do not describe or push from this step.
2. **Run `ce-compound`** to document the winning strategy as an institutional learning.
3. **Create PR** from the optimization stack using the project's Jujutsu bookmark and provider workflow. If the orchestration change contains review fixes, compose its description before publishing.
4. **Continue** — re-enter Phase 3, state re-read first.
5. **Done** — leave the optimization stack for manual review.

For option 1, load `ce-code-review` on the optimization stack, interactive or `mode:agent`, and land eligible fixes under the bar below before moving to the next option.

**Mechanical-apply bar:** apply any finding with a concrete `suggested_fix` that is a clear, reversible improvement; push back (keep, don't apply) when the reviewer is wrong, noting why. Defer anything whose right fix needs a design or product decision (architecture direction, contract shape, behavior change needing sign-off) and any finding with no concrete fix to act on — surface what was deferred. Confirm evidence still matches at `file:line` before editing. After applying, run tests (at least targeted tests for what changed; broader suite for multi-file edits). Do not describe or push the change from this step — leave it in the optimization stack for the Create PR option.

For option 3, compose any needed Jujutsu change description from the project's active instructions and the description syntax visible in `jj log`; those runtime conventions win. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Apply compatible Go guidance only to quality, clarity, and structure; do not impose fixed syntax or content. Then set or advance the provider-facing bookmark to the stack head before using the provider workflow.
Option 4 (continue) re-enters Phase 3 with the current state, state re-read from disk first.

### 4.4 Cleanup

Clean up scratch space:
```bash
# Keep the experiment log for local resume/audit on this machine
# Remove temporary batch artifacts
rm -f .context/optimize/<spec-name>/strategy-digest.md
```

Do NOT delete the experiment log if the user may resume locally or wants a local audit trail. If they need a durable shared artifact, summarize or export the results into a tracked path before cleanup.
Do NOT delete experiment workspaces that are still being referenced.
