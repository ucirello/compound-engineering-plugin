---
name: ce-test-browser
description: Run browser tests for pages affected by the current change or a Jujutsu revision. Use when asked to run or check browser tests for the current change.
argument-hint: "[revision, bookmark, 'current', or --port PORT]"
---

# Browser Test Skill

Run end-to-end browser tests on pages affected by a Jujutsu change or revision using the best approved browser driver available in the active harness.

**Done:** the run ends by reporting what it found — either the summary, with every affected route marked Pass, Fail, or Skip and each Skip carrying its reason, or, when a preflight blocker stops testing before any route can be exercised, the blocker and what would clear it. Reaching neither, or dropping a route from the summary because nobody could reach it, is the failure this bar exists to prevent.

## Modes

- **Manual (default):** the user controls the dev server. When the fallback driver is `agent-browser`, ask whether to run headed or headless.
- **Pipeline (`mode:pipeline`):** invoked by LFG or another automated runner. The run is unattended — never block on a question. Read `references/pipeline-orchestration.md` from this skill's directory and follow it; it overrides port selection (step 4), dev-server startup (step 5), and visibility prompts (step 6), running the same port script with `--free` inside the block that starts the server.

## Browser Driver Policy

Select the driver before the first browser action:

1. **Prefer a host-native integrated browser.** Use a browser-control surface embedded in or directly owned by the active harness when it can navigate local URLs, inspect rendered and interactive state, click/fill/press, capture screenshots, and inspect console errors. A separately configured browser extension or integration is not host-native. Load and follow the selected capability's own instructions before browser work.
2. **Otherwise fall back to `agent-browser`.** Read `references/agent-browser-driver.md` before running any command.
3. **Do not introduce a third browser stack.** Never install or substitute standalone Playwright, Puppeteer, a separately configured browser extension or MCP, or other ad hoc browser automation. A Playwright API exposed inside the selected host-native browser remains host-native; it is not standalone Playwright.

Use one driver for the entire run. A selected host-native driver may fall back to `agent-browser` only if initialization fails before the first route is tested. After testing begins, do not mix driver sessions, element references, screenshots, or authentication state.

## Workflow

Read `references/route-and-report.md` from this skill's directory before step 3 — it carries the route-mapping patterns, the port and server commands, the per-page checks, the two human-facing prompts, and the summary format.

1. **Select the driver** per the policy above and record it. This also requires a Jujutsu workspace with changes to test.
2. **Determine test scope** from the argument. Use `@` when the argument is `current` or empty; otherwise use the supplied revision or bookmark. Use the project's configured trunk revision as the base, falling back to `trunk()`, then list changed files with `jj diff --from '<base-revision>' --to '<target-revision>' --name-only`.
3. **Map changed files to routes** and build the list of URLs to test.
4. **Determine the dev server port.** `scripts/resolve-port.sh` owns the resolution and prints the port alone on stdout: an explicit port argument; else a `--port` flag in a `package.json` dev/start script; else `PORT=` in `.env`, `.env.local`, or `.env.development`; else `3000`. Pass an explicit port when the user gave `--port N`, or when your active project instructions already in context state the dev-server port. Do not grep instruction files for one. Each mode runs the script in the shell call that needs the port. Manual mode uses that port as-is.
5. **Verify the dev server is running** before asking the headed/headless question. A manual run with no server stops here.
6. **Set visibility, then verify the root.** A host-native integrated browser keeps its normal integrated surface visible and non-blocking in both modes. The `agent-browser` fallback runs headless without asking in pipeline mode; in manual mode, ask with the platform's blocking question tool and fall back to numbered options on the host's user-visible chat surface only when no blocking tool exists or the call errors. Never silently skip the question. Then navigate to `http://localhost:<port>`, inspect fresh state, and confirm the root is served.
7. **Test each affected page** — navigate, inspect fresh state, exercise the critical interactions, capture evidence.
8. **Human verification** where a flow needs external interaction: pause and ask. Pipeline mode does not pause; log each such flow as Skip with the reason and continue.
9. **Handle failures** by capturing the error state and exact repro, then asking whether to fix now or continue. Pipeline mode does not ask; log the failure and continue.
10. **Report the summary** in the format the reference gives.

## Driver Reference

When `agent-browser` is selected as the fallback, read `references/agent-browser-driver.md` from this skill's directory before running its commands. Host-native drivers follow their harness-provided instructions instead.
