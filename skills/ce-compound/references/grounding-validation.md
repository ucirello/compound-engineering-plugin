# Grounding Validation (Phase 2.45)

Read this when Phase 2.45 runs. The doc just written becomes permanent, trusted knowledge — future agents will act on its claims without re-verifying them. This phase checks the claims against reality before they compound: a deterministic mechanical pass (bundled script) plus a semantic pass (one read-only validator subagent). Neither pass is a hard gate — every flag is adjudicated, because solution docs legitimately cite deleted paths and pre-fix states.

## Which tree is the ground truth

Two claim categories verify against different trees:

- **Code-behavior claims** (enum values, status semantics, limits, defaults) verify against the **local working copy** — they describe what this session's work produced and verified here.
- **Merge-state claims** ("fixed in #1608", "landed", "shipped") verify against **remote truth** — the local working copy may predate a merge, so `gh pr view` (or the tracker equivalent) is primary and JJ revset reachability is only the fallback. The script's `INFO: workspace is N changes behind …` line tells you how much to distrust the local revision graph for this category.

Before running the script, optionally run `jj git fetch --all-remotes` (best-effort — skip silently on failure or offline; the network is never a correctness dependency). When remote state cannot be checked at all, keep the claim, add an as-of qualifier ("as of this writing"), and record degraded verification in the run report.

## Step 1: Adjudicate the mechanical flags

The script reports flags; you decide each one. Three resolutions — **fix**, **annotate**, or **confirm intentional** — never an automatic rewrite and never an automatic pass:

| Flag | Likely meaning | Resolution |
|------|----------------|------------|
| path not found anywhere | Typo, or drafted from memory | Fix the citation or remove the claim |
| path missing here, exists at upstream | Stale working copy | Verify the claim against upstream; annotate if the doc implies the file is present locally |
| path deliberately gone (doc says removed/renamed) | Historical citation | Confirm the surrounding prose marks it as historical ("removed by this fix", "pre-fix state"); add that marker if absent |
| Commit ID does not resolve | Fabricated or from another repository | Replace with the PR number, or drop |
| Commit ID reachable from `@` only | Local-only change; commit ID can change after revision rewrite or squash merge | Replace with the PR number |
| Commit ID reachable from upstream only | Working copy predates the merge | Keep, with a temporal qualifier; verify the landed claim via `gh` |
| Commit ID exists but is unreachable | Rewritten-away revision | Replace with the PR number |
| scaffold ("Learning 3", `{{…}}`) | Drafting-context leak | Always fix — rewrite as a real path or link |
| relative link unresolved | Wrong target | Fix the path |

If the script cannot be resolved on this platform, apply its checks manually at the same scope — scan the body for cited paths that don't exist, hexadecimal commit IDs, `Learning(s) N` / `{{…}}` scaffold, and broken relative links — and note in the run output that the check was manual. Do not silently skip.

After any body edit from this step or Step 2, re-run the script until it reports clean or every remaining flag is confirmed intentional.

## Step 2: Semantic validator subagent (Full and headless; skipped in lightweight)

Dispatch **one generic read-only subagent** covering the written solution doc plus any `CONCEPTS.md` entries added or edited this run (Phase 2.4's entries are claims too — a glossary entry written from a session-level summary is exactly how wrong semantics enter the vocabulary). Use the same mid-tier model class as other reviewer subagents when the platform exposes one. Build its prompt from this template:

```
You are a grounding validator for documentation about to enter a permanent
knowledge store. You are read-only: never edit files. Inspect with Read,
Grep, Glob, `jj` read-only commands, and `gh` when available.

Inputs: the doc content below, the CONCEPTS.md entries below (if any), and
this staleness context: <INFO line from the mechanical script, or "none">.

Check every factual claim in three categories:

1. CODE-BEHAVIOR CLAIMS — assertions about how code behaves: enum values,
   status semantics, limits, defaults, ordering, state transitions. For
   each, locate the defining source in the current working copy and quote the
   defining line(s) with file:line. Verdict: verified (with quote),
   contradicted (with the quote showing otherwise), or unverifiable
   (defining source not found).

2. MERGE-STATE CLAIMS — assertions that a change landed ("fixed in",
   "merged", "shipped in", "resolved by #N"). Primary check: gh pr view
   <n> --json state,mergedAt,baseRefName (remote truth). Fallback: JJ revset
   reachability from the upstream default bookmark. Resolve commit IDs with
   `jj log -r <id>` and test ancestry with `<id> & ::<bookmark>`. Verdict: verified,
   contradicted (e.g. PR open, not merged), or unverifiable (offline / no
   gh) — mark unverifiable as "degraded", do not guess.

3. INTERNAL COMPLETENESS — countable assertions ("six PRs", "three root
   causes", "all N consumers"). Count the substantiating items in the doc
   itself. Verdict: complete, or short (found M of N).

Ignore session narrative ("we first tried X") — that describes the
conversation, not the working copy or revision graph. Ignore style.

Return a structured list, one entry per claim checked:
  claim (verbatim) | category | verdict | evidence (quote + file:line, or
  command output) | suggested edit (only for non-verified claims)
```

**Orchestrator handling of verdicts:**

- **contradicted** → fix the doc using the quoted evidence (the quote, not the conversation, is authoritative)
- **unverifiable** (behavior) → soften or attribute: "per this session's conclusion…" — or drop the claim
- **unverifiable/degraded** (merge-state) → keep with an as-of qualifier; record degraded verification in the report
- **short** (completeness) → complete the enumeration or restate the count to match what the doc substantiates
- **verified** → no change

## Reporting

Summarize the phase in one line of the run output (headless report's `Grounding:` line; interactive success output): flags adjudicated (fixed / annotated / confirmed), claims checked, claims softened or corrected, and `degraded — merge-state claims unverified offline` when applicable.

JJ command semantics used here are defined by the official [`jj root`](https://docs.jj-vcs.dev/latest/cli-reference/#jj-root), [`jj log`](https://docs.jj-vcs.dev/latest/cli-reference/#jj-log), [`jj file show`](https://docs.jj-vcs.dev/latest/cli-reference/#jj-file-show), and [revset](https://docs.jj-vcs.dev/latest/revsets/) documentation. Prefer the installed version's `jj help <command>` when it differs from the generated CLI reference.
