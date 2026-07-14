# Shared Repo-Grounding Profile Cache

Read this when a repo-grounding skill needs the question-agnostic **project profile** (stack, deps, conventions, structure). The profile is derived once and reused within a session and across sessions and skills at an unchanged commit — only the *question-specific* grounding for the current run is ever re-derived.

This file is **byte-duplicated** into every consuming skill (the plugin has no cross-skill import mechanism). All copies must stay identical; `tests/repo-profile-cache-parity.test.ts` enforces it. The deterministic cache I/O lives in the co-located `scripts/repo-profile-cache.py`; the derivation-on-miss is done by the co-located `references/agents/repo-profiler.md` persona.

## What is cached (the agnostic profile)

A single JSON object, versioned by `profile_schema_version`:

- **Stack & versions** — languages, major frameworks + versions, build/test tooling.
- **Dependency surface** — manifest + lockfile paths, top-level dependencies, project license + dependency licenses.
- **Topology** — monorepo/workspace map, deployment model, API styles, data stores, module layout.
- **Conventions & instruction files** — paths + digests of the *root* `AGENTS.md`/`CLAUDE.md`/`GEMINI.md`/`ARCHITECTURE.md`/`README.md`/`CONTRIBUTING.md`/`STRATEGY.md`.
- **Vocabulary** — `CONCEPTS.md` canonical terms.

## What is NOT cached (always re-globbed fresh)

Never read from the cache — recompute every run:

- The `docs/solutions/` enumeration (a new learning, even uncommitted, must be visible — re-globbing it is ~free and the match reads files fresh anyway).
- Subdirectory-scoped instruction files (area-scoped `CLAUDE.md`/`AGENTS.md`).
- All question-specific grounding: a candidate's call-sites/footprint, prior-decision matches, feature patterns, JJ history of touched files, tracker/PR activity, external research.

## Cache location & key

```
<workspace-root>/.tmp/repo-profile/<root-id>/<working-copy-id>.json
```

- `<root-id>` = lexicographically-first commit ID from `jj log -r 'roots(::@)' --no-graph` — the repository identity.
- `<working-copy-id>` = commit ID from `jj log -r @ --no-graph` — the working state.

Each JJ workspace stores entries under its own root-local `.tmp`; when `jj workspace root` is unavailable, the storage root falls back to local `.tmp`. Lookup uses JJ metadata only; on a hit, only this one file is read.

## Protocol — how a skill uses it

Invoke the helper via the `SKILL_DIR` anchor (set `SKILL_DIR` to the absolute path of the directory containing the SKILL.md you just read; the Bash tool's cwd is the user's project, not the skill dir):

```bash
SKILL_DIR="<absolute path of this skill's directory>"
python3 "$SKILL_DIR/scripts/repo-profile-cache.py" get
```

`get` prints exactly one of:

- `HIT` then the profile JSON on the following lines → load it as the agnostic profile; skip derivation.
- `MISS` then a write-path on the next line → dispatch the `repo-profiler` persona to derive the profile, write its JSON output to a file, then persist it. This `put` runs after the profiler, so it is a **separate Bash-tool call** from the `get` above — shell variables do not persist between calls, so **re-set `SKILL_DIR` in the same command**:
  ```bash
  SKILL_DIR="<absolute path of this skill's directory>"
  python3 "$SKILL_DIR/scripts/repo-profile-cache.py" put <profile-json-file>
  ```
- `NO-CACHE` → no JJ repo or no writable workspace-local cache. Derive the profile fresh for this run and **skip** `put` (nothing to persist).

In all three cases, after the agnostic profile is in hand, run **this skill's question-specific grounding fresh** on top of it.

## Freshness (delta-aware)

A cached entry is a `HIT` only when its `profile_schema_version` and JJ working-copy commit ID match. JJ snapshots tracked and newly-added files into the working-copy commit, so any profile-input edit changes the key. The profile-input schema remains the contract for what the profiler reads; unrelated changes may conservatively create another cache entry.

## Degradation

The cache is an optimization, never a correctness dependency. Outside a JJ repo, with no writable workspace-root `.tmp` or local `.tmp` fallback, or on an unreadable/malformed entry, the helper returns `NO-CACHE`/`MISS` (exit 0) and the skill derives fresh. It never blocks and never serves a profile it cannot prove fresh. And if the helper *invocation itself* fails — a non-zero exit, empty output, or an unresolved `SKILL_DIR` so the script isn't found — treat it exactly like `NO-CACHE`: derive the profile fresh this run and proceed. Never stall waiting on the cache.
