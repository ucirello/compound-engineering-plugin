# Installing Compound Engineering for OpenCode

Add Compound Engineering to the `plugins` array in your global or project `opencode.json`:

```json
{
  "plugins": ["compound-engineering@git+https://github.com/EveryInc/compound-engineering-plugin.git"]
}
```

This entrypoint requires OpenCode V2; OpenCode 1.x is not supported.

Restart OpenCode after changing the config. The plugin registers the Compound Engineering skills and `/commands` directly; no Bun installer or generated skill copy is required.

To pin a release, add a tag. Replace `X.Y.Z` with the release you want — see the [releases page](https://github.com/EveryInc/compound-engineering-plugin/releases) for available tags:

```json
{
  "plugins": ["compound-engineering@git+https://github.com/EveryInc/compound-engineering-plugin.git#compound-engineering-vX.Y.Z"]
}
```

## Local Development

From this checkout, point OpenCode at the package path:

```json
{
  "plugins": ["/path/to/compound-engineering-plugin"]
}
```

Restart OpenCode after changing the package source. Opening this checkout as an OpenCode project loads `.opencode/plugins/rocketclaw.ts` through the shipped root `opencode.json` (the entrypoint is also auto-discoverable).

The shipped project configuration sets `experimental.subagent_depth` to `3`. Installing the package as a plugin does not merge its bundled configuration into a consuming project. Consumers must explicitly adopt that setting in their own project configuration, preserving any higher value and unrelated settings. A `.opencode/opencode.json(c)` configuration overrides direct project configuration, so check that it does not defeat the intended depth.
