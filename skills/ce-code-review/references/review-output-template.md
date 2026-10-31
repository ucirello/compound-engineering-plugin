# Code Review Output Template

### Quoted Go source guidance (not a mandatory repository template)

The following verbatim excerpts are from https://go.dev/wiki/CommitMessage. Repository-local syntax ALWAYS wins; the Go illustration does not prescribe message syntax here. Keep the runtime full-guide/history comparison below.

> Commit messages, also known as CL (changelist) descriptions, should be formatted per https://go.dev/doc/contribute#commit_messages. For example,
>
> ```text
> net/http: handle foo when bar
>
> [longer description here in the body]
>
> Fixes #12345
> ```
>
> Notably, for the subject (the first line of description):
>
> - the name of the package affected by the change goes before the colon
> - the part after the colon uses the verb tense + phrase that completes the blank in, “this change modifies Go to **___**”
> - the verb after the colon is lowercase
> - there is no trailing period
> - it should be kept as short as possible (many git viewing tools prefer under ~72 characters, though Go isn’t super strict about this).
>
> For the body (the rest of the description):
>
> - the text should be wrapped to ~72 characters (to appease git viewing tools, mainly), unless you really need longer lines (e.g. for ASCII art, tables, or long links).
> - the Fixes line goes after the body with a blank newline separating the two. (It is acceptable but not required to use a trailing period, such as Fixes #12345.).
> - there is no Markdown in the commit message.
> - we **do not** use `Signed-off-by` lines. Don’t add them. Our Gerrit server & GitHub bots enforce CLA compliance instead.
> - similarly, we do not use Co-authored-by and Assisted-by lines. Don’t add them.
> - when referencing CLs, prefer saying “CL nnn” or using a go.dev/cl/nnn shortlink over a direct Gerrit URL or git hash, since that’s more future-proof.
> - when moving code between repos, include the CL, repository name, and git hash that it was moved from/to, so it is easier to trace history/blame.

This is the **canonical skeleton** for *which sections appear and in what order* — copy the section structure; the example below shows one good rendering, not the only permitted layout. Shape each finding for the reader's next action per *Presentation direction* in `references/finish-review.md` (Stage 6) (what & where / why it matters / what response it needs / how sure; let the shape serve the finding type). Findings are grouped by severity, not by reviewer.

**Hard constraints (non-negotiable; the rest is judgment):** ASCII-safe only — no box-drawing or per-item horizontal-rule separators (`────`), no Unicode arrows or middot; use `->`. Don't paste file contents or re-print the diff — cite `file:line`. Stable `#` numbering, reused wherever a finding reappears. The Verdict and Actionable list are present, last, and self-sufficient.

**If you use a markdown table, escape literal pipe characters in cells.** Any `|` inside a finding title, issue description, code snippet, regex pattern, or delimited-string example (e.g. cache key examples like `userName + "\|" + groups`) must be written as `\|` so column boundaries are determined only by unescaped pipes. Unescaped pipes split the cell across columns and corrupt the row's `Reviewer` and `Confidence` values (and `Route` in the Actionable Findings table).

## Example

```markdown
## Code Review Results

**Scope:** merge-base with the review base branch -> working tree (14 files, 342 lines)
**Intent:** Add order export endpoint with CSV and JSON format support
**Mode:** markdown + explicit local apply

**Reviewers:** correctness, testing, maintainability, security, api-contract
- security -- new public endpoint accepts user-provided format parameter
- api-contract -- new /api/orders/export route with response schema

### Applied (explicit local apply; safe, verified)

| # | File | Fix | Reviewer |
|---|------|-----|----------|
| 6 | `export_helper_test.rb:40` | Added missing test for the empty-format branch | testing |
| 7 | `orders_controller.rb:88` (+test) | Tightened export file perms `0644 -> 0600` (security-posture — verify in diff) | security |

Validation: export tests 11 -> 13; suite 214 pass, lint clean.
Recorded in isolated JJ change: `<actual description composed from repository history and the full Go commit-message guide>` (working copy was clean before review; Stage 5c message standards apply).

### Triage Groups

| Group | Findings | Context | Preferred Resolution | Why |
|-------|----------|---------|----------------------|-----|
| Export result-set scaling | #2, #3 | Both stem from loading the full order set in one pass | Design the pagination contract first (#3), then stream with `find_each` behind it (#2) | One cursor/page decision resolves the memory bound and the API shape together |

### P0 -- Critical

| # | File | Issue | Reviewer | Confidence |
|---|------|-------|----------|------------|
| 1 | `orders_controller.rb:42` | User-supplied ID in lookup, no ownership check | security | 100 |

- **#1** — `find(params[:id])` on the export path has no `where(account: current_account)` scope, so any authenticated user can export another account's orders. Scope the lookup to the current account.

### P1 -- High

| # | File | Issue | Reviewer | Confidence |
|---|------|-------|----------|------------|
| 2 | `export_service.rb:87` | Loads all orders into memory -- unbounded | performance | 100 |
| 3 | `export_service.rb:91` | No pagination contract | api-contract, performance | 75 |

- **#2** — `Order.where(...).to_a` materializes the full result set; a large account OOMs the worker. Stream with `find_each` or paginate.
- **#3** — the endpoint returns every row in one response; needs a cursor/page contract before GA. Design decision — see Actionable Findings.

### P2 -- Moderate

| # | File | Issue | Reviewer | Confidence |
|---|------|-------|----------|------------|
| 4 | `export_service.rb:45` | No error handling for CSV serialization failure | correctness | 75 |

### P3 -- Low

| # | File | Issue | Reviewer | Confidence |
|---|------|-------|----------|------------|
| 5 | `export_helper.rb:12` | Format detection could use an early return | maintainability | 75 |

### Actionable Findings

| # | File | Issue | Route | Notes |
|---|------|-------|-------|-------|
| 1 | `orders_controller.rb:42` | Ownership check missing on export lookup | `gated_auto -> downstream-resolver` | `suggested_fix` present — caller decides whether to apply |
| 3 | `export_service.rb:91` | Pagination contract needs a broader API decision | `manual -> downstream-resolver` | Needs design input before implementation |

### Pre-existing Issues

| # | File | Issue | Reviewer |
|---|------|-------|----------|
| 1 | `orders_controller.rb:12` | Broad rescue masking failed permission check | correctness |

Detail lines for Pre-existing and history-dependent P0/P1 findings may include the same short provenance string the artifact `evidence` carries (e.g. `provenance: a1b2c3d Alice 2024-08-12 - harden rescue`) when the finding depends on that history. Do not dump full-file blame into the report.

### Learnings & Past Solutions

- [Known Pattern] `<root>/solutions/export-pagination.md` -- previous export pagination fix applies to this endpoint

### Agent-Native Gaps

- New export endpoint has no CLI/agent equivalent -- agent users cannot trigger exports

### Deployment Notes

- Pre-deploy: capture baseline row counts before enabling the export backfill
- Verify: `SELECT COUNT(*) FROM exports WHERE status IS NULL;` should stay at `0`
- Rollback: keep the old export path available until the backfill has been validated

### Coverage

- Suppressed: 2 findings below anchor 75 (1 at anchor 50, 1 at anchor 25)
- Removable surface: ~40 lines / 1 file across findings #5 (signal only, not a target)
- Residual risks: No rate limiting on export endpoint
- Testing gaps: No test for concurrent export requests

---

> **Verdict:** Ready with fixes
>
> **Reasoning:** 1 critical auth bypass must be fixed. The memory/pagination issues (P1) should be addressed for production safety.
>
> **Fix order:** P0 auth bypass -> P1 memory/pagination -> P2 error handling if straightforward
```

## Anti-patterns

Do NOT produce output like this. The following is wrong:

```markdown
Findings

Sev: P1
File: foo.go:42
Issue: Some problem description
Reviewer(s): adversarial
Confidence: 75
Route: advisory -> human
────────────────────────────────────────
Sev: P2
File: bar.go:99
Issue: Another problem
```

This fails because of the **box-drawing `────` separators between items**, no stable finding numbers, no severity-grouped `###` headers, no `## Code Review Results` title, and a verdict not set apart. The `────` rules and missing structure are the problem — `Field:`-prefixed lines are not themselves banned, but here they carry no stable numbers and bury depth. Prefer a terse table or a keyed list; put depth in a per-finding detail line (`- **#N** — …`), not in box-drawn blocks.

## Formatting Rules

- **ASCII-safe only** -- never box-drawing characters or per-item horizontal-rule separators (`────`) between entries (the report-level `---` before the verdict is still required), no Unicode arrows or middot; use `->`. Tables are a good default but not mandatory -- let the shape serve the finding type (`references/finish-review.md`, Stage 6); stay consistent within a section
- **Escape literal `|` in table cells** -- any `|` inside a finding title, issue description, code snippet, regex pattern, or delimited-string example must be written as `\|`. Unescaped pipes are parsed as column separators and corrupt the row's `Reviewer` and `Confidence` columns (and `Route` in the Actionable Findings table). Applies especially to cache-key delimiter examples, regex alternations, and logical-OR operators quoted inside findings.
- **Severity-grouped sections** -- `### P0 -- Critical`, `### P1 -- High`, `### P2 -- Moderate`, `### P3 -- Low`. Omit empty severity levels.
- **Stable sequential finding numbers** -- assign finding numbers once after sorting, continue them across severity sections, and reuse those same numbers when findings are repeated in Actionable Findings. Do not restart at `1` for each severity or route bucket.
- **Always include file:line location** for code review issues
- **Reviewer column** shows which persona(s) flagged the issue. Multiple reviewers = cross-reviewer agreement.
- **Confidence column** shows the finding's anchor as an integer (`50`, `75`, or `100`). Never render as a float.
- **No `Route` column in the per-severity tables** -- the synthesized route (``<autofix_class> -> <owner>``) appears only in the Actionable Findings table and the `mode:agent` JSON. The scannable severity tables are 5 columns: `# | File | Issue | Reviewer | Confidence`.
- **Detail line (per finding, as needed)** -- keep the scannable line short (the symptom + `file:line`, not the mechanism); put the why-it-matters + fix/options in a per-finding detail line keyed by stable `#`: `- **#N** — <why it matters + what response it needs>`. Add it whenever the one-liner isn't self-sufficient -- usually P0/P1; P2/P3 are often terse-only. This keyed detail is the home for depth -- don't paste code or restate the diff, and match weight to weight.
- **Header includes** scope, intent, and reviewer team with per-conditional justifications
- **Mode line** -- include `markdown report-only`, `markdown local-apply`, or `agent report-only`
- **Triage Groups section (when groups exist)** -- pipe table `| Group | Findings | Context | Preferred Resolution | Why |` rendered after Applied and before the severity tables. The `Findings` cell lists stable `#`s (e.g. `#2, #3`); every referenced `#` must appear in a severity table below. Groups are a triage lens over the findings -- they never replace the severity tables, merge findings, or renumber them. Omit when `grouping:off` is active or no groups survived Stage 5b/5c pruning.
- **Applied section (explicit local apply only)** — list applied fixes first as `# | File | Fix | Reviewer`, one row per stable # even for multi-file fixes, then validation and actual JJ change/description status (or dirty work left undescribed). No fixed message syntax. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards. Before composing read the full guide and compare several full subjects AND bodies with `(cd "$workspace_root" && jj log --no-graph -r '::<task-verified-history-head>' -n 10 -T 'description ++ "\n"')`; repository-local syntax wins for prefixes/packages, casing, tense, separation/wrapping and refs. No history means explicit rules plus compatible Go guidance, never invented precedent; no Markdown or Co-authored-by/Assisted-by trailers. Stage 5c owns authorized isolation and verification. Flag green-but-unverifiable auth/contract/concurrency edits. Applied findings appear only here, not severity tables. Omit when unauthorized or nothing applied.
- **Actionable Findings section** -- include when the actionable queue is non-empty (findings for the caller to handle)
- **Pre-existing section** -- separate table, no confidence column (these are informational)
- **Learnings & Past Solutions section** -- results from the `learnings-researcher` local prompt asset, with links to <root>/solutions/ files
- **Agent-Native Gaps section** -- results from the `agent-native-reviewer` local prompt asset. Omit if no gaps found.
- **Deployment Notes section** -- key checklist items from the `deployment-verification-agent` local prompt asset. Omit if the prompt did not run. Schema drift surfaces as `data-migration` findings — no separate section.
- **Coverage section** -- suppressed count, validation outcome counts when Stage 5b ran (confirmed, rejected, unresolved, malformed, failed, shortcut-skipped) with the reason for each non-confirmed outcome, removable surface (only when deletion-oriented maintainability findings exist; approximate net lines/files removable if applied -- a dead-weight signal, never a reduction target, omit otherwise), residual risks, testing gaps, failed reviewers
- **Summary uses blockquotes** for verdict, reasoning, and fix order
- **Horizontal rule** (`---`) separates findings from verdict
- **`###` headers** for each section -- never plain text headers

## Agent mode (JSON)

When `mode:agent` is active, **do not** emit the markdown table report above. Emit **one parseable JSON object** as the primary response and write the same payload to `review.json` under the resolved `<run-dir>`.

The contract is defined in `references/modes-and-output.md` under **`## JSON output format (`mode:agent` only)`**. Minimum fields: `status`, `verdict`, `scope`, `intent`, `reviewers`, `findings`, `actionable_findings`, `artifact_path`, `run_id`.

Key differences from the human-facing markdown format:

- **No pipe-delimited tables** — findings are JSON arrays with merged fields (`#`, `title`, `severity`, `file`, `line`, `confidence`, `autofix_class`, `owner`, `suggested_fix`, `why_it_matters`, `evidence`, `reviewers`, etc.).
- **`actionable_findings`** — subset for caller apply workflows (`gated_auto` / `manual` with `downstream-resolver`).
- **`triage_groups`** — the markdown Triage Groups section serialized as `{title, findings: [<stable #s>], context, preferred_resolution, why}` objects, so callers can batch related fixes by theme. Groups span the full finding set — a triage lens, not an apply queue — so a caller must intersect each group's `findings` with `actionable_findings` before applying; the apply handoff stays `actionable_findings`. Empty when `grouping:off` or no groups.
- **No `applied_fixes` and no Applied section** — `mode:agent` does not apply fixes; the caller does. Applied work surfaces only in explicitly authorized local-apply markdown (Stage 5c/6). The handoff is `actionable_findings`.
- **Failure/degraded paths** — `{"status":"failed","reason":"..."}` or `"status":"degraded"` with reason; never mix markdown tables into the JSON response.
- **Stable `#`** — same numbering as Stage 5 synthesis, carried in JSON finding objects for downstream apply/residual tracking.
