# `.rocketclaw/launch.json` schema

RocketClaw polish reads `.rocketclaw/launch.json` at the Jujutsu workspace root to resolve the dev-server start command. The schema is a compact launch configuration owned by RocketClaw; its fields remain compatible with common editor launch concepts.

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

## Fields RocketClaw polish consumes

| Field | Required | Purpose |
|-------|----------|---------|
| `name` | yes (when multiple configurations) | Used to disambiguate when the array has more than one entry. RocketClaw polish asks the user to pick by `name`. |
| `runtimeExecutable` | yes | The binary RocketClaw polish spawns (e.g., `bin/dev`, `npm`, `overmind`, `bun`). |
| `runtimeArgs` | no | Array of arguments passed to `runtimeExecutable`. Default: empty array. |
| `port` | yes | The port the dev server will listen on. RocketClaw polish probes `http://localhost:<port>` for reachability and uses it for browser handoff. |
| `cwd` | no | Workspace-relative working directory for the dev server. Default: workspace root. Useful for monorepos (`apps/web`, `packages/frontend`). |
| `env` | no | Additional environment variables for the dev-server process. Default: inherit the AI Assistant's environment. |

## Stub template (written on first run when user accepts)

When RocketClaw polish auto-detects a project type and the user confirms "Save this as `.rocketclaw/launch.json`?", the AI Assistant writes a minimal stub derived from the detected type. These templates intentionally use common defaults that users can edit later.

### Rails stub

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Rails dev",
      "runtimeExecutable": "bin/dev",
      "runtimeArgs": [],
      "port": 3000
    }
  ]
}
```

### Next.js stub

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Next dev",
      "runtimeExecutable": "npm",
      "runtimeArgs": ["run", "dev"],
      "port": 3000
    }
  ]
}
```

### Vite stub

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Vite dev",
      "runtimeExecutable": "npm",
      "runtimeArgs": ["run", "dev"],
      "port": 5173
    }
  ]
}
```

### Procfile / Overmind stub

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Overmind dev",
      "runtimeExecutable": "overmind",
      "runtimeArgs": ["start", "-f", "Procfile.dev"],
      "port": 3000
    }
  ]
}
```

### Nuxt stub

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Nuxt dev",
      "runtimeExecutable": "npm",
      "runtimeArgs": ["run", "dev"],
      "port": 3000
    }
  ]
}
```

### Astro stub

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Astro dev",
      "runtimeExecutable": "npm",
      "runtimeArgs": ["run", "dev"],
      "port": 4321
    }
  ]
}
```

### Remix stub

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Remix dev",
      "runtimeExecutable": "npm",
      "runtimeArgs": ["run", "dev"],
      "port": 3000
    }
  ]
}
```

### SvelteKit stub

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "SvelteKit dev",
      "runtimeExecutable": "npm",
      "runtimeArgs": ["run", "dev"],
      "port": 5173
    }
  ]
}
```

## Why a subset of VS Code's schema

RocketClaw polish does not use `type`, `request`, `console`, `stopOnEntry`, or other debugger fields. Including them is harmless, but the stub writer never adds them. The supported fields describe how to start a long-running dev server on a known port.

## Ownership notes

`.rocketclaw/launch.json` sits at a clear workspace-root trust boundary and is user-authored or user-approved. Keep editor-specific handoff behavior in `ide-detection.md`; do not duplicate or symlink this configuration into harness-owned namespaces automatically.
