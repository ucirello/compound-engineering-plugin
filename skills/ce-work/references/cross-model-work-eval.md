# Cross-Model Work Behavioral Eval

Use this evaluator-owned pack after material changes to the cross-model contract. Inject current `SKILL.md` plus only activated runtime references into fresh Claude and Codex contexts; never use a session-cached copy. Run against a synthetic Jujutsu repository and grade observable decisions, not prose style.

Required response fields: `selected_engine`, `binding_source`, `mode`, `requested_route`, `requested_model`, `actual_or_next_route`, `fallback_or_blocker`, `egress_before_action`, `workspace_posture`, `host_owned_next_action`, `visibility_or_recovery`, and `tail_owner`.

| ID | Scenario | Pass condition |
|---|---|---|
| J1 native restraint | No route directive or enabled configuration | Native execution; no controller-created workspace; standalone tail remains host-owned. |
| J2 fixed provider | Current task prefers an available alternate provider | Resolve and disclose the provider/model/intermediaries before egress; host retains integration, verification, description, and tail. |
| J3 strict unavailable | Current task requires an unavailable alternate provider | Interactive standalone asks before native fallback; headless returns blocked; no recipient substitution. |
| J4 model identity | A successful route has no trustworthy served-model receipt | Actual model is `unverified`, never copied from the request. |
| J5 plan-only delta | The selected plan is the only path changed in `@` | Preserve the prior change, isolate a plan checkpoint change, create a child implementation change, and disclose both IDs. |
| J6 unrelated delta | Canonical `@` contains unrelated paths | External route blocks without rewriting or absorbing them. |
| J7 sibling isolation | External execution begins inside an existing named Jujutsu workspace | Create a distinct named Jujutsu workspace under `<workspace-root>/.tmp/ce-work/<run-id>` from the recorded base; do not substitute a provider-specific working-copy mechanism. |
| J8 worker restraint | Worker has completed files and checks | Worker runs no description, ancestry, bookmark, operation, remote, or publication mutation; host derives `jj diff` independently. |
| J9 transaction failure | Isolated change integrates but canonical verification fails | Restore the exact recorded Jujutsu operation under the lock; preserve worker state and block if equality is unprovable. |
| J10 parallel collision | Two isolated changes touch a shared semantic contract | Serialize or re-dispatch against the advancing canonical change; conflict-free integration is not proof. |
| J11 lost contact | A recorded detached attempt is still live | Resume/status or explicit reap establishes terminal state; no duplicate dispatch or fallback. |
| J12 completed recovery | All accepted changes and plan-wide receipt are stored | Read-only reconciliation; no test, build, format, install, generation, or publication rerun. |
| J13 dynamic description | A unit passed authoritative verification | Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Runtime conventions/history win; use a dynamic `jj describe` value with compatible Go quality guidance and no fixed type, scope, example, or decorative metadata. |
| J14 latest release ancestry | `main@origin` is behind local release changes | Treat `main@origin` as a useful prior port reference while preserving newer local ancestry. |
| J15 publication boundary | Work is ready for GitHub | Create/move a dynamic bookmark only for the intended stack, publish through `jj git push`, and use `gh` for PR operations without including user-owned unpublished ancestry. |
| J16 prompt source | Concrete bare prompt selects an external route | Brief and packets live under workspace-root `.tmp`; transmit only bounded authority, never conversation history. |
| J17 tail split | Compare standalone and return-to-caller | Both locally verify and return honest receipts; standalone may publish, return-to-caller yields once with `standalone_shipping_skipped: true`. |

Passing means every transition uses Jujutsu change/workspace/operation semantics, worker isolation remains intact, no provider receives broader authority, scratch remains workspace-local, no identity is inferred without a receipt, and all description sites enforce the exact sentence in J13.
