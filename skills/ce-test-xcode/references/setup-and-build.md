# Setup and build

This reference owns the path from invocation to a launched app with log capture running.

## Availability gate

Confirm that the active OpenCode session exposes XcodeBuildMCP's simulator-listing capability and that the call succeeds. Host-specific MCP tool prefixes are adapters, not the contract.

If the capability is absent or errors, stop before discovery or build. Report that XcodeBuildMCP must be installed and connected, with these setup options for the user to run:

```text
Homebrew:
  brew tap getsentry/xcodebuildmcp && brew install xcodebuildmcp

npx:
  npx -y xcodebuildmcp@latest mcp
```

Then tell the user to add XcodeBuildMCP as an MCP server in OpenCode and restart the session. Testing does not authorize installing or configuring it for them.

Also stop with the missing prerequisite when Xcode, its command-line tools, a valid project/workspace, or an iOS simulator is unavailable.

## Workspace and evidence paths

Use the workspace already assigned to the OpenCode session, including any existing isolation; this test workflow does not create, rename, or remove a repository workspace. In a JJ workspace, resolve the absolute root with `jj workspace root` from the target workspace; run subsequent JJ commands as `(cd "$workspace_root" && jj …)`. Outside JJ, use the absolute local project root instead.

Allocate a run-specific directory under `"$workspace_root/.tmp/"` for temporary artifacts, including simulator screenshots, build and launch diagnostics, and any saved logs. Use absolute paths for tool output options, directing configurable temporary build outputs there as well. Keep fallback and error-path captures there too; do not substitute an OS-global temporary path. Report any evidence the adapter cannot save locally, and count the affected check only on the evidence actually collected.

## Discover and launch

1. Discover projects and workspaces, then list schemes for the selected project. An empty argument or `current` selects the default or last-used scheme; a named argument selects that scheme. Ask only when no such scheme can be resolved or project discovery itself remains materially ambiguous.
2. List simulators. Reuse a compatible booted simulator when practical; otherwise prefer an available iPhone 15 Pro and boot it by UUID. Wait until it is ready.
3. Build the simulator app with the selected project/workspace and scheme. On failure, report the relevant build errors and stop; do not install or launch a missing artifact.
4. From the successful build result, retain the app path and bundle identifier. Install the app, launch it, and start simulator log capture for that bundle.

Any failure before the app is visibly launched with log capture running is a setup blocker: preserve its evidence, report it, and stop later stages.

At handoff, retain the project/workspace, scheme, simulator identity, app identity, and log-capture handle needed by `test-and-report.md`.
