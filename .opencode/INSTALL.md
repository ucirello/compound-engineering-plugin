# Installing RocketClaw for OpenCode

Add RocketClaw to the `plugins` array in your global or project `opencode.json`:

```json
{
  "plugins": ["git+https://github.com/EveryInc/compound-engineering-plugin.git"]
}
```

You can also install it into the global OpenCode config:

```
opencode2 plugin add git+https://github.com/EveryInc/compound-engineering-plugin.git
```

Restart OpenCode after changing the config. The OpenCode plugin registers the RocketClaw skills directory directly; no Bun installer or generated skill copy is required.

To pin a release, add a tag. Replace `X.Y.Z` with the release you want — see the [releases page](https://github.com/EveryInc/compound-engineering-plugin/releases) for available tags:

```json
{
  "plugins": ["git+https://github.com/EveryInc/compound-engineering-plugin.git#compound-engineering-vX.Y.Z"]
}
```

```
opencode2 plugin add git+https://github.com/EveryInc/compound-engineering-plugin.git#compound-engineering-vX.Y.Z
```

## Local Development

From this checkout, point OpenCode at the package path:

```json
{
  "plugins": ["/path/to/rocketclaw"]
}
```

Restart OpenCode after changing the package source.
