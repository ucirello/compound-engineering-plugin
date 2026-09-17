# Installing RocketClaw for OpenCode

Add RocketClaw to the `plugins` array in your global or project `opencode.json`:

```json
{
  "plugins": ["rocketclaw@git+https://github.com/EveryInc/rocketclaw-plugin.git"]
}
```

Restart OpenCode after changing the config. The OpenCode plugin registers bundled skills and user-invocable slash commands; no Bun installer or generated skill copy is required.

To pin a release, add a tag. Replace `X.Y.Z` with the release you want — see the [releases page](https://github.com/EveryInc/rocketclaw-plugin/releases) for available tags:

```json
{
  "plugins": ["rocketclaw@git+https://github.com/EveryInc/rocketclaw-plugin.git#rocketclaw-vX.Y.Z"]
}
```

## Local Development

From this checkout, point OpenCode at the package path:

```json
{
  "plugins": ["/path/to/rocketclaw-plugin"]
}
```

Restart OpenCode after changing the package source.
