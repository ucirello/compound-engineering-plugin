# Step 1: artifact root and settled-decisions brief (LFG)

## Workspace paths

Resolve `<workspace-root>` with `jj workspace root` when this workflow first needs a workspace path. A temporary artifact belongs under `<workspace-root>/.tmp/lfg/<run-id>/`. If the workspace root cannot be resolved before any repository-bound work exists, use `./.tmp/lfg/<run-id>/` as the local fallback. Keep temporary paths inside that selected `.tmp` tree, do not treat them as durable artifacts, and remove them before shipping so Jujutsu's automatic working-copy snapshot cannot include them.

## Readiness check

An explicit `status: blocked` return is terminal even when `artifact_path` names a readable plan. Preserve and report its `artifact_path` when present, `phase`, `blocker`, and `recovery_path`; do not use artifact presence to retry planning or advance to implementation.

The plan the gate checks is the exact path `ce-plan` reported writing this run under the docs artifact root `ce-plan` resolved. Do not choose, rewrite, or relocate that path. Validate that its real, symlink-resolved path stays inside that root; a missing or invalid root or path stops the pipeline. A different existing file, however closely it matches the feature, is not a written plan: a return with neither a blocker nor a reported path takes the single retry, never a stale artifact.

Read the plan metadata before continuing past step 1's gate. A plan carrying `artifact_contract: unified-plan/v1` proceeds only when it is `artifact_readiness: implementation-ready` with `execution: code`. When reading persisted plans, also accept the historical contract alias formed by prefixing `ce-` to `unified-plan/v1`; never write that alias. Every other value stops the pipeline: `artifact_readiness: requirements-only`, any unrecognized readiness value, an invalid progress-like readiness value, and `execution: knowledge-work`. An output that is not an implementation plan at all — an approach plan, an answer-seeking or universal output — stops it too, whether or not it carries the contract marker.

## Settled-decisions brief

Compose this brief from the invoking conversation and pass it with the sanitized feature request when you invoke `ce-plan`.

Contents: direction (1-2 lines); settled decisions, each with four required fields — the decision, its provenance class (`user-directed` or `user-approved`), the rejected alternative, and a one-line reason; open areas; and a standing report-conflicts line.

An entry whose rejected alternative cannot be stated demotes to a directive or open area. Scope topically — only decisions about the feature being shipped; when in doubt, demote (re-litigation is the safe floor; importing stale settlements is not). If the conversation contains no settled decisions, skip composition entirely and invoke `ce-plan` exactly as it is written in the body — no empty-brief ceremony.

The brief is transient: once `ce-plan` writes the plan, the plan's labeled KTDs are canonical. A step-1 retry reuses the composed brief verbatim — never recompose it.
