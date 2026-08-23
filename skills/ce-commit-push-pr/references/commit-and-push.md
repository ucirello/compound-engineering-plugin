# Describing and pushing

If retrospective stack construction already created layers, skip this ordinary path; Step 5 submits the stack.

When work sits on the default bookmark, read `references/bookmark-creation.md` before continuing. It owns stale local base, local-only work, and collision-safe rooting from the remote base.

Group clearly distinct concerns at file granularity into at most 2-3 changes. One change is correct when separation is ambiguous. Honor `exclude:<paths>` exactly; excluded paths remain in `@` and are named in the report. Preserve a known plan-unit association in the local convention without inventing fixed syntax.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. The project's active instructions and the description syntax observed at runtime in `jj log` win. Apply compatible Go guidance only to quality, clarity, and structure; it does not prescribe any fixed syntax or example.

For each group, use exact filesets:

```bash
jj commit -m "<message composed from the standards above>" <file1> <file2>
```

The selected paths stay in the described parent and all remaining work moves into the child working-copy change. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. The project's active instructions and the description syntax observed at runtime in `jj log` win during validation. Apply compatible Go guidance only to quality, clarity, and structure; it does not prescribe any fixed syntax or example. Verify each result with `jj show`; repair topology before publication if grouping changed dependencies.

Immediately before pushing, re-confirm the intended feature bookmark. Move it to the final described change, normally `@-`, never to an undescribed working-copy change:

```bash
jj bookmark set <bookmark> -r @-
jj git push --bookmark <bookmark> --remote <remote>
```

An empty working-copy change with an already synchronized bookmark is a no-op.
