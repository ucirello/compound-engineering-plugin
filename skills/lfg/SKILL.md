---
name: lfg
description: "Take a request all the way to done, hands-off, through the right skills. A code change ends as an open pull request, pushed without stopping. Use only when the user explicitly asks for autonomous end-to-end work or invokes lfg directly. Use ce-plan, ce-work, ce-debug, or ce-commit-push-pr for work the user reviews step by step."
argument-hint: "[feature, bug, issue reference, or plan path; optionally assign planning and/or implementation to a native model]"
---

**Outcome.** The request reaches the end state its shape calls for, produced by the skill whose job that is, with everything unresolved recorded where the user will see it. Most requests end with that skill's result and no branch. A change to the code is the one shape with more steps of its own: it ends in an open pull request whose URL you hold, with CI decided, after being implemented, simplified, reviewed with the eligible findings applied and the rest recorded, any durable learning captured, committed, and pushed. Merging stays with the user unless they granted it for this run.

**Work source.** On the routes that change the code, nothing is implemented without a work source verified this run, and only three things qualify: an implementation-ready plan or a one-pass statement, each of which `ce-work` implements, or a `fixed` return from `ce-debug`, where the fix is the implementation. The plan is one the session identifies, as `references/intake.md` defines. Never search the plans directory for a candidate or act on a file you discovered. Never plan from scratch over an existing plan.

**Route by what the request is.** Match the request to the skill whose job it is; the host's skill list is the catalog. Read `references/intake.md` before choosing; it alone defines the routes, their precedence, what each child skill is passed, and how each return is read. In short:

- A plan path, or a plan `ce-plan` wrote this session, takes the plan route.
- A concrete report of failing or wrong behavior goes to `ce-debug`; reproducing it is that skill's job, not intake's.
- A change that hangs on a judgment the user did not settle goes to `ce-pov` first, and only a verdict that supports the change continues; a judgment with nothing to build ends at the verdict.
- Product shape with more than one plausible reading goes to `ce-brainstorm` when a human is present, and to `ce-plan` in pipeline mode when not.
- A request whose result is not a code change goes to the skill that owns that result (`ce-explain`, `ce-prototype`, `ce-pov`, `ce-ideate`, and so on); that invocation is the whole run: return its result and end.
- Any other change to the code goes to `ce-plan`, unless it can be stated, done, and verified in one pass with no decision the user would weigh; then it goes straight to `ce-work`.

**Interaction.** Ask the user only through `ce-brainstorm`, and only when a human is present. Otherwise proceed within already-authorized scope, subject to higher policy, tool permissions, genuine prohibitions, watch boundaries, and opt-outs; do not infer authorization for irreversible actions such as an ungranted merge, force-push, or data deletion. `lfg` runs from schedulers, loops, and nested orchestrators. The one other question is the routing disambiguation `references/stage-routing.md` defines: when the conversation assigns planning or implementation to a model or harness, read that file before routing; it defines native routing and sanitization, and unsupported harness requests stop safely.

**Stop, and say why, when** any of these holds:

- The work source cannot be produced: planning returned blocked, the diagnosis found no safe fix, the fix would be divergent, `ce-pov` did not support the change, or a stage assignment cannot be passed on.
- A child return is anything but complete and evidenced.
- A settled decision is invalidated.
- A project-defined shipping process falls short.

A stop leaves nothing pushed that was not already pushed.

Resolve every skill named here against the host's available-skills list and invoke that exact entry, including its namespace when present. Read `references/task-visibility.md` before starting: it defines the stage view published through the platform's task-tracking capability, the chat narration, and the completion rule that a step is done only after it ran, a child skill's return resumes the next numbered step in the same turn, and the turn ends before DONE or a stop only to wait on a wake that resumes it.

Run all repository commands with cwd set to the verified absolute JJ workspace root (`jj root`), never `jj -R`. Use native JJ, including `jj git`, never the Git executable. Repository-scoped `gh` commands require `GIT_DIR=$(jj git root)` in that workspace. Keep scratch, errors, and fallback artifacts beneath that workspace's `.tmp/`. Before any local commit/change-description composition, read and apply `references/commit-messages.md`.

This loaded skill explicitly requests the reviewers and native subagents required by its child skills; that satisfies a host's user-or-loaded-skill delegation exception without another approval question. Respect higher prohibitions and tool denials. Delegation permission is not model-override permission: if the host requires an explicit user model request, omit optional model arguments absent one, use suitable inherited reviewers, preserve configured tier intent, and disclose unmet routes. Same-model reviewers are not cross-model independence. Classify permission, nesting/capacity, and tool errors separately; do not bypass them through shell or another harness, and never call incomplete mandatory coverage complete.

**Workspace handoff.** Require children to detect and reuse existing verified isolation/name, without renaming or recreating it. For a new isolated workspace, capture local date once and keep it stable across retry/resume; normalize the caller/task/PR/revision name to `YYYYMMDD-meaningful-kebab-slug` without double prefixes, use the same destination basename, check registrations and destinations, and resolve collisions with `-2`, `-3`, never timestamps/PIDs/random. Keep its absolute owned destination under local `.tmp/`; create with `(cd "$workspace_root" && jj workspace add --colocate --name "<name>" --revision "<verified-base>" "<absolute-owned-destination>")`, then verify `(cd "$new_workspace_root" && jj git colocation status)` and adopt the session there. Preserve source/PR bookmarks and harness ownership. A native capability unable to guarantee explicit colocation and the required name is a compatibility blocker, not permission for a bridge bypass.

Completion is not workspace-deletion authorization. For explicitly authorized run-owned cleanup, stop workers, move the active session to a surviving absolute workspace root, verify exact registration/name/path/run ownership and authorization, prove integration when needed, retain recovery refs, and copy/read back needed evidence outside the target. Inspect tracked, conflicted, ignored, and untracked content; snapshots do not protect ignored/untracked files. Remove only verified disposable work with `jj workspace remove <verified-name>` from the survivor. `forget` only unregisters while preserving files. Respect harness lifecycle, preserve unrelated/ambiguous/referenced work and archive/best/recovery bookmarks, and verify both deregistration and directory disappearance. On warnings/failure preserve and report, never force filesystem deletion or Git cleanup.

## The run (routes that change the code)

1. **Produce the work source** per `references/intake.md`. On the plan route, read `references/plan-brief.md` first; it alone defines the settled-decisions brief and the artifact-root rule. Any explicit `status: blocked` return, including `settled-decision-invalidated`, stops the run. Blocked status outranks an existing artifact and is never retried. Only absence of both a blocker and a plan file `ce-plan` reported writing this run invokes `ce-plan` a second time with the same arguments, reusing the composed brief verbatim; the plan must then pass the readiness check in `references/plan-brief.md`. Record the work source for every later step. LFG never launches `/goal` directly; `ce-work` implements and returns control.

2. **Read `references/work-return.md` first**, then invoke the `ce-work` skill with `mode:return-to-caller <plan-path-from-step-1>`; a one-pass statement takes the path's place. On the defect route this step does not run: `ce-debug` already implemented and committed, and `references/debug-return.md` was its gate. Only a valid `status: complete` from `ce-work` may advance; every other status or malformed return stops the pipeline.

3. **Read `references/review-followup.md` now**; it governs steps 3 through 7. Invoke the `ce-simplify-code` skill with `mode:pipeline` and `size-cutoff:30` on the diff that file scopes; skip only the invocation for a docs-only or roughly sub-10-line change.

4. Invoke the `ce-code-review` skill with `mode:agent plan:<plan-path-from-step-1>`; with no plan, omit `plan:`. A `settled_conflict` finding whose evidence shows the settled decision cannot work (infeasible, wrong-thing, or destructive) stops the pipeline as blocked, with the finding reported, before the shipping precondition.

**Shipping precondition (every push from step 5 on).** Run `jj git remote list` once from the absolute workspace root. No remote means local-only: make every commit the steps call for, but skip every push, PR create/edit, and CI-watch action, including step 10 in full. That is terminal, not an error.

5. **Apply and persist review fixes** as that file defines. Do not proceed to the residual handoff, run browser tests, or output DONE while eligible review fixes remain only in the working tree uncommitted.

6. **Autonomous residual handoff**: whenever an unapplied actionable finding, a `settled_conflict` stamp from step 4, or a proceeded-and-flagged `settled_decision_conflicts` entry from step 2 exists, record it durably per that file: in the PR body, or in tickets or the DONE report when no PR will exist. Skip only when none of the three exists. Do not output DONE until the residuals are durable. Never block DONE on tracker filing failures once the report states them. Do not prompt the user.

7. Invoke the `ce-compound` skill with `mode:non-interactive` when the run produced durable reasoning the code, tests, and plan do not carry; that file states the full condition.

8. Invoke the `ce-test-browser` skill with `mode:pipeline`.

9. **Read `references/shipping.md` first**; it governs steps 9 through 11. Then invoke the `ce-commit-push-pr` skill with `mode:pipeline`.

10. Watch the PR to CI-decided with `ce-babysit-pr mode:pipeline <pr-url>` when an open PR exists, as `references/shipping.md` decides. Do not reimplement CI-watching here.

11. Output `<promise>DONE</promise>` after the close-out in `references/shipping.md`.
