# Setup and build

This reference owns the path from invocation to a launched app with log capture running.

## Availability gate

Confirm that OpenCode exposes XcodeBuildMCP's simulator-listing capability and that the call succeeds. MCP tool prefixes are not the contract.

If the capability is absent or errors, stop before discovery or build. Report that XcodeBuildMCP must be installed and connected, with these setup options for the user to run:

```text
Homebrew:
  brew tap getsentry/xcodebuildmcp && brew install xcodebuildmcp

npx:
  npx -y xcodebuildmcp@latest mcp
```

Then tell the user to add XcodeBuildMCP as a [local MCP server in OpenCode](https://opencode.ai/v2/docs/mcp-servers) and restart OpenCode. Testing does not authorize installing or configuring it for them.

If the user is also setting up RocketClaw in OpenCode V2, tell them to merge `"experimental": { "subagent_depth": 3 }` into `~/.config/opencode/opencode.json`, or use `opencode debug paths` / `opencode debug paths config` to locate and update the existing user-level `opencode.json` or `opencode.jsonc`. Preserve unrelated settings, sibling keys, and any existing integer depth above `3`; do not create a competing config file or let a higher-precedence config lower the effective depth below `3`. Deep delegation needs this setting in consuming projects; installing the plugin or relying on its package-local config is not enough. This is separate from the simulator availability gate.

Also stop with the missing prerequisite when Xcode, its command-line tools, a valid project/workspace, or an iOS simulator is unavailable.

## Discover and launch

Keep run-owned build output, screenshots, logs, and setup-error evidence in a new run directory under the workspace's ignored `.tmp/rocketclaw/xcode/`. Use [`jj workspace root`](https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace-root) from the active workspace's absolute root; outside JJ, use the project's local `.tmp/rocketclaw/xcode/`. Pass absolute output paths to the tools, including on fallback or failure. Do not change the project's ignore rules just to run the test.

1. Discover projects and workspaces, then list schemes for the selected project. An empty argument or `current` selects the default or last-used scheme; a named argument selects that scheme. Ask only when no such scheme can be resolved or project discovery itself remains materially ambiguous.
2. List simulators. Reuse a compatible booted simulator when practical; otherwise prefer an available iPhone 15 Pro and boot it by UUID. Wait until it is ready.
3. Build the simulator app with the selected project/workspace and scheme. Set the build's Derived Data path to a directory within the run directory. On failure, report the relevant build errors and stop; do not install or launch a missing artifact.
4. From the successful build result, retain the app path and bundle identifier. Install the app, launch it, and start simulator log capture for that bundle, writing to a file in the run directory. If the MCP log tool cannot write to a chosen path, use a permitted shell to stream logs via `xcrun simctl spawn <device-uuid> log stream`, filtering to the selected app executable and redirecting output and errors to the run directory. Verify the stream started and retain the capture handle for cleanup.

Any failure before the app is visibly launched with log capture running is a setup blocker: preserve its evidence, report it, and stop later stages.

At handoff, retain the project/workspace, scheme, simulator identity, app identity, and log-capture handle needed by `test-and-report.md`.
