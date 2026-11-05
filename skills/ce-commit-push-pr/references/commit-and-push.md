# Committing and pushing

Before composing any description, including stack or archival messages, follow the runtime standards in `context.md`. Run JJ from the absolute target workspace root. Never invoke Git directly; see https://docs.jj-vcs.dev/latest/cli-reference/ .

If stack construction committed the layers, continue to Step 4; Step 5 publishes them. On the default bookmark, follow `branch-creation.md` first.

Inspect `jj status`, `jj diff`, and `jj file list`. Group naturally distinct concerns into at most 2–3 changes using whole-file groups only. Honor `exclude:<paths>` and preserve unrelated work. JJ has no staging index: use `jj commit -m "<message composed from the standards above>" -- <owned-paths>` to commit exactly the group, leaving other changes behind. Verify the resulting change and remaining working copy. Do not absorb or rewrite someone else's commits. Preserve human authorship/credit under repository-local conventions, never model/harness attribution. Include an already-known Implementation Unit U-ID as semantic context when unambiguous, using runtime repository syntax rather than a fixed suffix; do not hunt for a plan.

Apply the Project publishing gate to the exact outgoing state. Immediately before pushing, re-verify feature bookmark, remote, head repository and outgoing revision. Move only the workflow-owned bookmark with `jj bookmark set <bookmark> -r <verified-outgoing-revision>`, then `jj git push --remote <verified-remote> --bookmark <bookmark>` (`--allow-new` only for an authorized new remote bookmark). Never push the default, guess a target, or accidentally publish an empty working-copy tip. A clean already-published state is a no-op.
