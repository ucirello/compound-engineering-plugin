# Updating an existing STRATEGY.md

Required read before editing any `STRATEGY.md` that already exists. Covers whose shape the file is in and how the update run proceeds.

## Meaning is the contract; existing shape decides the format

When this skill creates `STRATEGY.md`, it writes the house format in `references/strategy-template.md`. When a doc already exists that is not solely in that shape, adapt to it: read it by meaning (a section counts as present when the doc expresses it anywhere, under any heading or in prose), make only additive or minimal changes in its own idiom, and never restructure it, add frontmatter or headings uninvited, or duplicate a meaning under a new heading. Preserve content this skill did not write; if this run learns something that makes it false, make the smallest edit that keeps its intent true and say so in chat. A section whose inline metadata records approval or forbids edits, or a doc the user does not own, is not edited at all - report the conflict, or write to a separate file with a link. The worst outcome is turning an existing document into this template and breaking what already reads it.

## Classify the shape before editing

The conduct above protects existing content. Applying it to a file containing only this skill's format freezes an old format for no reason, so decide from the file itself; Jujutsu history is evidence but cannot establish ownership of a section:

- **House-format only** when the file positively has this skill's shape - at least one `##` heading from the template, current (`Purpose`, `Positioning`, `Users`, `Boundaries`, `Key metrics`, `Tracks`, `Milestones`, `Brand`) or legacy (`Target problem`, `Our approach`, `Who it's for`, `Not working on`, `Marketing`) - and every `##` heading is one of those, with no out-of-template ownership or lock metadata. Frontmatter with `name` and `last_updated` and a `# <name> Strategy` title corroborate; a hand-written file that copied this shape is treated the same way, while a prose-only file with no template heading takes the adapt-in-place path. Such a file is maintained in house format on any write: legacy headings renamed, sections put in the template's current order, a missing required section offered, and `last_updated` set.
- **Multi-writer** when any other heading or out-of-template ownership or lock metadata is present. This skill's own headings are still its to rename, but nothing is reordered and nothing foreign is restyled or edited. Ordering into the template belongs only to house-format-only files.

## The update run

Read the existing `<workspace-root>/STRATEGY.md` thoroughly. Summarize current state in 3-5 lines so the user sees what is on file. Legacy headings are migrated as the section above says - headings only, content untouched, mentioned in chat. A section carrying approval or do-not-edit metadata keeps its heading and content. A file in any other shape is read by meaning and updated in its own shape; when this skill adds a section whose meaning the file does not yet carry, it uses the template heading. When a section already carries that meaning under another heading, merge into it without renaming it or adding a duplicate.

Check for drift: compare every section of the doc against the workspace model - stated intent, structure, recent Jujutsu changes, provider review records such as GitHub PRs, and plans and learnings under `<root>` - not only against what changed since the last write, since a targeted update advances `last_updated` without reviewing the rest. Gather repository evidence with the JJ and provider semantics in `references/grounding.md`. Name any section the evidence suggests is stale, with the evidence, as a candidate - not a verdict.

If the focus hint named a specific section, jump to that section in `references/interview.md`. Preserve every other section's content exactly, including sections this skill did not write, and its place per the shape test above (a house-format-only file takes the template's order; a multi-writer file is never reordered); the heading migration is a rename only and does not conflict with that. Apply pushback as if this were a first run - do not rubber-stamp existing weak content just because it is already written.

If no specific target, ask the user which section to revisit using the blocking question tool, listing any drift candidates first. Options:

- "Purpose"
- "Positioning"
- "Users"
- "Metrics, tracks, boundaries, or other"

For each revisited section, re-interview with full pushback. For sections the user confirms are still accurate, leave their content untouched. If the file is house-format only and no section carries a meaning the template now requires (Boundaries - a migrated `Not working on` already carries it), offer to add it among this skill's own sections - do not add it silently, and do not add it to a file whose own portion is not in house format (a hand-written prose doc). When the file has YAML frontmatter, set `last_updated` to today's ISO date; when it has none, leave it that way - readers fall back to the file's own date.

Write the updated doc back to `<workspace-root>/STRATEGY.md`.
