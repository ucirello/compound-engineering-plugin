# PR Description Writing

## The core principle

The diff is already visible on GitHub. The description exists to explain what the diff cannot show: what was impossible before and is now possible, what was broken and is now fixed, what shape changed. Cut any sentence a reader could reconstruct from the diff itself.

- Bad: "Adds `evidence-decider.ts`, modifies `ce-commit-push-pr/SKILL.md` to call it, and updates two test files."
- Good: "Evidence capture now decides automatically whether a change has observable behavior. CLI tools and libraries are now eligible alongside web UIs."

If the lead sentence describes what was moved, renamed, or added rather than what's now possible or fixed, rewrite it. This applies to every section, not just the opening — restating the diff is the failure mode this skill exists to prevent.

For user-facing bugs, run an extra before/after pass before writing the mechanism: name what the user would have seen before and what they now see instead. Only then mention the technical cause or fix, and only if it helps the reviewer understand risk. A lead like "Playback hooks now ignore late async responses" is still too mechanical if the visible bug was "old videos, thumbnails, or errors could appear after switching selections."

---

## Step Pre-A: Resolve the range and base

Two modes:

- **Current-workspace mode** (default) — describe the current working-copy change (`@`) and any bookmark pointing at it vs the repo's default base.
- **PR mode** — describe a specific PR. Triggered when the caller passes a PR ref.

For PR mode, fetch metadata first:

```bash
gh pr view <ref> --json baseRefName,headRefOid,url,body,state,isCrossRepository,headRepositoryOwner
```

If `state` is not `OPEN`, report and stop — do not invent a description. Use `baseRefName` as `<base>` and `headRefOid` as `<head>`.

For current-bookmark mode, resolve `<base>` in priority order: caller-supplied (`base:<ref>`) -> `gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'` -> try `main`/`master`/`develop` via `jj bookmark list <candidate>@origin`. If none resolve, ask the user. `<head>` is `@`.

**Base remote:** `origin` for current-workspace mode and same-repo PRs. For fork PRs, match the PR's base owner/repo against `jj git remote list`. If no local remote matches, skip to the `gh` fallback — do not diff against `origin` (wrong base).

```bash
jj git fetch --remote <base-remote> --branch <base>
jj log --no-graph -r "<base>@<base-remote>..<head>"
jj log --no-graph -T 'change_id.short() ++ " " ++ description ++ "\n"' -r "<base>@<base-remote>..<head>"   # full change descriptions for related-reference discovery
jj diff --from "<base>@<base-remote>" --to "<head>"
```

If the JJ change list is empty, report "No JJ changes to describe" and stop.

**Fallback** — use `gh pr diff <ref>` and `gh pr view <ref> --json commits` when local JJ can't reach the refs (fork PR with no matching remote, shallow clone, offline, or unrelated histories).

Note in the user-facing summary when the API fallback was used.

---

## Step A: Size the description

Match weight to weight. When in doubt, shorter wins. Subtract fix-up JJ changes (review fixes, lint, rebase resolutions) when sizing — they're invisible to the reader. Large PRs need more selectivity, not more content.

| Change profile | Description approach |
|---|---|
| Small + simple (typo, config, dep bump) | 1-2 sentences, no headers. Under ~300 characters. |
| Small + non-trivial (bugfix, behavioral change) | 3-5 sentences. No headers unless two distinct concerns. |
| Medium feature or refactor | Narrative frame, then what changed and why. Call out design decisions. |
| Large or architecturally significant | Narrative frame + 3-5 design-decision callouts + brief test summary. Target ~100 lines, cap ~150. For PRs with many mechanisms, use a Summary table; do not create an H3 per mechanism. |
| Performance improvement | Include before/after measurements as a markdown table. |

For small + simple PRs, the value-led sentence is the entire description.
For small + non-trivial bugfixes, the 3-5 sentence target still needs a user-visible before/after lead when the bug affected UI, CLI output, workflow output, or any other user-observable behavior. Concision is not a reason to skip the visible symptom.

---

## Step B: Compose the title

`type: description` or `type(scope): description`.

- Type by intent, not file extension. When `fix` and `feat` both seem to fit, default to `fix` — adding code to remedy missing behavior is `fix`. Reserve `feat` for capabilities the user could not previously accomplish. Use `refactor`/`docs`/`chore`/`perf`/`test` when more precise.
- Scope (optional): narrowest useful label. Omit when no single label adds clarity.
- Description: imperative, lowercase, under 72 chars, no trailing period.
- Match repo conventions visible in recent JJ changes.
- **Never use `!` or `BREAKING CHANGE:` without explicit user confirmation** — they trigger automated major-version bumps.

---

## Step B1: Resolve related work references

Before writing the body, make an explicit related-reference pass. Gather candidate work-item references from the user prompt, caller handoff, bookmark name, full JJ change descriptions, existing PR body, PR template, plan/debug notes, and visible URLs or IDs already in context. Preserve existing related references when rewriting a PR unless the user asks to remove them.

Classify each candidate as:

- **closing reference** — the PR fully resolves the item and the tracker's closing syntax is known.
- **non-closing reference** — the PR is related, partial, investigative, follow-up, validation-only, or the tracker semantics are unknown.
- **uncertain** — the change clearly came from a tracked bug, incident, performance investigation, alert, or log trace, but the exact ID/link or close-vs-link intent is missing. Ask the user for the reference or intent; in non-interactive flows, use a non-closing reference or omit rather than pretending to close it.

Do not invent a closing keyword. Magic words are workflow actions, not decoration. If the candidate is ambiguous, put a neutral related reference in the related-reference sentence/block or omit it; do not scatter the ID through the summary.

Do not put a non-closing reference next to close/fix/resolve/address/report wording in prose. For partial or related work, write the behavioral scope in one sentence and put the tracker ID separately. Use the table's non-closing reference labels exactly; do not substitute synonyms like `Refs`, `References`, or `Toward` unless the project's documented tracker convention requires one of those labels. For a non-closing reference, the tracker ID appears only in that related-reference sentence or block, never in the summary/opening/body prose. This avoids both accidental automation and reviewer confusion.

- Bad: "closing one corruption path from #123"
- Bad: "partial fix for #123"
- Bad: "This addresses the retry-related corruption path reported in #123."
- Good: "This covers the duplicate-row retry path; concurrent cancellation remains follow-up work."
- Good: "Related: #123"

Common syntax examples:

| Tracker | Closing reference | Non-closing reference | Notes |
|---|---|---|---|
| GitHub Issues | `Fixes #123`; cross-repo: `Fixes owner/repo#123` | `Related: #123`; cross-repo: `Related: owner/repo#123` | Closing keywords are `close(s/d)`, `fix(es/ed)`, and `resolve(s/d)`. Use closing syntax only when the PR targets the default branch and truly resolves the issue; otherwise use a non-closing reference. Repeat the keyword for multiple closing issues. |
| Linear | `Fixes ENG-123` | `Related to ENG-123` | Linear supports closing and non-closing magic words. Put magic words in the PR description, not a PR comment. Multiple issues can follow one magic word when they share the same intent, e.g. `Fixes ENG-123, DES-5 and ENG-256`. |
| Other trackers | Use the project's documented closing keyword only when known. | Prefer a full URL or tracker ID under `Related`. | Some trackers parse JJ change descriptions, PR descriptions, or both. Follow project docs or tracker integration docs when present; otherwise never guess a closing action. |

Closing references can live in the opening paragraph when the body is tiny. Non-closing references always get their own sentence or `## Related` block before validation/evidence. For one item that truly closes, a single line like `Fixes ENG-123.` can be enough; for mixed items, separate closing and non-closing bullets.

---

## Step C: Assemble the body

In order: opening → body sections that earn their keep → related references when they need their own block → test plan if non-obvious → evidence block if one exists → Compound Engineering badge after a `---` rule.

The opening goes under `## Summary` if the body uses any `##` headings; bare paragraph otherwise. No orphaned opening paragraphs above the first heading.

**Evidence handling:** preserve any existing `## Demo` or `## Screenshots` block verbatim unless the user's focus asks to refresh it. If the caller passed a freshly captured URL or path, splice as `## Demo`. Otherwise omit. Place before the badge. Never label test output as "Demo" or "Screenshots."

**Visual aids:** reach for a diagram or table when it conveys the change faster than prose — relationships, flows, state transitions, sequences, trade-offs, before/after data, or any structure prose would have to enumerate. Mermaid and markdown tables cover most shapes; don't be limited to a particular type if a different one fits the change better. Place inline at the point of relevance. Skip for simple, prose-clear, or rename/dep-bump changes. Prose is authoritative when it conflicts with a visual.

**GitHub gotchas:** never prefix list items with `#` (GitHub auto-links `#1` as an issue ref). Use `org/repo#123` or full URL for actual references.

---

## Step D: Badge

```markdown
---

[![Compound Engineering](https://img.shields.io/badge/Built_with-Compound_Engineering-6366f1)](https://github.com/EveryInc/compound-engineering-plugin)
![HARNESS](https://img.shields.io/badge/MODEL_SLUG-COLOR?logo=LOGO&logoColor=white)
```

| Harness | `LOGO` | `COLOR` |
|---|---|---|
| Claude Code | `claude` | `D97757` |
| Codex | (omit `?logo=` param) | `000000` |
| Antigravity CLI (`agy`) | `googlegemini` | `4285F4` |

**Model slug:** spaces become underscores; append context window and thinking level in parens if known. **URL-encode literal parens as `%28` / `%29`** — unencoded parens inside markdown image URLs break release-please's changelog parser, which silently drops the change from the changelog. Examples: `Opus_4.6_%281M,_Extended_Thinking%29`, `Sonnet_4.6_%28200K%29`, `Gemini_3.1_Pro`.

Skip the badge if regenerating a body that already contains it.
