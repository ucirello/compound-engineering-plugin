# `.workspace/launch.json` schema

Polish reads `.workspace/launch.json` at the Jujutsu workspace root to resolve the dev-server start command. The path and schema are runtime-neutral and contain no tool attribution.

## Top-level shape

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "<human label>",
      "runtimeExecutable": "<binary>",
      "runtimeArgs": ["<arg>", "<arg>"],
      "port": <number>,
      "cwd": "<optional, workspace-relative>",
      "env": { "<key>": "<value>" }
    }
  ]
}
```

## Fields polish consumes

| Field | Required | Purpose |
|-------|----------|---------|
| `name` | yes (when multiple configurations) | Used to disambiguate when the array has more than one entry. Polish asks the user to pick by `name`. |
| `runtimeExecutable` | yes | The binary polish spawns (e.g., `bin/dev`, `npm`, `overmind`, `bun`). |
| `runtimeArgs` | no | Array of arguments passed to `runtimeExecutable`. Default: empty array. |
| `port` | no | The dev-server port. A numeric value completes the tuple's port fact; when the command, working directory, and environment are also usable, no project detection or resolver runs. When omitted, polish resolves only the missing port from the selected project type. The port seeds `http://localhost:<port>` as the default endpoint candidate; server evidence or a user correction may replace that candidate, so the schema does not lock the URL scheme. |
| `cwd` | no | Workspace-relative working directory for the dev server. Default: workspace root. Useful for monorepos (`apps/web`, `packages/frontend`). |
| `env` | no | Additional environment variables for the dev-server process. Default: inherit polish's environment. |

## Saved configuration

When auto-detection completes a missing tuple fact and the user confirms the save, write the completed runtime-local tuple. Preserve every usable fact from a selected configuration and add only facts resolved during this run. Derive `name` from the selected project or command without naming an agent, model, vendor, or author. Record the actual `runtimeExecutable`, `runtimeArgs`, `cwd`, `env`, and numeric `port`; do not substitute framework defaults or emit a fixed template.

The writer adds only the fields polish consumes. Existing unrelated fields remain untouched when updating a configuration.
