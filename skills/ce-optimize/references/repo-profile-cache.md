# Shared Repo-Grounding Profile Cache

Read this when a repo-grounding skill needs the question-agnostic **project profile** (stack, deps, conventions, structure). The profile is derived once and reused within and across sessions and skills at an unchanged JJ working-copy revision. Only the *question-specific* grounding for the current run is re-derived.

This file is byte-duplicated into every consuming skill because skills cannot import across directories. All copies must stay identical. The deterministic cache I/O lives in the co-located `scripts/repo-profile-cache.py`; the derivation-on-miss is done by the co-located `references/agents/repo-profiler.md` persona.

## What is cached

A single JSON object, versioned by `profile_schema_version`:

- **Stack & versions** - languages, major frameworks and versions, build/test tooling.
- **Dependency surface** - manifest and lockfile paths, top-level dependencies, project license and dependency licenses.
- **Topology** - monorepo/workspace map, deployment model, API styles, data stores, module layout.
- **Conventions & instruction files** - paths and digests of the root `AGENTS.md`/`CLAUDE.md`/`GEMINI.md`/`ARCHITECTURE.md`/`README.md`/`CONTRIBUTING.md`/`STRATEGY.md`.
- **Vocabulary** - `CONCEPTS.md` canonical terms.

## What is not cached

Recompute these every run:

- The `docs/solutions/` enumeration, so a newly written learning is immediately visible.
- Subdirectory-scoped instruction files such as area-scoped `CLAUDE.md` or `AGENTS.md`.
- All question-specific grounding: call sites, feature footprints, prior-decision matches, feature patterns, JJ history of touched files, tracker/PR activity, and external research.

## Cache location and key

```
$(jj workspace root)/.tmp/rocketclaw/repo-profile/<root-id>/<revision-id>.json
```

- `<root-id>` is the lexicographically first non-virtual root revision selected by `roots(::@ ~ root())`.
- `<revision-id>` is the current working-copy commit ID selected by `@`.

The helper resolves the JJ workspace root first and keeps the cache entry, profiler handoff file, and atomic staging files below that workspace's `.tmp/rocketclaw/repo-profile`. If no JJ workspace can be resolved, the path fallback is the current project's `.tmp/rocketclaw/repo-profile`, but the helper returns `NO-CACHE` because no JJ revision key can be proven.

## Protocol

Invoke the helper via the `SKILL_DIR` anchor. Set `SKILL_DIR` to the absolute path of the directory containing the SKILL.md you just read; the shell's working directory is the user's project, not the skill directory.

```bash
SKILL_DIR="<absolute path of this skill's directory>"
python3 "$SKILL_DIR/scripts/repo-profile-cache.py" get
```

`get` prints exactly one of:

- `HIT` followed by the profile JSON. Load it as the agnostic profile and skip derivation.
- `MISS` followed by a workspace-local write path. Dispatch the `repo-profiler` persona, write its JSON output directly to that path, then persist it. `put` is a separate shell call, so set `SKILL_DIR` again in the same command:
  ```bash
  SKILL_DIR="<absolute path of this skill's directory>"
  python3 "$SKILL_DIR/scripts/repo-profile-cache.py" put <miss-write-path>
  ```
- `NO-CACHE`. Derive the profile fresh for this run and skip `put`.

After obtaining the agnostic profile in any case, run this skill's question-specific grounding fresh.

## Freshness

A cached entry is a `HIT` only when its `profile_schema_version`, root ID, and revision ID match the current JJ workspace state. JJ snapshots non-ignored workspace changes before resolving `@`, so an input change produces a different content-addressed working-copy revision and cache key. The helper also rejects `put` when its handoff path was produced for a different revision.

## Degradation

The cache is an optimization, never a correctness dependency. A missing JJ workspace, an unwritable workspace-local cache, malformed content, a revision race, or a helper failure degrades to `NO-CACHE` or `MISS` without blocking the caller. The skill derives fresh and never serves a profile it cannot prove current.
