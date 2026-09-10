# Installing Compound Engineering for OpenCode V2

This plugin targets `opencode2` exclusively. Add it to the `plugins` array in your global or project `opencode.json`:

```json
{
  "plugins": ["compound-engineering@git+https://github.com/EveryInc/compound-engineering-plugin.git"]
}
```

Restart OpenCode after changing the config. The plugin registers skills and commands through the V2 `Plugin.define` lifecycle; no Bun installer or generated skill copy is required.

To pin a release, add a tag. Replace `X.Y.Z` with the release you want — see the [releases page](https://github.com/EveryInc/compound-engineering-plugin/releases) for available tags:

```json
{
  "plugins": ["compound-engineering@git+https://github.com/EveryInc/compound-engineering-plugin.git#compound-engineering-vX.Y.Z"]
}
```

Install or inspect the package with the OpenCode V2 CLI:

```sh
opencode2 plugin add compound-engineering@git+https://github.com/EveryInc/compound-engineering-plugin.git
opencode2 plugin list
```

## Local Development

From this checkout, point OpenCode at the package path:

```json
{
  "plugins": ["/path/to/compound-engineering-plugin"]
}
```

Restart OpenCode after changing the package source, or run `opencode2 service restart` if the server is already running.
