# Retained output

Honor an explicit user destination. Otherwise, use the project's established durable artifact convention under the resolved artifact root; do not invent a second canonical plan. This reference governs a retained document from direct use; chat results and caller-owned artifacts keep their existing delivery contracts.

<!-- ce-docs-root:start -->
**Resolve the artifact root `<root>` before composing any artifact path.**

- **Read** `docs_root` from `<workspace-root>/.rocketclaw/config.yaml` only. Verify the [JJ workspace root](https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace-root) with `jj workspace root` from the absolute target workspace root. Do not read `docs_root` from `config.local.yaml`. Unset -> `<root>` is `docs`, exactly as before.
- **Validate** a set value: a workspace-relative directory whose real, symlink-resolved path stays inside the workspace and is neither the workspace root nor repository metadata (`.jj` or `.git`, including their contents). Otherwise stop with an error naming `docs_root` and the value -- never fall back to `docs`.
- **Use** `<root>` as the sole artifact location: create it if absent, compose each path as `<root>/<subdir>` with this skill's own subdirectory, and never also read `docs`.
<!-- ce-docs-root:end -->
