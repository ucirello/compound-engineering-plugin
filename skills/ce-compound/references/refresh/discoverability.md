# Discoverability check

After the report, apply the **Discoverability Check** section of `references/refresh-and-discoverability.md`. It defines what a reader must learn, the smallest addition and its tone, the consent step, and the `CONCEPTS.md` variant. Follow its interactive Full path in an interactive refresh, with these differences:

- **Instruction files:** look for the project's root agent-instruction surface, whatever this project uses (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, or an equivalent). If there is none, skip the check.
- **Questions:** ask as `references/refresh/modes.md` describes under Blocking questions.
- **Non-interactive:** emit a "Discoverability recommendation" line in the report instead of editing instruction files. The scope of a non-interactive refresh is doc maintenance, not project config.
- **Late edit:** if this check edited an instruction file after Commit already ran, fold only that owned edit into the verified unpublished refresh change using native JJ, or add a small owned-path follow-up change describing the discoverability edit. Read and apply all message-composition standards in `references/refresh/commit.md`, including the full Go guide and recent JJ subjects/bodies; do not impose fixed message syntax. Push the verified bookmark when already authorized so its open PR includes the edit. If the user chose "don't commit", leave edits in the working copy alongside the rest; never absorb unrelated changes.
