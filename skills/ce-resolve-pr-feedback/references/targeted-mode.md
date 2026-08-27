# Targeted Mode

Read this reference when Mode Detection (in SKILL.md) routes to **Targeted Mode** — a specific comment or thread URL was provided. Targeted mode addresses only that thread.

## 1. Extract Thread Context

Parse the URL to extract HOST, OWNER, REPO, PR number, and comment REST ID:
```
https://HOST/OWNER/REPO/pull/NUMBER#discussion_rCOMMENT_ID
```

**GitHub Enterprise host.** Take the host from the URL (targeted mode is always URL-triggered). Every API or bundled-script call carries `GIT_DIR="$(jj git root)"`. When the host is **not** `github.com`, also pass `GH_HOST=<host>` inline on every call (`gh api` honors `GH_HOST` as the request host) so an enterprise thread is fetched, replied to, and resolved on the right host instead of `github.com`. On `github.com`, omit only the `GH_HOST=<host>` prefix. Carry the same host into the reply/resolve calls you run from Full Mode steps 5-7.

**Step 1** -- Get comment details and GraphQL node ID via REST (cheap, single comment):
```bash
GIT_DIR="$(jj git root)" GH_HOST=<host> gh api repos/OWNER/REPO/pulls/comments/COMMENT_ID \
  --jq '{node_id, path, line, body}'   # omit GH_HOST=<host> on github.com
```

**Step 2** -- Map comment to its thread ID. Use [scripts/get-thread-for-comment](../scripts/get-thread-for-comment). Set `SKILL_DIR` to the absolute directory you loaded the ce-resolve-pr-feedback SKILL.md from — the Bash tool's CWD is the user's project, not the skill dir, and shell state does not persist between Bash calls, so set it inline. If the bundled script is missing, use Full Mode's fallback `gh` commands to inspect the PR comments:
```bash
SKILL_DIR="<absolute path of the directory containing the ce-resolve-pr-feedback SKILL.md>";
GH_HOST=<host> bash "$SKILL_DIR/scripts/get-thread-for-comment" PR_NUMBER COMMENT_NODE_ID [OWNER/REPO]
```

This fetches thread IDs and their first comment IDs (minimal fields, no bodies) and returns the matching thread with full comment details.

**Step 3** -- Check for your own unsubmitted review before doing any work. A reply posted while you hold one is absorbed into that draft: the call returns a comment ID and URL as if it succeeded, but the reviewer sees nothing until the draft is submitted. Full Mode gets this free from `get-pr-comments`; targeted mode never calls that script, so check directly (PENDING reviews are only visible to their author, so any hit is yours):
```bash
GIT_DIR="$(jj git root)" GH_HOST=<host> gh api --paginate repos/OWNER/REPO/pulls/PR_NUMBER/reviews --jq '.[] | select(.state == "PENDING") | .id'
```
`--paginate` is required: this endpoint is chronological and pages at 30, so a draft can sort past page 1. Print IDs rather than a count — `--jq` runs per page, so a count emits one number per page, but IDs simply concatenate and stay empty when there is no draft. (`--slurp` is not an option; `gh` rejects it alongside `--jq`.)

If this prints anything, stop. Tell the user they have an unsubmitted review on the PR and that it must be submitted or discarded before this skill can reply. Do not submit or discard it yourself; a draft review is unsent human writing.

## 2. Judge, Fix, Reply, Resolve

Before judgment, resolve the PR's `headRefName` and `headRefOid`, fetch its head remote with `jj git fetch`, and map that commit ID into JJ. The working-copy change must be the PR head or a direct mutable descendant created with `jj new <head-revision>`. Stop rather than displacing or combining unrelated working-copy content. Carry the resolved PR bookmark and remote into Full Mode's shared commit/push step.

Apply Full Mode step 7's independent reply/resolution completion check before judgment. When the target is already `resolution-pending`, that shared step owns the only remaining work; skip judgment, fixing, validation, and commit, then complete the missing resolution without posting again.

**Judge first (the gate).** Apply the rubric in `references/evaluation-rubric.md` to this one thread, in your own context. Account for `isOutdated` and the location fields (`line`, `originalLine`, `startLine`, `originalStartLine`). The cross-item reasoning is a no-op for one thread, but the read-depth and divert logic apply in full: inspect callers, invariants, `jj file annotate`, `jj log`, and PR rationale before accepting a contestable finding or overriding deliberate-looking code. Do not fix on the reviewer's authority alone.

**Then act on the verdict:**

- **`fixed` / `fixed-differently`** — read `references/agents/pr-comment-resolver.md` and spawn a single generic subagent seeded with that fixer prompt to implement it. Do not dispatch a standalone agent by type/name. Pass the file/location fields, comment text, and your approved change note. When dispatch is unavailable or fails, apply the fix yourself using the same prompt.
- **`replied` / `not-addressing` / `declined`** — no subagent. Compose the reply text per the rubric and proceed to reply/resolve.
- **`needs-human`** — compose `decision_context` and the natural-sounding reply per the rubric, leave the thread open (don't resolve), and present the decision to the user (use the platform's blocking question tool as in Full Mode step 9). The shared reply step below posts the reply once — do not post it here.

Then follow the same validate -> commit -> push -> reply -> resolve flow as Full Mode steps 5-7 (in `references/full-mode.md`). Skip validate/commit when no code changed.
