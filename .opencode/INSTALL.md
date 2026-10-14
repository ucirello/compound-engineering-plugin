# Installing RocketClaw for OpenCode V2

Add the RocketClaw package to the `plugins` array in your project `opencode.json`, using the actual fork's package URL:

```json
{
  "plugins": ["<RocketClaw package git URL>"],
  "experimental": { "subagent_depth": 3 }
}
```

This plugin supports OpenCode V2 only. Restart OpenCode after changing the config. It registers RocketClaw skills and `/commands` directly; no Bun installer or generated skill copy is required.

To pin a release, append the verified fork release tag to its Git package URL:

```json
{
  "plugins": ["<RocketClaw package git URL>#<verified-release-tag>"],
  "experimental": { "subagent_depth": 3 }
}
```

## Local Development

From this checkout, point OpenCode at the package path:

```json
{
   "plugins": ["/absolute/path/to/rocketclaw"],
   "experimental": { "subagent_depth": 3 }
}
```

Restart OpenCode after changing the package source. Opening this checkout as an OpenCode project uses the shipped root `opencode.json`, whose relative entrypoint is `./.opencode/plugins/rocketclaw.ts` and whose `experimental.subagent_depth` default is `3`.

Installing a Git/npm plugin does not merge configuration bundled inside the package into a consuming project. Consumers must explicitly adopt the depth setting in their own project configuration, preserving a higher existing value and unrelated experimental settings. This is a shipped project default, not an in-memory plugin-enforced floor. See the [V2 loading guide](https://opencode.ai/v2/docs/plugins) and [configuration discovery guide](https://opencode.ai/v2/docs/config).
