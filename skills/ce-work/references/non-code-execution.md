# Knowledge-Work Execution

Load for `execution: knowledge-work`. Read the production plan fully, read its named sources, synthesize the requested deliverable, save it to the user-selected or sensible durable `docs/` path, and report the absolute path.

Skip code-unit dispatch, test discovery, external implementation, incremental Jujutsu changes, review delivery, PR, and CI. If a required sub-step produces executable code or configuration, route that sub-step through the normal code path.

Whether to include the final document in a described Jujutsu change is the user's choice. If requested, apply this exact rule at the description site:

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

The project's active runtime instructions and conventions are required input. Inspect descriptions with `jj log`; syntax observed there wins over generic guidance. Apply the linked Go guidance only when compatible with those instructions and that history. Use no fixed type, scope, template, example, or identity footer.
