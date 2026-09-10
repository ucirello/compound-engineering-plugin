# Installing RocketClaw for OpenCode

Add RocketClaw to the `plugins` array in your global or project `opencode.json`:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "plugins": ["./"]
}
```

Restart OpenCode after changing the config. The OpenCode plugin registers the RocketClaw skills directory directly; no Bun installer or generated skill copy is required.

## Local Development

From this checkout, point OpenCode at the package path:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "plugins": ["/absolute/path/to/this-checkout"]
}
```

Restart OpenCode after changing the package source.
