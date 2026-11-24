# Feature bookmark from the default branch

Do not move the local default bookmark. Record its tip and the working change before fetching, and verify the base and head repository identities per `references/context.md`.

## Decision flow

1. Fetch the exact default branch on the verified base remote:

   ```bash
   (cd "$workspace_root" && jj git fetch --remote "exact:$base_remote" --branch "exact:$base_branch")
   ```

2. Compare the captured local default tip against the fetched `<base>@<base-remote>` with `jj log -r '<fetched-base-id>..<local-default-id>'`. Compare committed tips, not an unbookmarked working-copy child. If there are no unpushed default commits, base the feature on the fetched tip. If there are unpushed commits, show the list and ask whether to carry them or leave them on the local default. Carry only authorizes using the captured local tip as the feature's parent; leaving uses the fetched tip and does not move the local default. Pipeline leaves the default commits where they are and reports the decision; if no owned work remains or the separation is unproven, stop.
3. For a single feature, use the selected exact tip. If the editable `@` is an owned, unbookmarked working change above a different parent, use `jj rebase -r <working-change-id> --onto <selected-base-id>` only when it is safe to replay its whole pending diff and the operation won't rewrite any other work. An empty working copy can instead use `jj new <selected-base-id>` when new edits are needed. Commit the owned paths in Step 3 and attach the new feature bookmark to the committed feature tip, never to the remaining working-copy changes. If the existing work already has the selected parent, leave it there. When stack construction requests only a base decision, return the verified tip without editing `@`.

Before changing the working-copy parent, verify collisions with tracked, ignored, and untracked work, other workspace owners, and pending conflicts. If changing parents would overwrite unrelated work or combine it with the requested change, stop; ask only for a real decision in interactive mode and report the blocker in pipeline mode. Never stash, discard, move a default bookmark to detach it from `@`, or force through a conflict.

## Fetch failure fallback

If fetch fails, keep the verified local parent rather than switching to a stale remote bookmark. Only create the feature from that local lineage when the scope of its outgoing work is already known; don't use a stale comparison to classify commits. Report that base freshness was not verified. This fallback does not waive the requirement to verify the exact outgoing range and publishing authority before any push.
