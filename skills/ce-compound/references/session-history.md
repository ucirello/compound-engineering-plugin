# Session history (Full mode)

Use supported OpenCode session listing/export only; never inspect internal databases or other harness storage. Resolve the absolute workspace root by locating the enclosing `.jj` directory; run every JJ subprocess with that root as cwd. Optional bookmark context comes from `jj log --no-graph -r @ -T 'bookmarks'`; absent bookmarks mean no bookmark filter.

## Context-pressure source handoff

Follow `SKILL.md`'s ONE fresh native delegate protocol. Parent reads `$OPENCODE_SESSION_ID` with shell, never guesses, and passes source ID, known title, absolute workspace root, existing learning doc path, and one-sentence topic, never predigested conversation. Delegate loads `ce-compound mode:non-interactive depth:full`.

The supplied source is primary evidence. Export it using `opencode session export ID` or `opencode api get /api/session/ID/message` into a private per-run directory under that workspace's `.tmp/`. Before reading, reduce exported messages to user/assistant text and tool names/short results, stripping reasoning and secrets. Do not read internal DB files. Never exclude the supplied source as “current”; exclude only the delegate's own session. Source export failure is an evidence blocker, not proof of no relevant history.

## Prior-session probe

Run alongside Related Docs Finder. Use supported session listing, starting with seven days and matching workspace and the one-sentence topic. Export only relevant candidates (at most five), reduce before reading as above, and escalate synthesis only for bookmark matches or at least two topic-keyword matches. No relevant candidates is a valid result. Unsupported listing/export is visibly degraded coverage, never permission to scan internal storage or another harness. Retained legacy extraction helpers are compatibility parsers, not active discovery routes.

Read `agents/session-historian.md`, then dispatch a native generic subagent with that prompt, topic, reduced scratch paths and metadata. It reads only supplied paths, writes findings to `<run-dir>/session-history.md`, and returns the confirmed artifact path; inline prose is fallback only if writing fails. Include source-session evidence separately even when no prior sessions qualify. Wait for this final Phase 1 input before assembly; do not pause for questions.
