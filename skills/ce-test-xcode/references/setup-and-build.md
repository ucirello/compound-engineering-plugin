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

Also stop with the missing prerequisite when Xcode, its command-line tools, a valid project/workspace, or an iOS simulator is unavailable.

## Discover and launch

After project discovery, resolve the selected project's absolute workspace root before running project-scoped commands; use that root as the actual working directory. In a JJ workspace, obtain it with `jj workspace root`. Store run-created temporary screenshots, log exports, and other evidence under `<absolute-workspace-root>/.tmp/`, including fallback and error paths, rather than OS-global temporary storage. Outside a JJ repository, use the selected project's local `.tmp/`. Ensure `.tmp/` is ignored; preserve evidence through handoff rather than deleting it during simulator cleanup. Do not relocate Xcode-managed build artifacts or simulator state.

1. Discover projects and workspaces, then list schemes for the selected project. An empty argument or `current` selects the default or last-used scheme; a named argument selects that scheme. Ask only when no such scheme can be resolved or project discovery itself remains materially ambiguous.
2. List simulators. Reuse a compatible booted simulator when practical; otherwise prefer an available iPhone 15 Pro and boot it by UUID. Wait until it is ready.
3. Build the simulator app with the selected project/workspace and scheme. On failure, report the relevant build errors and stop; do not install or launch a missing artifact.
4. From the successful build result, retain the app path and bundle identifier. Install the app, launch it, and start simulator log capture for that bundle.

Any failure before the app is visibly launched with log capture running is a setup blocker: preserve its evidence, report it, and stop later stages.

At handoff, retain the project/workspace, scheme, simulator identity, app identity, and log-capture handle needed by `test-and-report.md`.
