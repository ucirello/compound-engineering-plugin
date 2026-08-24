---
name: ce-commit
description: Describe Jujutsu changes with clear, value-communicating messages. Use when the user asks to commit or save working-copy changes with repository-appropriate descriptions.
---

# Jujutsu Change Description

Turn the requested working-copy content into well-bounded local Jujutsu changes with accurate descriptions. Do not push or open a PR; route that work to `ce-commit-push-pr`.

**Done when:** every requested logical change occupies an explicit change boundary, has a description that states its outcome, and contains exactly its intended files; excluded or unrelated content remains outside those changes. **Stop when:** there is no requested content to describe, the directory is not a Jujutsu workspace, or ambiguity or conflicts prevent a truthful boundary or description.

## Context

Gather current state with separate shell tool calls. Do not join commands with shell operators, substitutions, pipes, or redirects. Interpret non-zero exits as state, and use the installed `jj help <command>` when repository configuration or the installed version affects a command form.

| Command form | Purpose | Non-zero or empty result |
| --- | --- | --- |
| `jj root` | Confirm the workspace and obtain its root | Not a Jujutsu workspace; stop |
| `jj status` | Inspect the working-copy change, conflicts, and changed paths | State unavailable; stop |
| `jj diff -r <working-copy-change>` | Inspect the complete content to be bounded and described | No content in that change |
| `jj log -r <working-copy-change> --no-graph` | Read the current change ID and description | Change unavailable; stop |
| `git log <repository-appropriate-history-options>` | Observe the repository's established message syntax | No useful history; rely on active repository-local instructions and compatible Go guidance |

Jujutsu snapshots the working copy at the start of ordinary commands, so this context can change while it is gathered. Re-read `jj status` and the relevant `jj diff` immediately before each boundary or description mutation.

## Workflow

1. **Establish scope** - Compare the complete working-copy change with the user's request. Honor `exclude:<paths>` whenever the invocation carries it: excluded paths must remain outside every requested change and must be named in the report. Stop and ask when ownership of content is ambiguous or unresolved conflicts prevent an accurate boundary or description.

2. **Choose change boundaries** - Group the requested content by independently understandable outcome. Use one change when separation is ambiguous and at most three unless the user requests otherwise. Select whole files only; do not split hunks interactively. When the working-copy change contains multiple groups, exclusions, or unrelated content, use explicit JJ filesets to split each requested group into its own change while leaving all unselected content in the remaining working-copy change. When the existing boundary already contains exactly one requested group, preserve its content and topology.

3. **Compose each description** - Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. The user's request, repository-local active instructions, and the syntax observed in `git log` determine the current standard; repository-local instructions and `git log` syntax always win over Go guidance. The description must communicate the change's outcome rather than enumerate its files. Include motivation, trade-offs, issue context, or a known plan implementation-unit identifier only when the current standards and available context make them relevant. Do not search for a plan solely to add an identifier. Do not add generated-by text, authorship, co-authorship, sign-off, or other attribution.

4. **Apply boundaries and descriptions** - Use the installed forms of these commands with neutral values:

```text
jj split -r <source-change> -m "<composed-description>" <included-filesets...>
jj describe -r <target-change> -m "<composed-description>"
```

Use `jj split` only when a content boundary must change; its selected filesets form the described change and its unselected content remains in the child change. Use `jj describe` when the target already has the exact intended content. After every mutation, identify changes by change ID rather than assuming a position such as parent or child, then verify the target's full diff and the remaining working-copy diff before continuing.

Pass a complete multiline description as one message value. If the harness cannot pass that value safely, use an ignored file under `<workspace-root>/.tmp/ce-commit/` as the fallback and remove it after use. Confirm `.tmp` is ignored before creating the file; otherwise stop rather than snapshot scratch content. Do not use an operating-system temporary directory.

5. **Verify and report** - Run `jj status`, inspect each resulting change with `jj diff -r <created-change>` and `jj log -r <created-change> --no-graph`, and confirm that descriptions and exact filesets match the intended groups. Report each change ID, commit ID, description, and fileset, plus every excluded, unrelated, or newly arrived path left in the working-copy change. If concurrent edits changed a boundary, stop and report that the affected description must be reconsidered.
