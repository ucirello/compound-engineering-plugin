# Discoverability check

After the report, apply the **Discoverability Check** section of `references/refresh-and-discoverability.md`. It defines what a reader must learn, the smallest addition and its tone, the consent step, and the `CONCEPTS.md` variant. Follow its interactive Full path in an interactive refresh, with these differences:

- **Instruction files:** look for the project's root agent-instruction surface, whatever this project uses (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, or an equivalent). If there is none, skip the check.
- **Questions:** ask as `references/refresh/modes.md` describes under Blocking questions.
- **Non-interactive:** emit a "Discoverability recommendation" line in the report instead of editing instruction files. The scope of a non-interactive refresh is doc maintenance, not project config.
- **Late edit:** if this check edited an instruction file after Commit already ran, update the same unpushed JJ change or add a small follow-up change describing the discoverability edit. Compose its message using the runtime Go/full-history standards in `references/refresh/commit.md`, not a fixed prefix or subject. Push the verified bookmark if already pushed so the open PR includes it. Preserve unrelated work and owned-path scope. If the user chose "don't commit", leave edits uncommitted alongside the rest.
