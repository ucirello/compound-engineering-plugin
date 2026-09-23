# Installing RocketClaw for OpenCode V2

Point OpenCode at the RocketClaw package directory in your global or project `opencode.json`:

```json
{
  "plugins": ["/path/to/rocketclaw"]
}
```

Restart OpenCode after changing the config. The plugin registers bundled skills and a slash command for each user-invocable skill directly; no Bun installer or generated skill copy is required. Commands preserve the user's prompt and attachments and select the corresponding skill by ID.

The package entrypoint is `.opencode/plugins/rocketclaw.ts` and uses the OpenCode V2 plugin API. Install the package dependencies before loading a local checkout. Skills with `disable-model-invocation: true` remain explicitly selectable but are omitted from the model's available-skill list. Skills with `user-invocable: false` or `slash: false` do not receive commands.

Skill registrations use `path`, as required by the published `@opencode/plugin` 2.0.15 schema; the V2 plugins guide currently shows `location` in its skill example.

## Local Development

Opening this checkout as an OpenCode project also works without a config entry: OpenCode auto-discovers `.opencode/plugins/rocketclaw.ts`.

The separate `.opencode/plugins/continue-on-deny/` plugin supports the launcher policy: permission decisions requiring a prompt become automatic denials with the reason `Permission denied. Do not retry this. Try another approach.` Allowed actions remain allowed. The hook operates before prompting and does not intercept human rejection replies. Automatic denial must return to the model loop so it can choose another approach.

When loading RocketClaw as a package in another project, the launcher must load the separate `continue-on-deny` plugin if that policy is required. Loading the main package alone registers skills and commands.
