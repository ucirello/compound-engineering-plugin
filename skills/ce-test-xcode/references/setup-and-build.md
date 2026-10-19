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

Resolve the target workspace's absolute root before collecting evidence. In a Jujutsu repository, run `jj workspace root` from that workspace and use the returned root; otherwise use the project's absolute root. Store run-created temporary files, screenshots, exported logs, and fallback/error captures beneath `<workspace-root>/.tmp/`, not OS-global temporary storage. Ensure `.tmp/` is ignored in the repository's `.gitignore` before writing artifacts; preserve existing ignore rules. Configure tool output paths accordingly, and copy tool-managed captures there when the adapter cannot select their original location. Do not relocate Xcode-managed build products or caches merely for this evidence-storage rule.

Run any workspace-scoped JJ command from the workspace's absolute root, for example `(cd "$workspace_root" && jj status)`, rather than relying on `jj -R`. Use Jujutsu for version-control inspection; see the [JJ command reference](https://docs.jj-vcs.dev/latest/cli-reference/). If repository-scoped GitHub CLI inspection is needed, use `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh ...)`. Testing does not authorize creating or removing version-control workspaces.

1. Discover projects and workspaces, then list schemes for the selected project. An empty argument or `current` selects the default or last-used scheme; a named argument selects that scheme. Ask only when no such scheme can be resolved or project discovery itself remains materially ambiguous.
2. List simulators. Reuse a compatible booted simulator when practical; otherwise prefer an available iPhone 15 Pro and boot it by UUID. Wait until it is ready.
3. Build the simulator app with the selected project/workspace and scheme. On failure, report the relevant build errors and stop; do not install or launch a missing artifact.
4. From the successful build result, retain the app path and bundle identifier. Install the app, launch it, and start simulator log capture for that bundle.

Any failure before the app is visibly launched with log capture running is a setup blocker: preserve its evidence, report it, and stop later stages.

At handoff, retain the project/workspace, scheme, simulator identity, app identity, and log-capture handle needed by `test-and-report.md`.
