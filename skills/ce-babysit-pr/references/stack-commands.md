# Managed-stack recipes for JJ

Load this for a confirmed managed stack. GitHub owns membership and order; JJ owns local changes, bookmarks, and pushes. This works for `gh stack link` stacks without local tracking. Run every command from the absolute workspace root and give `gh` the `GIT_DIR` returned by `jj git root`. Use the actual verified tracking remote for each layer, including fork remotes.

## Discover order / next open layer

Use the snapshot's remote GraphQL stack query, ordered by `entries.position`, and its live base/head ancestry probes. A fresh `manager_status == "confirmed"` is required. A local manager view is neither necessary nor authoritative for a remotely linked stack. Unknown membership remains a residual, never an inferred manual stack.

## After an owned push on the active layer

Preserve the pre-push baseline: manager ID/order, each open layer's local bookmark, remote/head repository, remote OID, and the old immediate-parent cutoff. Re-fetch exact bookmarks, require the target still equals the delegate's pushed SHA, and require that remote membership/order and dependent tips still match the baseline. The active target is never rebased.

Process open dependents bottom-to-top. Select only that layer's verified commit slice above its old parent, prove no unrelated descendants would be rewritten, and rebase the slice onto its new immediate parent. If JJ already propagated the change, verify the resulting slice and ancestry instead of applying it again. Record the owning operation and original tips for recovery. The parameterized local recipe is:

```bash
jj rebase -r '<old-parent-oid>..<dependent-tip-oid>' -o <new-parent-oid>
jj resolve --list -r <rebased-dependent-tip>
jj bookmark move <dependent-bookmark> --to <rebased-dependent-tip>
```

Do not resolve semantic conflicts in another layer. Before any push, a conflict aborts only this owned unpublished propagation using its recorded JJ operation, after proving no concurrent work would be undone; otherwise preserve the evidence and return a precise stack-sync decision. Revalidate that the target is unchanged and every outgoing dependent is conflict-free and contains only its original layer change on the new parent. Publish exact dependent bookmarks with JJ's remote-state checks:

```bash
jj git push --remote <tracking-remote> --bookmark <dependent-bookmark>
```

Never bypass unexpected remote movement. After success or rejection, fetch and compare every open dependent with its old and expected new OID. Partial pushes are progress, not all-or-none success: name the first rejected/divergent layer, retain already-published updates, and resume only from that boundary once the cause is resolved. Re-prove manager order, ancestry, review, and CI before claiming readiness. No local gh-stack tracking is created or required.

## Land one exact prefix (only under `posture:stack-land`)

The supported [async stack merge API](https://github.com/github/gh-stack/blob/v0.1.0/docs/src/content/docs/reference/merge-api.md) merges the prefix through an explicit PR. Select the **bottom-most open settled** PR, revalidate membership/order and its head immediately before submission, then submit once:

```bash
gh api --hostname <host> --method PUT repos/<owner>/<repo>/pulls/<BOTTOM_MOST_OPEN_SETTLED_PR>/merge-async -f merge_method=squash -f merge_action=default -f sha=<verified-head-oid>
```

`default` lets GitHub apply its merge-queue rules. For an explicitly selected `merge_queue` action, omit the merge method. Do not supply generated message overrides. Persist the response and any `details.uuid` in the existing state directory. A `pending` response is polled with the read-only endpoint:

```bash
gh api --hostname <host> repos/<owner>/<repo>/pulls/<PR>/merge-async/<uuid>
```

An HTTP 409 identifies an existing request: inspect its recorded head/method/action, never resubmit blindly. `failed`, authorization/schema errors, or unavailable API become precise residuals. A lost response is reconciliation-only. `enqueued` is not merged: keep watching or return a queued residual until the PR is actually `MERGED`. Only then perform a layer transition rather than a run-level Terminal stop.

After actual merge, fetch with JJ and re-probe remote order and each remaining layer's live base. Synchronize only confirmed remaining slices with the same bounded propagation protocol above, excluding the landed slice so squash-merged commits are not replayed. Preserve drafts and unrelated work. The next layer starts with the same posture and invocation budget after its bookmark/head/base is verified. A sync failure leaves a precise residual; it does not erase the completed merge.

Under `target`/`stack-ready`, print the exact API submission command with known host, repository, PR and head OID; never execute it. Never use the ordinary single-PR merge endpoint or `gh pr merge` for a stack member.

## Incompatible local-manager commands

Do not use `gh stack rebase`, `push`, `sync`, or checkout/navigation commands: they require local Git tracking and perform Git mutations outside JJ. Their capabilities above are retained through JJ and the remote API. `gh stack merge <number>` can work remotely but interprets a number as a stack number first, risking the wrong prefix; the explicit PR endpoint avoids that ambiguity. Missing local tracking is not a reason to disable stack monitoring, propagation, or landing.
