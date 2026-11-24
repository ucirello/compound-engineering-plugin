# Artifact Root

An explainer lands under `<root>/explainers/` only when archived to the repo, and learnings may be read under `<root>/solutions/`. Resolve `<root>` only when you compose such a path; a scratch-only or external-concept run never composes one. Pass the resolved path to any subagent, not the config.

<!-- ce-docs-root:start -->
**Resolve the artifact root `<root>` before composing any repository artifact path.**

- **Read** `docs_root` only from `.rocketclaw/config.yaml` in the absolute workspace root verified with `jj root`. Do not read it from `config.local.yaml`. Unset -> `<root>` is `docs`.
- **Validate** a set value: a repo-relative directory whose real, symlink-resolved path stays inside the workspace and is neither the workspace root nor inside `.jj/` or `.git/`. Otherwise stop with an error naming `docs_root` and the value -- never fall back to `docs`.
- **Use** `<root>` as the sole artifact location: create it if absent, compose each path as `<root>/<subdir>` with this skill's own subdirectory, and never also read `docs`.
<!-- ce-docs-root:end -->
