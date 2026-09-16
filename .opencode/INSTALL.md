# Installing RocketClaw for OpenCode

RocketClaw targets **opencode2** v2.0.3. Use the V2 `plugins` key (not V1 `plugin`).

## CLI

Install a published package into the global config:

```sh
opencode2 plugin add <package>
```

List active plugins:

```sh
opencode2 plugin list
```

## Config

Add RocketClaw to the `plugins` array in your global or project `opencode.json`.

File URL:

```json
{
  "plugins": ["file:///path/to/this/checkout"]
}
```

Package form:

```json
{
  "plugins": [
    {
      "package": "file:///path/to/this/checkout"
    }
  ]
}
```

A plugin under `.opencode/plugins/` in this checkout is also discovered automatically.

Restart after changing the config:

```sh
opencode2 service restart
```

The plugin registers skills from this checkout's `skills/` directory and exposes each user-invocable skill as a slash command that attaches that skill id. No generated skill copy is required.
