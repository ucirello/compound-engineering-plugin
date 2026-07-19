# Evaluation Rubric

The **orchestrator** applies this to decide each item's verdict **before** any fix is dispatched. This is the legitimacy gate: judgment happens here, in the one context that holds every thread at once -- not inside an isolated fixer that has lost the author's design intent. Read the actual code when a verdict turns on it; never decide validity from the comment text alone.

The output of applying this rubric is a verdict per item, sorted into:
- **fix-list** -- `fixed` / `fixed-differently` intent; dispatched to fixers.
- **reply-list** -- `replied` / `not-addressing` / `declined`; reply text composed here (you have the evidence in hand), no code change.
- **human-list** -- `needs-human`; `decision_context` composed here.

## Default to fixing

Most review feedback -- across P0-P2, nitpicks included -- is correct and worth fixing. Work the list and fix: verdict `fixed`, or `fixed-differently` when a better approach than the one suggested is the right call. Judge every item on its merits regardless of source (human reviewer or review bot) or form (inline thread, formal review body, or top-level comment) -- correctness doesn't depend on who raised it or where.

The checks below are tripwires, not a gate to deliberate on per item. When nothing trips, mark it to fix and move on -- don't manufacture doubt or risk to avoid work. "I'm uneasy" is not a tripwire; "I read the callers and this breaks X" is.

## How deep to read

Read enough to decide the verdict, no more:

- **Clear nit or clearly-valid finding** (typo, a bug the diff already shows, naming, a missing guard the comment pinpoints) -> the comment plus the line already in the diff is enough. Mark to fix.
- **Contestable finding, or code that looks deliberate** (the finding asserts a bug where the code reads intentional, touches an invariant, or contradicts a nearby pattern) -> deep-read before accepting: open the referenced file, read the callers, check for the invariant or test that would make the reviewer wrong. **This is where a confidently-wrong reviewer gets caught.** A fresh reviewer -- especially a bot -- usually couldn't see the blast radius or the reason the code is the way it is.
- **Recover the author's intent before overriding deliberate-looking code.** Read relevant `jj log` history, the PR description, and the surrounding code. The intent the author had is the thing an isolated reviewer lacked; weigh it against the finding rather than assuming the reviewer saw more.
- **Dedup reads by file.** Multiple threads on the same file: read it once, judge them together.

## Cross-item reasoning (when judging more than one item)

You hold every thread at once -- use that:

- **Cluster by root assumption.** If one source (often a bot) makes the same kind of claim across several threads and you find it doesn't hold in one place, scrutinize the siblings: a systematically-wrong premise produces a cluster of plausible-but-wrong findings. This is the single biggest advantage of judging centrally instead of per-isolated-agent.
- **Converging requests are a strong fix signal.** The same change asked for by multiple independent reviewers rarely warrants a divert.

## Diverts (apply per item)

Divert from fixing only on a concrete signal:

- **The finding doesn't hold** -- reading the code shows the issue doesn't exist or is already handled -> `not-addressing`, with evidence.
- **The concern is no longer relevant** -- the code at this location changed since the review (see outdated handling below) -> `not-addressing`.
- **The fix would make the code worse** -- it violates a project rule in the active instructions/conventions, adds dead defensive code, suppresses errors that should propagate, introduces premature abstraction, or restates code in comments -> `declined`, citing the specific harm.
- **The change buys nothing real** -- a cosmetic preference or immaterial edit with no benefit to correctness, clarity, or maintainability -> `replied`, briefly saying why no change is warranted. Small *real* improvements still get fixed; the skip bar is "no benefit," not "minor."
- **The change is risky and you can't bound it** -- it touches a hot path, a boundary other code relies on, or thinly-tested code, and the benefit doesn't justify the risk. Risk isn't proportional to size; a one-line edit can carry it. First de-risk: read the callers (you may want a fixer to add a test and run it). If material risk remains after that read, -> `needs-human`.
- **It's a question, not a change request** ("why X?", "is this intentional?") -- answerable from the code -> `replied`; depends on a product/business call you can't determine -> `needs-human`.

## Outdated threads (`isOutdated=true`)

The diff hunk shifted, so the reported line may no longer be where the concern lives. GitHub also exposes `line` as nullable -- outdated and file-level threads often have `line == null`. Start the lookup at whichever location field is available, preferring in order: `line`, `startLine`, `originalLine`, `originalStartLine`. If none resolve to current content matching the reviewer's description, extract an anchor from the comment (a symbol, identifier, or distinctive phrase) and search the **same file** once for it before concluding. Do not search other files. Three outcomes:

- Anchor found in the file -> re-evaluate at that location against the tripwires above. If it's a fix, pass the resolved location/anchor to the fixer.
- Anchor not found and the comment describes concrete in-place code -> `not-addressing` with evidence ("searched <file> for <anchor>, not present").
- Anchor not found and the comment suggests the code was extracted to another file -> `needs-human`. Do not grep the repo; picking the right new location is a judgment call for the user.

## Escalate sparingly (`needs-human`)

Beyond the risk and question cases above: architectural changes that affect other systems, security-sensitive decisions, ambiguous business logic, or conflicting reviewer feedback. Rare -- most feedback just gets fixed.

Do the investigation work before escalating. Don't punt with "this is complex." The user should be able to read your analysis and decide in under 30 seconds.

## Reply text for reply-list and human-list items

Compose these now -- you have the evidence. Quote the specific sentence being addressed, not the whole comment if it is long. Do not apply a fixed opening, verdict prefix, or prose template.

- For `replied`, directly answer the question, explain the design decision, or state the concrete reason an immaterial point does not warrant a change.
- For `not-addressing`, give the evidence showing that the finding does not hold or no longer applies.
- For `declined`, identify the specific harm the requested change would cause or the project convention it would violate.
- For `needs-human`, write a natural acknowledgment in the PR author's voice without automation branding. The posted reply briefly identifies the tradeoff and defers the decision; it does not contain the full internal analysis.

The **decision_context** presented to the user, not posted, contains the quoted ask, what was investigated with file and line references, the precise ambiguity requiring a decision, concrete options and tradeoffs, and a recommendation or the information that would change it. Do not impose fixed headings or option labels.

Whenever the recommendation includes how a change should be described, apply the complete rule at this site: Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. The project's full active instructions and runtime change-description conventions observed in `jj log` take precedence. Use compatible Go guidance only for quality, clarity, and structure. Do not impose a fixed prefix, type, scope, subject, body, layout, template, or example.
