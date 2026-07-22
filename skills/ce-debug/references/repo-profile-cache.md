# Shared Repo-Grounding Profile Cache

Read this when a repo-grounding skill needs the question-agnostic **project profile**: stack, dependencies, topology, conventions, and vocabulary. Only question-specific grounding is derived fresh for each run.

This file, `scripts/repo-profile-cache.py`, and `references/agents/repo-profiler.md` are byte-duplicated into every consumer and must remain identical.

## Cached Profile

The versioned JSON object preserves this complete shape:

- `stack`: languages, frameworks and versions, build/test tooling.
- `dependencies`: manifests, lockfiles, direct dependencies, project license, dependency licenses.
- `topology`: workspace map, deployment model, API styles, data stores, module layout.
- `conventions`: root instruction files and project-wide rules, coding standards, testing, review process, strategy.
- `vocabulary`: canonical terms from `CONCEPTS.md` when present.

Never cache the `docs/solutions/` enumeration, subdirectory-scoped instruction files, or question-specific grounding. Recompute those every run.

## Location And Identity

```text
<workspace-root>/.tmp/rocketclaw/repo-profile/<change-id>/<commit-id>.json
```

- `<workspace-root>` comes from `jj workspace root`, with the physical current directory as fallback.
- `<change-id>` and `<commit-id>` come from `jj log -r @`; together they identify the stable change and its current working-copy state.
- The cache never uses an OS-global temporary directory.

## Protocol

Invoke the co-located helper through the skill-directory anchor:

```bash
SKILL_DIR="<absolute path of this skill's directory>"
python3 "$SKILL_DIR/scripts/repo-profile-cache.py" get
```

The result is exactly one of:

- `HIT` followed by profile JSON: load it and skip agnostic derivation.
- `MISS` followed by the selected cache path: dispatch `references/agents/repo-profiler.md`, write its JSON to a file, then persist it in a separate call. Re-set `SKILL_DIR` because shell state does not persist:
  ```bash
  SKILL_DIR="<absolute path of this skill's directory>"
  python3 "$SKILL_DIR/scripts/repo-profile-cache.py" put <profile-json-file>
  ```
- `NO-CACHE`: derive fresh and skip `put`.

After every result, run the consumer's question-specific grounding fresh.

## Freshness And Safety

A hit requires matching schema, change, and commit identities; a current-user-owned readable cache file; the complete nested profile shape; and no profile-input path in `jj diff --summary -r @`. Both rename endpoints are checked. Inputs conservatively include manifests and lockfiles at any depth, runtime selectors, project files, licenses, root instruction/docs, project-wide rules, CI and deployment topology. Non-input source or planning changes do not invalidate.

`put` applies the same profile and diff checks. It writes a private, unique file in the destination directory with `os.open(..., os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)`, then publishes it with `os.replace` and cleans up an unpublished file on failure.

The cache is only an optimization. Unavailable JJ metadata, failed diff inspection, malformed data, ownership mismatch, unwritable workspace storage, helper failure, or an unresolved `SKILL_DIR` must degrade to `MISS` or `NO-CACHE` without blocking fresh derivation.
