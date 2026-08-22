# Discoverability

After the report, check semantically whether the project's active instructions lead an agent to `.context/solutions/`, explain its searchable structure, and say when it is relevant. If no substantive project instruction file exists, skip.

When the spirit is missing, draft the smallest style-matching addition, preferably one line in an existing related section:

```text
.context/solutions/  # documented solutions to past problems, organized by category with YAML frontmatter (module, tags, problem_type)
```

Interactive mode shows the target and rationale and asks before editing. Non-interactive mode reports the recommendation without editing instructions.

If `.context/CONCEPTS.md` exists, apply the same semantic check for shared domain vocabulary; otherwise skip it.

If an instruction edit happens after the refresh change was described, include it in the same local revision when safe. Otherwise create a new Jujutsu child, describe it, update the existing bookmark, and push only when publication was selected.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. The project's active instructions and the description syntax observed at runtime in `jj log` win. Apply compatible Go guidance only to quality, clarity, and structure; it does not prescribe imperative mood, casing, punctuation, line wrapping, subject/body shape, or any fixed syntax.
