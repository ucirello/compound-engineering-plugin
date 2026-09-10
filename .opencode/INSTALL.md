# Installing RocketClaw for OpenCode V2

This plugin targets `opencode2` exclusively. Add it to the `plugins` array in your global or project `opencode.json`:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "plugins": ["./"]
}
```

Restart OpenCode after changing the config. The plugin registers skills and commands through the V2 `Plugin.define` lifecycle; no Bun installer or generated skill copy is required.

Inspect loaded plugins with the OpenCode V2 CLI:

```sh
opencode2 plugin list
```

## Local Development

From this checkout, point OpenCode at the package path:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "plugins": ["/absolute/path/to/this-checkout"]
}
```

Restart OpenCode after changing the package source, or run `opencode2 service restart` if the server is already running.
