# Remove the retired Compound Codex tool map

The Bun-era `convert` / `install --to codex` path inserted a managed block into the global Codex instructions file:

`<!-- BEGIN COMPOUND CODEX TOOL MAP -->` … `<!-- END COMPOUND CODEX TOOL MAP -->`

in `${CODEX_HOME:-$HOME/.codex}/AGENTS.md`. That Claude compatibility map is obsolete, and one of its lines told Codex to collapse subagent dispatch onto the main thread. OpenCode does not use the map. This is optional cleanup of an older install, not part of native OpenCode delegation; see `references/native-models.md` for the separate OpenCode V2 prerequisite.

## Removal

Delete the managed block from that file: the line `<!-- BEGIN COMPOUND CODEX TOOL MAP -->` through the next line `<!-- END COMPOUND CODEX TOOL MAP -->`. If that pair is not present as two whole lines in that order, the block is not there — change nothing.

Leave the rest of the file untouched, and delete the file if nothing is left. Do not add a replacement map, and do not touch a project or repo `AGENTS.md`: the Bun installer only ever wrote the Codex home file.

Show the user a short before/after of what changed, or say the block was already absent.
