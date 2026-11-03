# Discoverability check

After the report, apply the **Discoverability Check** section of `references/refresh-and-discoverability.md`. It defines what a reader must learn, the smallest addition and its tone, the consent step, and the `CONCEPTS.md` variant. Follow its interactive Full path in an interactive refresh, with these differences:

- **Instruction files:** look for the project's root agent-instruction surface, whatever this project uses (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, or an equivalent). If there is none, skip the check.
- **Questions:** ask as `references/refresh/modes.md` describes under Blocking questions.
- **Non-interactive:** emit a "Discoverability recommendation" line in the report instead of editing instruction files. The scope of a non-interactive refresh is doc maintenance, not project config.
- **Late edit:** if this check edited an instruction file after the refresh revision was described, update that revision only when unpublished or create a scoped follow-up revision and publish it when already authorized. Compose the message using `refresh/commit.md`, not a fixed prefix/template. If the user chose "don't commit", leave the edits uncommitted alongside the rest.
