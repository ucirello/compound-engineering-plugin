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

For OpenCode setup, the user must also merge `experimental.subagent_depth` as an integer of at least `3` into the existing global `~/.config/opencode/opencode.json`. If the global location differs, discover it with `opencode debug paths` / `opencode debug paths config` and use the existing `opencode.json` or `opencode.jsonc` there. Preserve unrelated settings, sibling experimental settings, and any higher depth; do not create a competing JSON/JSONC document. Package/plugin configuration alone does not enable consumer delegation, and higher-precedence configuration must not lower this depth. This is setup guidance only, not permission to modify global files.

Also stop with the missing prerequisite when Xcode, its command-line tools, a valid project/workspace, or an iOS simulator is unavailable.

## Discover and launch

Resolve the target workspace's absolute root before collecting evidence. In a JJ workspace, run `jj root` with the working directory set to the target workspace's absolute directory, then use that returned absolute root for any subsequent JJ commands. Otherwise use the project's absolute root. Store run-owned screenshots, exported logs, and other temporary evidence in a distinct directory beneath that root's `.tmp/`; do not use OS temporary directories, `TMPDIR`, or a global temporary fallback. Configure available tool output destinations accordingly. If a tool cannot honor an output destination, disclose that limitation rather than silently claiming workspace-local storage.

1. Discover projects and workspaces, then list schemes for the selected project. An empty argument or `current` selects the default or last-used scheme; a named argument selects that scheme. Ask only when no such scheme can be resolved or project discovery itself remains materially ambiguous.
2. List simulators. Reuse a compatible booted simulator when practical; otherwise prefer an available iPhone 15 Pro and boot it by UUID. Wait until it is ready.
3. Build the simulator app with the selected project/workspace and scheme. On failure, report the relevant build errors and stop; do not install or launch a missing artifact.
4. From the successful build result, retain the app path and bundle identifier. Install the app, launch it, and start simulator log capture for that bundle.

Any failure before the app is visibly launched with log capture running is a setup blocker: preserve its evidence, report it, and stop later stages.

At handoff, retain the project/workspace, scheme, simulator identity, app identity, and log-capture handle needed by `test-and-report.md`.
