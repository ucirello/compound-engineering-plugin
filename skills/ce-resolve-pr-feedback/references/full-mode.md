# Full Mode

Read this reference when Mode Detection (in SKILL.md) routes to **Full Mode** — no argument given, a PR number was provided, or a whole-PR URL (`.../pull/N` with no comment fragment) was provided. Full mode processes all unresolved threads on the PR. When the argument is a PR URL, parse the host, `OWNER/REPO`, and number from it — the host feeds the `GH_HOST` prefix below, and `OWNER/REPO` targets the correct repo for a fork→upstream PR.

The shape: **fetch once, judge centrally, fan out only the fixes.** The orchestrator (you) holds every thread from a single fetch, so the legitimacy judgment happens in your context — where you can dedup reads, spot a systematically-wrong reviewer across threads, and weigh the author's design intent. Subagents are dispatched only to *implement* fixes you've already approved. Do not fan out the judgment: spinning a subagent per thread to decide validity re-pays per-agent overhead, re-reads the same files, and throws away the cross-thread view — and you'd pay it even for threads that turn out to be skips.

## Composition Standard

At every site in this reference that composes, edits, validates, or recommends a JJ description, apply this exact sentence: Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. The sentence's `git log` wording is not an operational instruction: inspect the project's active instructions and current `jj log` history; their runtime syntax and conventions take precedence. Apply compatible Go guidance only for quality, clarity, and structure. Do not impose a fixed prefix, heading, subject, body, layout, template, example, or path inventory.

For all output, preserve each site's required facts, quoted review context, verdict semantics, and machine-readable values. Fixed fields and examples define required content rather than mandatory message syntax. Do not add product branding, generated-by text, or creator, model, provider, tool, agent, runtime, workflow, or co-author attribution.

## 1. Fetch Unresolved Threads

If no PR number was provided, identify the nearest local bookmark at or behind the working-copy change, then resolve that bookmark's PR. Do not rely on Git HEAD or implicit branch detection; a JJ workspace may expose a detached Git HEAD. If the revset returns no local bookmark or more than one plausible PR-head bookmark, stop and ask for a PR number or URL:
```bash
jj log -r 'latest(::@ & bookmarks(), 1)' --no-graph -T 'bookmarks'
gh pr view BOOKMARK --json number -q .number
```

Then fetch all feedback using the GraphQL script at [scripts/get-pr-comments](../scripts/get-pr-comments). Set `SKILL_DIR` to the absolute directory containing the SKILL.md you loaded — the Bash tool's CWD is the user's project, not that directory, and shell state does not persist between Bash calls, so set it inline in each block below that runs a bundled script. If the bundled script is missing on disk the call fails plainly; fall back to the `gh` commands shown after this block.

**GitHub Enterprise host.** The bundled `gh api graphql` scripts hit `gh`'s default host unless told otherwise, so on an enterprise PR they would wrongly target `github.com`. Derive the host: if the caller passed a full PR **URL**, take its host; otherwise read it from `gh repo view --json url -q .url`. Then — because shell state does **not** persist between separate Bash calls — pass the host as a `GH_HOST=<host>` **environment prefix inline on every bundled-script call** (`gh api` honors `GH_HOST` as the request host). A single assignment in one block does **not** carry to later Bash calls, which is why each call below shows the prefix. On `github.com`, drop the prefix entirely.

```bash
PR_HOST=$(printf '%s' "<pr-url-if-one-was-passed>" | sed -n 's#^https\?://\([^/]*\)/.*#\1#p');
[ -z "$PR_HOST" ] && PR_HOST=$(gh repo view --json url -q .url 2>/dev/null | sed -n 's#^https\?://\([^/]*\)/.*#\1#p');
echo "$PR_HOST"   # github.com -> no prefix; any other host -> prefix GH_HOST=<host> on each script call below
```

```bash
SKILL_DIR="<absolute path of the directory containing the SKILL.md you loaded>";
GH_HOST=<derived-host> bash "$SKILL_DIR/scripts/get-pr-comments" PR_NUMBER OWNER/REPO   # omit GH_HOST=<derived-host> on github.com
```

**Pass the base `OWNER/REPO`** (parsed from the PR URL, when one was given) as the second arg. `get-pr-comments` otherwise falls back to `gh repo view` in the *current workspace* — so for a fork→upstream PR handed in as a URL, omitting it would fetch review feedback from the fork (or fail) instead of the upstream base repo. Every `get-pr-comments` call below (fetch and verify) takes the same `OWNER/REPO`.

Returns a JSON object with four keys:

| Key | Contents | Has file/line? | Resolvable? |
|-----|----------|---------------|-------------|
| `pending_review` | Node ID of your own unsubmitted (PENDING) review on this PR, or `null` | n/a | n/a |
| `review_threads` | Unresolved inline code review threads (includes outdated; each carries its `isOutdated` flag so line drift can be accounted for) | Yes | Yes (GraphQL) |
| `pr_comments` | Top-level PR conversation comments (excludes PR author) | No | No |
| `review_bodies` | Review submission bodies with non-empty text (excludes PR author) | No | No |

**Stop here if `pending_review` is non-null.** Thread replies posted while you hold an unsubmitted review are absorbed into that draft: the reply call returns a comment ID and URL as if it succeeded, but nothing is visible to the reviewer until the draft is submitted. Do not proceed into steps 2-8 — the fixes would land while every reply silently disappeared. Tell the user they have an unsubmitted review on the PR, that it must be submitted or discarded before this skill can reply, and stop. Do not submit or discard it yourself; a draft review is unsent human writing.

If the script fails, fall back to:
```bash
gh pr view PR_NUMBER --json reviews,comments
gh api repos/{owner}/{repo}/pulls/PR_NUMBER/comments
```

## 2. Triage: Separate New from Pending

Before processing, classify each piece of feedback as **new** or **already handled**.

**Review threads**: Read the thread's comments. If there's a substantive reply that acknowledges the concern but defers action (e.g., "need to align on this", "going to think through this", or a reply that presents options without resolving), it's a **pending decision** -- don't re-process. If there's only the original reviewer comment(s) with no substantive response, it's **new**.

**PR comments and review bodies**: These have no resolve mechanism, so they reappear on every run. Apply two filters in order:

1. **Actionability**: Skip items that contain no actionable feedback or questions to answer. Examples: review wrapper text ("Here are some automated review suggestions..."), approvals ("this looks great!"), status badges ("Validated"), CI summaries with no follow-up asks. If there's nothing to fix, answer, or decide, it's not actionable -- drop it from the count entirely.
2. **Already replied**: For actionable items, check the PR conversation for an existing reply that quotes and addresses the feedback. If a reply already exists, skip. If not, it's new.

The distinction is about content, not who posted what. A deferral from a teammate, a previous skill run, or a manual reply all count. Similarly, actionability is about content -- bot feedback that requests a specific code change is actionable; a bot's boilerplate header wrapping those requests is not.

**Silent drop.** Non-actionable items are dropped without narration. Do not announce, list, or count dropped items in conversation, the task list, or the step 9 summary. Automated review wrappers commonly contain introductory boilerplate around any substantive findings; drop the wrapper while retaining actionable feedback. The fetch layer pre-filters only blank bodies and messages from the known PR author. All external identities and surfaces rely on this content-aware check so identity reuse or format changes cannot silently hide actionable feedback.

If there are no new items across all feedback types, skip steps 3-8 and go straight to step 9.

## 3. Consolidate & Decide (the legitimacy gate)

This is the gate. Judge every **new** item here, in your own context, before any fix is dispatched. Apply the rubric in [references/evaluation-rubric.md](evaluation-rubric.md) (read it now) across the whole batch at once.

Working over the full set lets you do what a per-thread subagent can't:
- **Dedup reads by file** — read a file once and judge all its threads together.
- **Cross-item reasoning** — cluster findings by root assumption; a source (often a bot) that's wrong in one place is suspect across its siblings; converging requests from independent reviewers are a strong fix signal.
- **Selective depth** — clear nits need only the comment plus the diff line; deep-read (callers, invariants, `jj file annotate`/PR rationale for author intent) only where a finding is contestable or the code looks deliberate. That deep read on the contestable minority is what catches a confidently-wrong reviewer.

Produce a verdict per item and sort into three lists:

- **fix-list** — `fixed` / `fixed-differently`. These get dispatched to fixers in step 4. For each, note the file/location (and for outdated threads, the resolved location or anchor) and a one-line "what to change." **Class fix:** when the cross-item pass (rubric: "A validated finding can span sites this PR itself introduced") found equivalent same-invariant sites this PR touched, record them as **one** fix-list item that enumerates every concrete location (`file:line`) and lists every feedback ID it covers — one class item → one fixer (step 4), so the sites are edited coherently and every covered thread/comment is replied-to and resolved from that single result. Enumerate only sites whose treatment is unambiguous; a site needing its own judgment stays a separate item.
- **reply-list** — `replied` / `not-addressing` / `declined`. No code change. Compose the reply text now per the rubric (you have the evidence) and carry it to step 7.
- **human-list** — `needs-human`. Compose `decision_context` now; carry to steps 7 and 9.

Create a task list of all new items through the harness's available planning capability, tagged with their verdict, so progress is visible.

**At scale.** If the batch is large (many threads spanning many files) and judging them all inline would overflow your context, process the consolidation in groups (e.g., file-clustered groups of ~8-10 threads), emitting the three lists incrementally. Don't fan the judgment out to subagents to avoid this — batch it instead.

If the fix-list is empty (all verdicts are reply/needs-human), skip steps 4-6 and go to step 7.

## 4. Fix (PARALLEL — fix-list only)

Dispatch fixers **only** for fix-list items. Reply-list and human-list items never reach a subagent.

### Dispatch

Read [references/agents/pr-comment-resolver.md](agents/pr-comment-resolver.md) and spawn a generic subagent seeded with that fixer prompt for each fix-list item. Do not dispatch a standalone agent by type/name. The fixer is a pure executor: the validity judgment is already done, so it implements and returns — it does not re-judge worthwhileness.

Each fixer receives:
- The feedback_id (thread ID or comment ID) and feedback type.
- The file path and location fields: `line`, `originalLine`, `startLine`, `originalStartLine` (for outdated threads, the resolved location/anchor from step 3).
- The reviewer's comment text.
- Your step-3 note: what to change and why it was judged valid.
- The PR number.

For `pr_comment` / `review_body` fix-list items (no file/line), the fixer identifies the relevant files from the comment text and the PR diff.

**No subagent capability — apply the fixes yourself, sequentially.** When the harness exposes no way to dispatch (or a dispatch fails), work the fix-list in this context one item at a time, using the fixer prompt as your own instructions and producing the same per-item result. This is a supported path, not a degradation to disclose as lost coverage: the legitimacy judgment already happened centrally in step 3, and fixers only *implement* changes you approved, so running them here costs parallelism and context headroom — never correctness. Keep the dispatch path's discipline: one item at a time, re-read each file before editing it, and stop to re-evaluate if implementing surfaces a contradiction (the `blocked` handling applies unchanged).

This workflow therefore does not depend on subagent authorization to complete a review. That is deliberate: it can run unattended, where a permission prompt would stall the whole loop, so its tool surface stays narrow and its fix path stays viable without dispatch.

### Fixer return format

- **verdict**: `fixed`, `fixed-differently`, or `blocked`
- **feedback_id**, **feedback_type**
- **reply_text**: markdown reply to post (quoting the relevant feedback) — omit for `blocked`
- **files_changed**: list of files modified (empty for `blocked`)
- **reason**: what was done, or the concrete contradiction for `blocked`

**Handling `blocked`.** A fixer returns `blocked` only when implementing surfaced a concrete contradiction its narrower view exposed (the change breaks a caller/test it can see, or the code isn't what the finding described). Re-evaluate it yourself with that evidence: either re-dispatch with a corrected instruction, or move it to the reply-list (`not-addressing`/`declined`) or human-list. Don't silently drop it.

### Batching and conflict avoidance

**Batching**: If the fix-list has 1-4 items, dispatch all in parallel. For 5+, batch in groups of 4.

**Conflict avoidance**: No two fixers that touch the same file run in parallel. You already know the target files from step 3 — serialize fixers that share a file (dispatch one, wait, then the next); non-overlapping items run in parallel. For a **class item**, feed the fixer its full enumerated location set and every covered feedback ID (not a single thread), and account for **all** of its sites in this check — a class fix touching files another fixer also touches must be serialized against every one of them. When one fixer handles multiple threads on the same file, it addresses them sequentially.

**Sequential fallback**: Platforms that do not support parallel dispatch run fixers sequentially.

Fixes can occasionally expand beyond their referenced file (e.g., renaming a method updates callers elsewhere). This is rare but can cause parallel fixers to collide. Step 5 (combined validation) catches test breakage; step 8 (verify) catches unresolved threads. If either surfaces inconsistent changes, re-run the affected fixers sequentially.

## 5. Validate Combined State

Aggregate `files_changed` across every fixer summary. If it's empty, skip steps 5 and 6 and proceed to step 7.

Fixers run only targeted tests on their own changes. This step runs the project's full validation **once** against the combined diff to catch cross-agent interactions that targeted runs can't see.

1. **Run the project's validation command** (test suite, type check, or whatever the project's active conventions specify). Run once, not per-agent.

2. **Green** -> proceed to step 6.

3. **Red, failures touch files fixers changed** -> one inline diagnose-and-fix pass. Re-run validation. If still red, escalate with a `needs-human` item containing the test output; do **not** record or push the change.

4. **Red, failures touch only files no fixer changed** -> treat as pre-existing. Proceed to step 6, and include a concise note in the JJ description that identifies the pre-existing failing check and says it was not addressed by this PR. Compose the note under the Composition Standard; do not force a fixed label or footer syntax.

Record the validation outcome (command run, pass/fail counts, any pre-existing failures noted) for the step 9 summary.

## 6. Record and Push

1. Inspect `jj status` and `jj diff`. Record only files reported by fixers; JJ snapshots the workspace automatically, so do not stage files. Use path-scoped `jj commit` to put those files in the described parent change while preserving all unrelated changes in the new working-copy change. Compose the description under the Composition Standard, including the PR reference and any applicable pre-existing-failure note:

```bash
jj status
jj diff
jj commit -m "<description-composed-from-runtime-conventions>" -- [files from fixer summaries]
```

2. Read the PR head bookmark, move it to the recorded parent, and validate the exact description before pushing. Do not move another bookmark or include the unrelated working-copy child:
```bash
PR_HEAD_BOOKMARK=$(gh pr view PR_NUMBER -R OWNER/REPO --json headRefName -q .headRefName);
jj bookmark set "$PR_HEAD_BOOKMARK" -r @-
jj log -r @- --no-graph -T description
jj git push --bookmark "$PR_HEAD_BOOKMARK"
```

If the bookmark cannot be identified, the selected paths cannot be isolated, or the description does not satisfy the Composition Standard, stop before pushing and report the blocker. A push is successful only when `jj git push` updates the PR head bookmark.

## 7. Reply and Resolve

After the push succeeds, post replies and resolve where applicable. Post for every handled item: fix-list items use the fixer's `reply_text`; reply-list and human-list items use the reply text you composed in step 3. A **class item** carries multiple covered feedback IDs (`feedback_ids`/`feedback_types` from its fixer) — reply to and resolve *every* one, posting the shared `reply_text` on each thread, not just the first; a covered thread left unresolved re-actionizes in the next babysit loop. The mechanism depends on the feedback type.

### Reply format

All replies follow the Composition Standard and quote the relevant part of the original feedback for continuity — the specific sentence or passage, not the entire comment if it's long. Verdict-specific semantic requirements are in [references/evaluation-rubric.md](evaluation-rubric.md) and [references/agents/pr-comment-resolver.md](agents/pr-comment-resolver.md); they are not fixed prose templates.

For `needs-human` verdicts, post the natural-sounding reply but do NOT resolve the thread. Leave it open for human input.

### Review threads

0. **Verify the thread ID** before replying. GitHub Enterprise can return inconsistent node IDs for the same thread depending on the query path. Always confirm the ID from `get-pr-comments` resolves to the correct thread using [scripts/get-thread-for-comment](../scripts/get-thread-for-comment) with the comment's numeric URL ID. Extract the numeric comment ID from the comment URL (e.g. `discussion_r2589700` → `2589700`) for the `gh api` call; if the bundled script is missing, use `gh api` to inspect the review thread instead:
```bash
SKILL_DIR="<absolute path of the directory containing the SKILL.md you loaded>";
GH_HOST=<derived-host> GH_REPO=OWNER/REPO gh api repos/{owner}/{repo}/pulls/comments/COMMENT_ID --jq .node_id
GH_HOST=<derived-host> bash "$SKILL_DIR/scripts/get-thread-for-comment" PR_NUMBER COMMENT_NODE_ID OWNER/REPO
```
The returned `id` is the authoritative thread ID to use for reply and resolve. If it differs from what `get-pr-comments` returned, use the one from this script.

1. **Reply** using [scripts/reply-to-pr-thread](../scripts/reply-to-pr-thread). If the bundled script is missing, reply with `gh api --method POST repos/{owner}/{repo}/pulls/PR_NUMBER/comments/COMMENT_ID/replies -f body=...` against the thread's first comment — never `gh pr review` or a `/reviews` POST, which open an unsubmitted draft review that swallows this reply and every one after it:
Feed the body through a quoted heredoc, never `echo "..."` or `printf`. A reply is multi-line Markdown (a quote line, a blank line, then the response), and `echo` neither interprets `\n` nor survives a body composed with escape sequences — the reviewer then sees a single run-on line containing literal `\n` characters. The quoted delimiter (`<<'EOF'`) also stops the shell from expanding backticks, `$`, and `!` inside quoted code:
```bash
SKILL_DIR="<absolute path of the directory containing the SKILL.md you loaded>";
GH_HOST=<derived-host> bash "$SKILL_DIR/scripts/reply-to-pr-thread" THREAD_ID <<'EOF'
> the specific sentence being addressed from the reviewer's comment

<reply composed from the change and local conventions>
EOF
```
Check that the returned comment URL contains the correct `OWNER/REPO` and PR number before proceeding.

2. **Verify the posted body renders as Markdown** before resolving. Take the numeric ID from the returned URL fragment (`#discussion_r2589700` → `2589700`) and read back what GitHub actually stored:
```bash
GH_HOST=<derived-host> GH_REPO=OWNER/REPO gh api repos/{owner}/{repo}/pulls/comments/COMMENT_ID --jq .body
```
The output must show real line breaks. If instead it shows `\n` (or `\n\n`) as literal backslash-n characters inside one line, the body was posted escaped: **do not resolve the thread**. Fix it first by rewriting the body through a heredoc, then re-verify:
```bash
GH_HOST=<derived-host> GH_REPO=OWNER/REPO gh api --method PATCH repos/{owner}/{repo}/pulls/comments/COMMENT_ID -f body="$(cat <<'EOF'
> the specific sentence being addressed from the reviewer's comment

<reply composed from the change and local conventions>
EOF
)"
```

3. **Resolve** using [scripts/resolve-pr-thread](../scripts/resolve-pr-thread) (if the bundled script is missing, resolve the thread with `gh api` if supported):
```bash
SKILL_DIR="<absolute path of the directory containing the SKILL.md you loaded>";
GH_HOST=<derived-host> bash "$SKILL_DIR/scripts/resolve-pr-thread" THREAD_ID
```

### PR comments and review bodies

These cannot be resolved via GitHub's API. Reply with a top-level PR comment referencing the original (pass `-R OWNER/REPO` — the parsed base repo — so a fork→upstream reply posts on the watched upstream PR, not the fork namespace):

```bash
GH_HOST=<derived-host> gh pr comment PR_NUMBER -R OWNER/REPO --body "$(cat <<'EOF'
> the specific sentence being addressed from the reviewer's comment

<reply composed from the change and local conventions>
EOF
)"
```

The same escaping rule applies here: compose the body in a quoted heredoc so paragraph breaks are real newlines, and confirm the posted comment renders as Markdown rather than one line containing literal `\n`.

Include enough quoted context in the reply so the reader can follow which comment is being addressed without scrolling.

## 8. Verify

Re-fetch feedback to confirm resolution:

```bash
SKILL_DIR="<absolute path of the directory containing the SKILL.md you loaded>";
GH_HOST=<derived-host> bash "$SKILL_DIR/scripts/get-pr-comments" PR_NUMBER OWNER/REPO
```

The `review_threads` array should be empty (except `needs-human` items).

**If new threads remain**, check the iteration count for the PR rather than only this invocation. A caller may re-invoke this skill fresh each round, so a per-invocation counter never trips; count earlier review-fix changes in the PR lineage by inspecting their descriptions with `jj log -r '<base-change>::@'`, then include this run's cycles.

- **First or second fix-verify cycle**: Repeat from step 2 for the remaining threads.

- **After the second fix-verify cycle** (3rd pass would begin): Stop looping. Surface the recurring area, fixes already made, and feedback that continues to appear under the Composition Standard. Use the same `needs-human` escalation pattern -- leave threads open and present the pattern for the user to decide.

PR comments and review bodies have no resolve mechanism, so they will still appear in the output. Verify they were replied to by checking the PR conversation.

## 9. Summary

Present a concise summary under the Composition Standard. State the PR number and how many new items were resolved, then group handled items by verdict with one line per item describing *what was done* rather than only *where*. Include the validation command and outcome when a JJ change was recorded, including any pre-existing failure note. Omit empty verdict groups and do not force fixed headings or prefixes when local conventions use different language.

If any item is `needs-human`, append a decisions section. These are rare but high-signal. Each carries a `decision_context` (composed in step 3, or by a fixer's escalation): what the reviewer said, what was investigated, why it needs a decision, concrete options with tradeoffs, and a lean if any.

Present each `decision_context` directly under the Composition Standard so the user can decide quickly. Preserve the quoted feedback, investigation findings, reason a decision is needed, options with tradeoffs, and recommendation when supported; do not impose a fixed heading or message template.

The `needs-human` threads already have a natural-sounding acknowledgment reply posted and remain open on the PR.

If there are **pending decisions from a previous run** (threads detected in step 2 as already responded to but still unresolved), surface them after the new work. For each one, preserve the thread location, what remains undecided, the previous-reply link, and the available options; phrase the section under the Composition Standard rather than a fixed template.

If a blocking-question capability is available, use it to ask about all pending decisions (both new `needs-human` and previous-run pending) together. If there are only pending decisions and no new work was done, the summary is just the pending items. After the user decides, process the remaining items: fix the code, compose the reply under the Composition Standard, post it, and resolve the thread.

Fall back to presenting the decisions in the summary output and waiting in conversation only when no blocking-question capability exists or the call errors. Never silently skip. If the user does not respond, the items remain open on the PR for later handling.
