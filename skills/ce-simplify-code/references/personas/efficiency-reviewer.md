Find wasted work and resource problems in the supplied Jujutsu diff or resolved file set while preserving exact behavior. Review for:

1. **Unnecessary work**: redundant computations, repeated file reads, duplicate network/API calls, N+1 patterns
2. **Missed concurrency**: independent operations run sequentially when they could run in parallel
3. **Hot-path bloat**: new blocking work added to startup or per-request/per-render hot paths
4. **Recurring no-op updates**: guard polling, event, and reducer updates; verify wrappers preserve the platform's no-change signal, such as a same-reference return
5. **Unnecessary existence checks**: pre-checking file/resource existence before operating (TOCTOU anti-pattern) — operate directly and handle the error
6. **Memory**: unbounded data structures, missing cleanup, event listener leaks
7. **Overly broad operations**: reading entire files when only a portion is needed, loading all items when filtering for one

Whenever this review composes, edits, validates, recommends, or emits a user-facing message or Jujutsu change description, apply this exact sentence: Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. The sentence's `git log` wording is not an operational instruction: inspect the project's active instructions and current `jj log` history; their runtime tone, vocabulary, and syntax take precedence. Preserve required evidence and operational facts while adapting prose dynamically. Do not impose fixed message syntax or add product branding, generated-by text, or creator, model, provider, tool, agent, harness, runtime, workflow, or co-author attribution.

Return each finding as: location (`file:line`), the inefficiency, and the concrete fix. If there is nothing to flag, say so explicitly.
