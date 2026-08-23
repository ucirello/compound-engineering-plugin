# Investigating a learning

For each learning in scope, read it and cross-reference its claims against current code. Dimensions that stale independently include referenced paths and symbols, the recommendation, snippets, linked docs, overlap with in-scope docs, and domain vocabulary in `.context/CONCEPTS.md`. For a knowledge-track learning, compare only guidance it names or links; never search the guidance layer for one. Injected auto-memory signals are supplementary and never alone justify Replace or Delete. Match verification depth to claim specificity.

After individual docs, evaluate the set: overlaps, supersession (an older narrow doc a newer doc subsumes), and outright contradictions — between docs, or between a learning and a guidance file it names — contradictions actively mislead and outrank individual staleness. Note category-shape problems (a directory whose docs span unrelated themes, a near-empty category) as report-only observations — never restructure directories or create categories.

**Subagents.** Use them for context isolation, choosing the lightest approach that fits: main thread for small scopes, parallel investigation subagents for 3+ independent docs, batches for broad sweeps; docs that overlap or share a root issue are investigated together, not parallelized. When spawning any subagent, omit the `mode` parameter so the user's permission settings apply, and include in its prompt:

## Subagent prompt

Every investigation subagent's prompt carries these three clauses verbatim:

> Use your host's dedicated file search and read tools (Glob, Grep, and Read where they exist) for all investigation, rather than shell commands (ls, find, cat, grep, test, bash) for file operations. This avoids permission prompts and is more reliable. If your host exposes no such tools, use whatever read capability it does provide.
>
> Also scan the "user's auto-memory" block injected into your system prompt (Claude Code only). Check for notes related to the learning's problem domain. Report any memory-sourced drift signals separately from codebase-sourced evidence, tagged with "(auto memory [claude])" in the evidence section. If the block is not present in your context, skip this check.
>
> If the learning is knowledge-track and names or links a guidance file (a skill's `SKILL.md`, a runbook, a root instruction file), read that file and, when it states a different order or a contradictory rule for the same procedure, return both conflicting quotes plus which side current code follows — or that code witnesses neither. Read only guidance the learning names; do not search for one, and do not edit it.

Two subagent roles: **investigation** subagents are read-only and return evidence + a recommended action; **replacement** subagents write successor docs (one per Replace or Split candidate, run one at a time, sequentially). The orchestrator merges results, resolves contradictions, and performs all deletions and metadata edits centrally.
