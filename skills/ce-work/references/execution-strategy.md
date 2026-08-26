# Execution Strategy

Choose serial or parallel execution from dependencies, file ownership, shared contracts, and verification interference. Isolation changes recovery mechanics, not whether overlapping work is safe.

## Safety Check

Parallelize only ready units whose dependencies are accepted and whose expected edits are disjoint across files, interfaces, migrations, lockfiles, generated/registry/config surfaces, environment singletons, and test state. Uncertainty selects serial execution. Cap a wave at 3-5 workers.

## Isolation

- Inline and shared-directory workers edit the canonical Jujutsu workspace. Give each a fileset boundary; the orchestrator reviews, verifies, splits/squashes, and describes the resulting change.
- Host-native isolated workers use the host's workspace capability only when its receipt confirms a usable isolated Jujutsu workspace. The orchestrator integrates returned revisions in dependency order.
- External cross-model workers use only the controller-owned Jujutsu workspaces and transaction in `references/cross-model-execution.md`.

Workers receive one unit, its dependencies, expected files, verification, inherited constraints, and explicit exclusions. They may edit and run focused checks within that scope. The orchestrator owns canonical integration, authoritative verification, descriptions, bookmarks, push, and shipping.

## Unit Completion

After each serial unit, inspect `jj diff -r @` against the unit scope, run authoritative checks, repair failures before starting the next unit, record verification evidence, and update the task list without editing the plan body. Finish the logical unit as a focused Jujutsu change, then start a new working-copy change for subsequent work.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Local project conventions and visible history win.

## Parallel Completion

Inspect actual Jujutsu filesets rather than trusting reported paths. Same-path edits or shared-contract contention stop automatic integration. Integrate one accepted result at a time, revalidate remaining results against the advancing canonical revision, run authoritative checks, describe the focused canonical change, and release the worker only after integration is proven.

In a shared canonical workspace, workers never describe, split, squash, rebase, bookmark, or advance changes. The orchestrator separates each owned fileset after the wave. In isolated workspaces, workers leave their working-copy changes undescribed unless the host's isolation contract explicitly requires a described revision for return; even then, the orchestrator applies local description standards before publication.

On conflict, preserve the isolated revision and either rerun it on the new base or resolve it explicitly. Never treat a conflict-free fileset application as semantic compatibility.
