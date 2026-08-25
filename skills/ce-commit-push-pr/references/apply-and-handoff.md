# Apply, report, and hand off

## Route

- **Description-only:** print the title and body and stop unless application was requested.
- **New PR:** in Stack mode use `references/stack-submit.md`. Otherwise repeat the exact existing-PR query immediately before create. A matching owner and bookmark routes to existing-PR handling, exit-0 `[]` permits creation, and non-zero blocks.
- **Existing PR in full workflow:** report the URL after push, then ask whether to rewrite unless pipeline mode or explicit intent already decides. Stack mode still submits or synchronizes the managed stack.
- **Description update or confirmed rewrite:** compare title and body with the current PR, preview the proposed title, lead, and body length, and ask before `gh pr edit` unless apply intent is already explicit. Skip identical content.

## Explainer archival

Archive only in full workflow when teaching archival is on, a new-concepts section exists, and body application is authorized. Resolve all paths from `jj workspace root`. If `<root>/explainers/<date>-<concept-slug>.md` is ignored by repository policy, skip archival without forcing it. Write one file per concept with the project's accepted metadata and teaching content.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Repository-local syntax and active instructions win; apply compatible Go guidance to message quality, clarity, and structure without imposing a fixed message shape.

Commit archive files as one JJ change using explicit filesets and a dynamic message derived from runtime instructions and recent history:

```bash
jj commit -m "<archive-message-derived-from-local-standards>" <explainer-fileset>...
```

Do not impose a fixed prefix, type, scope, subject, body, or example. Move the feature bookmark to the resulting described change only after verifying that the archive files are the complete diff, then push that bookmark. Add provider-correct blob URLs with `gh browse -n -b <bookmark> -- <path>`; never hardcode a host. If archive write, commit, bookmark move, or push fails, warn and continue PR application without links only when the feature bookmark still names the already-pushed product changes.

## Body file

Use `<workspace-root>/.tmp/rocketclaw/` when `jj workspace root` succeeds. Outside a JJ workspace, use `.tmp/rocketclaw/` under the current local project directory. This is the only scratch location for this workflow.

Create a collision-resistant body filename in that directory, write the exact body, call `gh` with `--body-file <path>`, and remove the file immediately after the call. Do not run `jj` while the body file exists, and verify it is not included in any publish fileset. Never pass the body through stdin or command substitution.

```bash
gh pr create --title "<title-derived-from-local-standards>" --body-file "<workspace-root>/.tmp/rocketclaw/<unique-body-file>"
gh pr edit <pr-url> --title "<title-derived-from-local-standards>" --body-file "<workspace-root>/.tmp/rocketclaw/<unique-body-file>"
```

## Report and handoff

When this run applied a body containing new concepts, report their names and, in interactive full workflow, render one user invocation per concept as `/ce-explain <name>` except on Codex or a host that explicitly requires `$ce-explain <name>`. Output one invocation form only.

After a newly created PR, successful stack submit, or new changes pushed to an open PR, announce and invoke `ce-babysit-pr` through the host skill mechanism. Stack handoff starts from the bottom open non-draft PR with derived posture. In pipeline mode, wait for its structured stop and propagate typed `needs-human` residuals unchanged under `## Needs your decision`.

Skip only for `babysit:off`, a winning `auto_babysit: false`, description-only/update, no PR mutation, non-GitHub, a draft unless an explicit watch mode forces monitoring, or a head bookmark whose remote cannot be pushed. Fork PRs remain drivable when the selected head remote is pushable. Never recreate babysit mechanics or substitute another watcher. A failed handoff is a blocker.
