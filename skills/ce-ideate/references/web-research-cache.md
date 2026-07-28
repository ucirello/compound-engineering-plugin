# Web Research Cache (V15)

Read this RocketClaw reference when checking the V15 cache before dispatching `web-researcher`, or when appending fresh research to the cache after dispatch. The behavior here is conditional — most invocations either hit the cache or write to it once and move on.

## Cache file shape

```json
[
  {
    "key": {
      "mode": "repo|elsewhere-software|elsewhere-non-software",
      "focus_hint_normalized": "<lowercase, whitespace-collapsed focus hint or empty string>",
      "topic_surface_hash": "<short hash of the user-supplied topic surface>"
    },
    "result": "<web-researcher output as plain text>",
    "ts": "<iso8601>"
  }
]
```

Files live under `<scratch-dir>/web-research-cache.json`, where `<scratch-dir>` is `<workspace-root>/.tmp/ce-ideate/<run-id>` or the local `.tmp` fallback resolved once in SKILL.md Phase 1.

## Reuse check

Before dispatching `web-researcher`, use the native file-search tool to list cache files under the workspace-local scratch collection — refinement loops within a session may legitimately reuse another run's cache by topic, not run-id:

```text
file-search: pattern=".tmp/ce-ideate/*/web-research-cache.json" path="<workspace-root or current-directory fallback>"
```

An empty result means no reusable cache exists; continue with a fresh dispatch.

Read each matching file. If any entry's `key` matches the current dispatch (same full mode variant — `repo`, `elsewhere-software`, or `elsewhere-non-software` — plus same case-insensitive normalized focus hint plus same topic surface hash), skip the dispatch and pass the cached `result` to the consolidated grounding summary. Mode variants must match exactly: `elsewhere-software` and `elsewhere-non-software` are distinct domains and must not cross-reuse. Note in the summary: "Reusing prior web research from this session — say 're-research' to refresh."

On `re-research` override, delete the matching entry and dispatch fresh.

## Append after fresh dispatch

After a fresh dispatch, append the new result to the current run's cache file at `<scratch-dir>/web-research-cache.json` using the absolute path from Phase 1 (create the file if needed; Phase 1 already created the directory safely). The next invocation in the session can reuse it via the native file-search listing above.

## Topic surface hash

The topic surface is the user-supplied content the web research is grounded on:
- **Elsewhere modes (`elsewhere-software`, `elsewhere-non-software`):** the user's topic prompt plus any Phase 0.4 intake answers (the actual subject the agent is researching). The two sub-modes are keyed separately — a reclassification between software and non-software for the same topic hash must force a fresh dispatch, since the research domain differs.
- **Repo mode:** the focus hint plus a stable repo discriminator. This keeps the cache key meaningful when focus is empty — two bare-prompt invocations in the same repo legitimately share research, but the key still differentiates repos. Cache files are isolated under each workspace's `.tmp`, but the discriminator still protects copied scratch collections and workspace moves. Resolve the discriminator with this fallback chain and hash the result (first 8 hex chars of sha256 is sufficient):
    1. The applicable remote URL from `jj git remote list` (`upstream` for a fork, otherwise `origin`) — stable across machines and correct for collaborators on the same remote.
    2. `jj workspace root` — absolute workspace path; machine-local but available in a Jujutsu workspace.
    3. The current working directory's absolute path — local `.tmp` fallback when outside a Jujutsu workspace.

Normalize before hashing: lowercase, collapse whitespace. (The repo discriminator hash is computed from the raw command output; only the focus hint and topic text are normalized.)

## Degradation

If the cache file is unreachable across invocations on the current platform (filesystem isolation, sandboxing, ephemeral working directory), degrade to "no reuse, dispatch every time." Surface the limitation in the consolidated grounding summary and proceed without reuse rather than inventing a capability the platform may not have.
