# Retained output

Honor an explicit user destination. Otherwise, use the project's established durable artifact convention under the resolved artifact root; do not invent a second canonical plan. This reference governs a retained document from direct use; chat results and caller-owned artifacts keep their existing delivery contracts.

<!-- ce-docs-root:start -->
**Resolve the artifact root `<root>` before composing any artifact path.**

- **Read** `docs_root` from `<repo-root>/.rocketclaw/config.yaml` only. Resolve `<repo-root>` with `jj root` from the target workspace, capture its absolute path as `workspace_root`, and execute subsequent JJ commands with `(cd "$workspace_root" && jj ...)`. Do not read `docs_root` from `config.local.yaml`. Unset -> `<root>` is `docs`, exactly as before.
- **Validate** a set value: a repo-relative directory whose real, symlink-resolved path stays inside the repo and is neither the repo root nor under `.git/` or `.jj/`. Otherwise stop with an error naming `docs_root` and the value -- never fall back to `docs`.
- **Use** `<root>` as the sole artifact location: create it if absent, compose each path as `<root>/<subdir>` with this skill's own subdirectory, and never also read `docs`.
<!-- ce-docs-root:end -->
