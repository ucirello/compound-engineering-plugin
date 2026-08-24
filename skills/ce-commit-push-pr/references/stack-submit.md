# Opt-in stack construction and submission

Load only in Stack mode. `gh stack` is a soft dependency unless the user's explicit request or standing policy requires a stack, in which case inability to use it is a blocker. Read `references/gh-stack-cli.md` before provider mutation.

## Probe and topology

Probe `gh stack view --json`, `jj git colocation status`, `jj bookmark list --all-remotes`, and `jj workspace list` separately. `gh stack` requires a colocated Git-backed JJ repository; do not replace failed interop with Git repository commands.

When a parent PR is named, classify by PR number and resolve its exact head OID and owner. When a parent bookmark is named, fetch it from the selected JJ Git remote and prove its target. Unknown ownership, a target collision, provider exit 6 or 9, or divergence after import is a residual rather than permission to create another stack.

Preserve existing stack topology. A new upstack layer is based on the authoritative parent change: the current tracked remote bookmark when it contains the parent, otherwise the proven local parent change before first submit. Create each JJ change with `jj new <parent-change>`, commit its fileset, place a same-named bookmark on it, export, then let `gh stack` adopt it. Do not rebase a layer onto the repository default after its parent is known.

## Retrospective construction

Inspect the complete intended range and working-copy diff. Derive the smallest useful linear set of independently reviewable layers, foundation first. Each layer must be coherent against its parent and cannot depend on an upstack layer. Use existing change boundaries or whole-path filesets; hunk-level partitioning and published-history rewrites require explicit confirmation. In pipeline mode, stop with a residual when either is required.

`exclude:<paths>` belongs to no layer. Keep excluded paths in the original workspace's working-copy change. When isolation is needed, add a JJ workspace under `<workspace-root>/.tmp/rocketclaw/<unique-stack-workspace>` with `jj workspace add`; this is the only isolation location. Forget and remove that temporary JJ workspace after successful reconciliation. Stop if switching or rebasing would include, overwrite, or conflict with excluded content.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

For each layer, derive its description from runtime project instructions and recent history. Use compatible Go quality guidance only: a concise summary and an explanatory body when needed. Do not impose a fixed prefix, type, scope, subject, body, template, or example. A supplied Implementation Unit ID may be appended only when local conventions permit it and the layer maps unambiguously to that unit.

```bash
jj new <parent-change>
jj commit -m "<layer-message-derived-from-local-standards>" <layer-fileset>...
jj bookmark create <layer-bookmark> -r <layer-change>
jj git export
gh stack init --base "<base-bookmark>" "<bottom-bookmark>" "<next-bookmark>"
```

For subsequent layers, use the prior layer change as parent and create or safely advance its bookmark before export. After every `gh stack` mutation, run `jj git import` and verify that stack order, bookmark targets, and the top layer's aggregate diff match the plan. Keep an operation ID or unchanged source change as recovery evidence before any authorized rewrite.

## Submit

Archival enabled for this run is a pre-submit residual because adding an archive change after provider submission can invalidate managed topology. The user can rerun with `archive:off`.

Inspect every existing stack PR for draft state. If any draft was not explicitly authorized to become ready, run `gh stack submit --auto` without `--open`; remaining drafts are a residual before babysit. Otherwise:

```bash
gh stack submit --auto --open
```

Import after submit and verify local bookmarks against provider heads. Map every newly created PR to its head bookmark and URL. Compose and apply metadata per PR using its immediate parent and exact head. Preserve existing stack PR titles and bodies unless rewrite intent is explicit; pipeline mode defaults to no rewrite.

Managed members are landed only with `gh stack merge`, owned by babysit under `posture:stack-land` or by the user.
