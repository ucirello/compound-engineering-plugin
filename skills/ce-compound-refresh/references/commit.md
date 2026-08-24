# Recording the refresh

Skip if no files changed. Inspect the working-copy change and its parents, bookmarks that identify the current line of work, all paths changed in `@`, available publication remotes, existing provider review state, and recent change-description style. Resolve the remote-designated default with `trunk()` rather than assuming a bookmark name. A missing JJ workspace is a blocker for durable recording; do not fall back to another VCS.

When only refresh-owned paths are in `@`, describe that change and create a new empty working-copy change above it. When unrelated paths also share `@`, leave them untouched and either use a repository-approved JJ operation constrained to the refresh-owned paths or recommend that isolation; do not silently split or rewrite the user's work.

## Description composition and validation

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Repository-local active instructions and syntax observed in `git log` always win over Go guidance. Preserve the semantic requirement to summarize the refresh outcomes while adapting syntax to runtime conventions. Apply compatible Go guidance only to message quality, clarity, and structure; do not impose a fixed message syntax, prefix, type, scope, subject, body, layout, template, or example. Validate the completed description against those same sources before applying it with JJ.

## Non-interactive

When the completed refresh change is based on `trunk()` and publication is appropriate, create a dynamically named feature bookmark for what was refreshed, place it on the completed change, publish that bookmark through the resolved remote, and attempt a PR. When the work is already on a published feature line, record a separate described change there and advance that line's bookmark. Preserve `gh` and GitHub operations for GitHub review state. If JJ, remote, or provider operations fail, report the intended semantic operation and the relevant change ID, bookmark, remote, and failure; do not emit a fixed command sequence.

Every recommendation that includes a change description must include this exact sentence verbatim: Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Repository-local active instructions and syntax observed in `git log` always win over Go guidance. Preserve the site's semantic content requirement while adapting syntax to runtime conventions. Apply compatible Go guidance only to message quality, clarity, and structure; do not impose a fixed message syntax, prefix, type, scope, subject, body, layout, template, or example.

## Interactive

Ask per Blocking questions, with the recommendation derived from the inspected JJ state first. Offer describing the isolated refresh change on the current line, placing it on a separate bookmark when publication needs one, or leaving it undescribed. If unrelated paths share `@`, offer only repository-approved isolation constrained to refresh paths or leaving the working copy untouched. Do not prescribe a fixed bookmark namespace or command sequence.

Every option that composes or edits a change description must include this exact sentence verbatim: Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Repository-local active instructions and syntax observed in `git log` always win over Go guidance. Preserve the option's semantic content requirement while adapting syntax to runtime conventions. Apply compatible Go guidance only to message quality, clarity, and structure; do not impose a fixed message syntax, prefix, type, scope, subject, body, layout, template, or example.
