---
name: ce-test-xcode
description: "Build and test iOS apps on simulator with XcodeBuildMCP."
argument-hint: "[scheme name or 'current' to use default]"
disable-model-invocation: true
---

# Xcode Test Skill

Build, install, and test iOS apps on the simulator using XcodeBuildMCP. Captures screenshots, logs, and verifies app behavior.

## Prerequisites

- Xcode installed with command-line tools
- XcodeBuildMCP MCP server connected
- Valid Xcode project or workspace
- At least one iOS Simulator available

## Workflow

### 0. Verify XcodeBuildMCP is Available

Check that the XcodeBuildMCP MCP server is connected by calling its `list_simulators` method through the harness's available MCP interface. Discover the callable tool when the interface does not expose it immediately; do not depend on a platform-specific generated tool name.

If the tool is not found or errors, inform the user they need to add the XcodeBuildMCP MCP server:

```
XcodeBuildMCP not installed

Install via Homebrew:
  brew tap getsentry/xcodebuildmcp && brew install xcodebuildmcp

Or via npx (no global install needed):
  npx -y xcodebuildmcp@latest mcp

Then add "XcodeBuildMCP" as an MCP server in your agent configuration
and restart your agent.
```

Do NOT proceed until XcodeBuildMCP is confirmed working.

### 1. Discover Project and Scheme

Call XcodeBuildMCP's `discover_projs` tool to find available projects, then `list_schemes` with the project path to get available schemes.

If an argument was provided, use that scheme name. If "current", use the default/last-used scheme.

### 2. Boot Simulator

Call `list_simulators` to find available simulators. Boot the preferred simulator (iPhone 15 Pro recommended) using `boot_simulator` with the simulator's UUID.

Wait for the simulator to be ready before proceeding.

### 3. Build the App

Call `build_ios_sim_app` with the project path and scheme name.

**On failure:**
- Capture build errors
- Report to user with specific error details

**On success:**
- Note the built app path for installation
- Proceed to step 4

### 4. Install and Launch

1. Call `install_app_on_simulator` with the built app path and simulator UUID
2. Call `launch_app_on_simulator` with the bundle ID and simulator UUID
3. Call `capture_sim_logs` with the simulator UUID and bundle ID to start log capture

### 5. Test Key Screens

Resolve `<workspace-root>` with `jj workspace root`. If the project is not in a JJ workspace, derive the root from the Xcode project or workspace selected in step 1 rather than assuming the current directory is the root. Create a collision-resistant run directory under `<workspace-root>/.tmp/ce-test-xcode/` and keep all transient screenshots and exported copies of captured logs there. Never place transient artifacts outside `<workspace-root>/.tmp/`.

For each key screen in the app:

**Take screenshot:**
Call `take_screenshot` with the simulator UUID and a descriptive path in the run directory (e.g., `<run-dir>/screen-home.png`).

**Review screenshot for:**
- UI elements rendered correctly
- No error messages visible
- Expected content displayed
- Layout looks correct

**Check logs for errors:**
Call `get_sim_logs` with the simulator UUID. Look for:
- Crashes
- Exceptions
- Error-level log messages
- Failed network requests

**Known automation limitation — SwiftUI Text links:**
Simulated taps (via XcodeBuildMCP or any simulator automation tool) do not trigger gesture recognizers on SwiftUI `Text` views with inline `AttributedString` links. Taps report success but have no effect. This is a platform limitation — inline links are not exposed as separate elements in the accessibility tree. When a tap on a Text link has no visible effect, prompt the user to tap manually in the simulator. If the target URL is known, `xcrun simctl openurl <device> <URL>` can open it directly as a fallback.

### 6. Human Verification (When Required)

Pause for human input when testing touches flows that require device interaction.

| Flow Type | What to Ask |
|-----------|-------------|
| Sign in with Apple | "Please complete Sign in with Apple on the simulator" |
| Push notifications | "Send a test push and confirm it appears" |
| In-app purchases | "Complete a sandbox purchase" |
| Camera/Photos | "Grant permissions and verify camera works" |
| Location | "Allow location access and verify map updates" |
| SwiftUI Text links | "Please tap on [element description] manually — automated taps cannot trigger inline text links" |

Ask with the harness's blocking question capability. If it is not immediately available, use the harness's tool-discovery capability before falling back. Present numbered options in chat only when no blocking question capability exists or the call errors; never silently skip the question:

```
Human Verification Needed

This test requires [flow type]. Please:
1. [Action to take on simulator]
2. [What to verify]

Did it work correctly?
1. Yes - continue testing
2. No - describe the issue
```

### 7. Handle Failures

When a test fails:

1. **Document the failure:**
   - Take screenshot of error state
   - Capture console logs
   - Note reproduction steps

2. **Ask the user how to proceed:**

   ```
   Test Failed: [screen/feature]

   Issue: [description]
   Logs: [relevant error messages]

   How to proceed?
   1. Fix now - debug, propose a fix, rebuild and retest
   2. Skip - continue testing other screens
   ```

3. **If "Fix now":** inspect `jj status`, `jj diff`, and current `jj log` before editing. Preserve unrelated working-copy changes, use JJ for local version-control inspection and mutation, investigate the failure, apply only the requested fix, then rebuild and retest. Do not add creator, model, provider, tool, runtime, product, or generated-by attribution.
4. **If "Skip":** log as skipped, continue

### 8. Test Summary

After all tests complete, present a summary:

```markdown
## Xcode Test Results

**Project:** [project name]
**Scheme:** [scheme name]
**Simulator:** [simulator name]

### Build: Success / Failed

### Screens Tested: [count]

| Screen | Status | Notes |
|--------|--------|-------|
| Launch | Pass | |
| Home | Pass | |
| Settings | Fail | Crash on tap |
| Profile | Skip | Requires login |

### Console Errors: [count]
- [List any errors found]

### Human Verifications: [count]
- Sign in with Apple: Confirmed
- Push notifications: Confirmed

### Failures: [count]
- Settings screen - crash on navigation

### Result: [PASS / FAIL / PARTIAL]
```

### 9. Cleanup

After testing:

1. Call `stop_log_capture` with the simulator UUID
2. Optionally call `shutdown_simulator` with the simulator UUID

## Quick Usage Examples

When presenting a user-runnable invocation, render `ce-test-xcode` in the active harness's local callable-skill syntax rather than hard-coding a platform prefix. Show exactly one locally valid form:

| Intent | Argument |
|--------|----------|
| Test with the default scheme | none |
| Test a specific scheme | `MyApp-Debug` |
| Test after making changes | `current` |

## Integration with `ce-code-review`

When reviewing a change or revision that touches iOS code, `ce-code-review` can invoke this skill through the active harness's callable skill mechanism to build on the simulator, test key screens, and check for crashes.
