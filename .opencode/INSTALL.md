# Installing RocketClaw for OpenCode

Add RocketClaw to the `plugins` array in your global or project `opencode.json`:

```json
{
  "plugins": ["rocketclaw"]
}
```

Restart OpenCode after changing the config. The OpenCode plugin registers RocketClaw skills directly; no Bun installer or generated skill copy is required.

To pin a release, add a version. Replace `X.Y.Z` with the release you want:

```json
{
  "plugins": ["rocketclaw@X.Y.Z"]
}
```

Git package specs and local paths also work:

```json
{
  "plugins": [
    "github:example/rocketclaw",
    "/absolute/path/to/rocketclaw"
  ]
}
```

OpenCode V2 auto-discovers `.ts` / `.js` files under `.opencode/plugins/`. A checkout that already contains `.opencode/plugins/rocketclaw.ts` loads it without an extra `plugins` entry.

## Local Development

From this checkout, point OpenCode at the package path:

```json
{
  "plugins": ["/path/to/rocketclaw"]
}
```

Restart OpenCode after changing the package source. The config key is `plugins` (not `plugin`). The directory argument to `opencode2` is positional, not `--dir`.
