# Repository evidence

Resolve the intended absolute workspace root from the request and active context; when needed, confirm it with `jj root` from an absolute working directory inside that workspace. Use the resolved directory as the explicit working directory for repository commands and pass it to scouts that inspect the repository. Do not switch workspaces or modify repository state to collect evidence.

Use native JJ for local repository evidence; never invoke Git directly. For a range, verify both revisions and use `jj diff --from "$base" --to "$head"`. For historical reasons, inspect full commit descriptions in the relevant ancestry using `jj log` with a template that includes `description`; use `diff_lines(regex:...)` when tracking the introduction or removal of text. If JJ evidence is unavailable, use the other in-scope sources and report what could not be verified.

Scope PR and issue lookups to the verified repository. If using `gh`, run it from the absolute workspace root with `GIT_DIR` set only for that lookup. Stop the CLI lookup if the root or backing store cannot be resolved:

```bash
(
  cd "$workspace_root" || exit 1
  GIT_DIR="$(jj git root)" || exit 1
  export GIT_DIR
  gh <read-only repository query>
)
```

For connectors, pass the verified repository identity explicitly. Unavailable PR evidence is not evidence that no PR exists.
