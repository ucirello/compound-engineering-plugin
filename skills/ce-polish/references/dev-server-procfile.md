# Procfile / Overmind dev-server recipe (auto-detect fallback)

Loaded when `detect-project-type.sh` returns `procfile` and there is no `.agents/launch.json` to consult. Rails apps with `bin/dev` take precedence over the bare Procfile path (see `dev-server-rails.md`).

## Signature

- `Procfile` or `Procfile.dev` exists at the workspace root
- `bin/dev` is **not** present (if it is, use the Rails recipe)

## Start command

Prefer `overmind` when available — it handles socket files, supports hot-restart per process, and is the community default for multi-process dev:

```bash
overmind start -f Procfile.dev
```

Fallback to `foreman` when `overmind` is not installed:

```bash
foreman start -f Procfile.dev
```

If both are missing, prompt the user for the start command rather than guessing.

## Port

Default: `3000`. Procfile-based projects list their processes in `Procfile.dev`, so the authoritative port comes from the `web:` line:

```
web: bundle exec puma -p 3000 -C config/puma.rb
worker: bundle exec sidekiq
```

Parse the `web:` line for `-p <n>` or `--port <n>`. If neither is present, fall through to the cascade in `references/dev-server-detection.md`.

## Stub generation

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

Substitute `foreman` if `overmind` is unavailable on the user's machine — the stub represents what the user will run, not a canonical recipe.

## Common gotchas

- **Socket files:** set `OVERMIND_SOCKET` to `<workspace-root>/.tmp/rocketclaw/polish/<run-id>/overmind.sock` before starting Overmind, using the current directory's `.tmp` when no JJ repository exists. Polish's kill-by-port logic reclaims the port but does not clean up the socket, so keep it in the same per-run directory as the server log.
- **Procfile vs Procfile.dev:** production and development Procfiles often differ. Always prefer `Procfile.dev` for polish.
- **Multiple web processes:** some Procfiles split web traffic across multiple processes (API + frontend). Polish can only open one URL — users with multi-web setups should author `.agents/launch.json` explicitly to select which process is "the dev server" for polish.
