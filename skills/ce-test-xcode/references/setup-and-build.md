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

Resolve the selected project's absolute workspace root as `workspace_root` before discovery. Run project-scoped tools and shell commands from that root, not from a parent checkout or an evidence directory. In a JJ workspace, obtain the root with `jj workspace root` from the selected workspace, then run any subsequent JJ command as `(cd "$workspace_root" && jj ...)`; keep returned file paths repository-relative. Native JJ command guidance: https://docs.jj-vcs.dev/latest/cli-reference/ . This testing workflow does not create or retire source workspaces.

Keep temporary files, build scratch storage, screenshots, and captured logs under the selected workspace's local `.tmp/` (for example, `.tmp/xcode-test/<run-name>/`). Create a unique run-owned directory without overwriting existing evidence, and direct adapters' output paths there when supported. Do not use OS-global `/tmp`, `TMPDIR`, or bare `mktemp` fallbacks; outside a JJ repository, use the selected project's local `.tmp/` as well. Preserve required evidence through handoff.

1. Discover projects and workspaces, then list schemes for the selected project. An empty argument or `current` selects the default or last-used scheme; a named argument selects that scheme. Ask only when no such scheme can be resolved or project discovery itself remains materially ambiguous.
2. List simulators. Reuse a compatible booted simulator when practical; otherwise prefer an available iPhone 15 Pro and boot it by UUID. Wait until it is ready.
3. Build the simulator app with the selected project/workspace and scheme. On failure, report the relevant build errors and stop; do not install or launch a missing artifact.
4. From the successful build result, retain the app path and bundle identifier. Install the app, launch it, and start simulator log capture for that bundle.

Any failure before the app is visibly launched with log capture running is a setup blocker: preserve its evidence, report it, and stop later stages.

At handoff, retain the absolute workspace root, run-owned evidence directory, project/workspace, scheme, simulator identity, app identity, and log-capture handle needed by `test-and-report.md`.
