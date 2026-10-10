# Stack-manager semantics and native JJ ownership

`gh stack <command> --help` is authoritative for the installed manager. Commands run from the target absolute workspace root with exported `GIT_DIR=$(jj git root)`. No version/upgrade prerequisite is added. Stack management is an unsupported-by-JJ hosting capability, not permission to let a Git-backed manager switch or rewrite JJ working copies. Use native JJ for all local construction, selection, fetching, bookmarks, and rebases; verify manager compatibility before any hosting mutation. If the installed manager cannot register JJ-managed layers safely, report a hard residual for required stack intent or a single-PR fallback for soft intent. Do not bypass permissions with another harness or script.

## Classifying a parent without changing the workspace

Read `gh stack view --json` and `gh pr view '<parent-pr>' --json headRefName,headRefOid,author,baseRefName,headRepositoryOwner`. A branch-only parent can be classified locally, not as proof of a remote stack. Confirm the exact head owner/repository and SHA, fetching through `jj git fetch` and verifying reachability. If absent, use hosting API metadata/diff; only a ref fetch unsupported by JJ may use the Git backend, never Git checkout/reset. Create a collision-free local bookmark at the exact verified revision. An existing name at another revision is a blocker, never permission to reset it.

Manager JSON contains trunk/currentBranch and branch entries with name/head/base/current/merged/rebase-needed/PR fields. `base` is the parent SHA last known to be contained, not necessarily its current tip. No documented ordering or top field: verify parent relations and planned order explicitly, never infer order from array position. Not-in-stack differs from unknown/auth/network/disambiguation/unavailable; preserve those residuals. Do not use checkout merely as a classifier.

Retain manager error distinctions from documented operations when interpreting an actual compatible route: exit 0 success; exit 2 not in a stack; exit 5 invalid arguments or, for add, not on top; exit 6 disambiguation required; exit 9 stacks unavailable. Follow installed help if it differs and report that difference. Never parse stderr status prose as an exit code or retry a different parent to hide a topology mismatch.

## Registering and publishing

Build JJ revisions and bookmarks bottom-to-top using `stack-submit.md`. If the manager supports external-tool linking (`gh stack link`), consult help and verify that registered layers will be visible to subsequent view/submit/merge; linking alone may be GitHub-only and supply no local tracking. Never claim successful managed ownership without readback. A manager requiring Git checkout/init/add for local tracking is a compatibility blocker, not an instruction to mutate JJ behind its back. Preserve an authored standalone parent as untouched trunk; adopt it as a managed bottom only when the current user owns it and adoption is authorized. Never silently use a different top than the parent requested.

`gh stack submit --auto [--open]` is a hosting operation only after compatibility and topology verification. `--auto` avoids title prompts; `--open` opens new PRs and existing drafts. Preserve existing drafts unless explicitly authorized to open them. A no-argument/TUI operation blocks under PTY; always pass verified explicit arguments/flags. Reconcile exact PR heads after submission.

Do not use `gh pr merge` on managed members. Landing belongs to `gh stack merge`, only under explicit land intent through `ce-babysit-pr` or the user. Keep final merge approval and manager compatibility checks intact.
