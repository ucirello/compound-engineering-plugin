# Setup and build

This reference owns the path from invocation to a launched app with log capture running.

## Workspace and evidence

Resolve the workspace root with `jj workspace root`. When the current directory is outside a JJ workspace, use that directory as the local workspace root. Inside a JJ workspace, treat `jj status`, `jj diff`, and `jj log` as authoritative for working-copy state, changed surfaces, and relevant history. Jujutsu has working-copy changes and bookmarks, not a staging area or current branch; do not substitute mutating Git commands for JJ operations.

Preserve operational interoperability rather than translating it into repository mutation. Use `gh` for GitHub metadata when the user's scope names a PR or other GitHub object; in a non-colocated Git-backed JJ workspace, point `GIT_DIR` at the path returned by `jj git root`. Read-only Git commands may remain when an operational provider requires them, and Git Bash remains a supported shell.

Create one private run directory under `<workspace-root>/.tmp/rocketclaw/ce-test-xcode/<run-id>/` and retain its absolute path. Store screenshots, captured logs, and other temporary evidence only there; do not use operating-system or global temporary storage. Outside JJ, the same path is rooted at the local workspace directory.

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

1. Discover projects and workspaces, then list schemes for the selected project. An empty argument or `current` selects the default or last-used scheme; a named argument selects that scheme. Ask only when no such scheme can be resolved or project discovery itself remains materially ambiguous.
2. List simulators. Reuse a compatible booted simulator when practical; otherwise prefer an available iPhone 15 Pro and boot it by UUID. Wait until it is ready.
3. Build the simulator app with the selected project/workspace and scheme. On failure, report the relevant build errors and stop; do not install or launch a missing artifact.
4. From the successful build result, retain the app path and bundle identifier. Install the app, launch it, and start simulator log capture for that bundle.

Any failure before the app is visibly launched with log capture running is a setup blocker: preserve its evidence, report it, and stop later stages.

At handoff, retain the project/workspace, scheme, simulator identity, app identity, log-capture handle, and evidence-directory path needed by `test-and-report.md`.
