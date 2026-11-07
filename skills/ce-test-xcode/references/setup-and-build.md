# Setup and build

This reference owns the path from invocation to a launched app with log capture running.

## Availability gate

Confirm that the active harness exposes XcodeBuildMCP's simulator-listing capability and that the call succeeds. Host-specific MCP tool prefixes are adapters, not the contract.

If the capability is absent or errors, stop before discovery or build. Report that XcodeBuildMCP must be installed and connected, with these setup options for the user to run:

```text
Homebrew:
  brew tap getsentry/xcodebuildmcp && brew install xcodebuildmcp

npx:
  npx -y xcodebuildmcp@latest mcp
```

Then tell the user to add XcodeBuildMCP as an MCP server and restart the agent. Testing does not authorize installing or configuring it for them.

For OpenCode setup, tell the user to merge `"experimental": { "subagent_depth": 3 }` into the existing `~/.config/opencode/opencode.json`, or use `opencode debug paths` / `opencode debug paths config` to locate their actual global configuration directory and update its existing `opencode.json(c)`. Preserve higher integer depths, unrelated settings, and sibling `experimental` fields; do not replace the file or create a competing JSON/JSONC file. Depth at least `3` supports deep agentic delegation; installing the plugin or its package-local configuration alone does not enable this consumer setting, and higher-precedence configuration must not lower it below `3`. This is user setup guidance, not authority to modify host configuration.

Also stop with the missing prerequisite when Xcode, its command-line tools, a valid project/workspace, or an iOS simulator is unavailable.

## Discover and launch

1. Discover projects and workspaces, then list schemes for the selected project. An empty argument or `current` selects the default or last-used scheme; a named argument selects that scheme. Ask only when no such scheme can be resolved or project discovery itself remains materially ambiguous.
2. List simulators. Reuse a compatible booted simulator when practical; otherwise prefer an available iPhone 15 Pro and boot it by UUID. Wait until it is ready.
3. Build the simulator app with the selected project/workspace and scheme. On failure, report the relevant build errors and stop; do not install or launch a missing artifact.
4. From the successful build result, retain the app path and bundle identifier. Install the app, launch it, and start simulator log capture for that bundle.

Any failure before the app is visibly launched with log capture running is a setup blocker: preserve its evidence, report it, and stop later stages.

At handoff, retain the project/workspace, scheme, simulator identity, app identity, and log-capture handle needed by `test-and-report.md`.

Keep run-owned screenshots, exported logs, and temporary/error evidence under the target workspace's absolute `.tmp/` directory (local `.tmp/` when no JJ repository exists), not OS-global temporary storage. Configure capture output paths there when supported; otherwise copy returned evidence there before handoff without deleting tool-owned originals.
