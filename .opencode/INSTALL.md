# Installing RocketClaw for OpenCode V2

This plugin targets `opencode2` exclusively. The plugin id is `rocketclaw`.

OpenCode loads `.ts` and `.js` files from `.opencode/plugins/` automatically. From this checkout, `.opencode/plugins/rocketclaw.ts` is picked up with no extra config.

To load the package from another directory, add the package path to the `plugins` array in your global or project `opencode.json`:

```json
{
  "plugins": ["/path/to/this-plugin"]
}
```

Restart OpenCode after changing the config, or run `opencode2 service restart` if the server is already running. The plugin registers skills and user-invocable commands through the V2 `Plugin.define` lifecycle (`ctx.skill.transform` and `ctx.command.transform`); no Bun installer or generated skill copy is required.

Inspect loaded plugins:

```sh
opencode2 plugin list
opencode2 plugin list --builtin
```

Install a package plugin from a local path:

```sh
opencode2 plugin add /path/to/this-plugin
```

There is no `--dir` flag; the parent CLI takes an optional directory argument: `opencode2 <subcommand> [flags] [<directory>]`.
