# Routes, server, and reporting

Read this before mapping changed files to routes (workflow step 3). It carries the route-mapping starting points, the port and server commands, what to check on each page, the two human-facing prompts, and the summary format.

## Map changed files to routes

Map each changed file to the route(s) that render it, then build the list of URLs to test. The table below is a starting point of common patterns, not an exhaustive rule set — apply judgment for the project's actual layout:

| File Pattern | Route(s) |
|-------------|----------|
| `app/views/users/*` | `/users`, `/users/:id`, `/users/new` |
| `app/controllers/settings_controller.rb` | `/settings` |
| `app/javascript/controllers/*_controller.js` | Pages using that Stimulus controller |
| `app/components/*_component.rb` | Pages rendering that component |
| `app/views/layouts/*` | All pages (test homepage at minimum) |
| `app/assets/stylesheets/*` | Visual regression on key pages |
| `app/helpers/*_helper.rb` | Pages using that helper |
| `src/app/*` (Next.js) | Corresponding routes |
| `src/components/*` | Pages using those components |

## Determine the port and verify the dev server is running

`scripts/resolve-port.sh` resolves the port and prints it alone on stdout, so the shell call that needs it captures the value instead of a later step re-typing a printed number. Append the explicit port as an argument when you have one.

```bash
SKILL_DIR="<absolute path of the directory containing the SKILL.md you just read>";
PORT=$(bash "$SKILL_DIR/scripts/resolve-port.sh");
if lsof -i ":${PORT}" -sTCP:LISTEN -t >/dev/null 2>&1; then
  echo "Server running on port ${PORT}";
else
  echo "Server not running on port ${PORT}";
  echo "Start your dev server, then re-run:";
  echo "  Rails: bin/dev  or  rails server -p ${PORT}";
  echo "  Node/Next.js: npm run dev";
  echo "  Custom port: run this skill again with --port <your-port>";
  exit 0;
fi
```

## Test each affected page

For each affected route, use the selected driver to navigate and capture fresh rendered or interactive state.

**Verify key elements:**
- Page title/heading present
- Primary content rendered
- No error messages visible
- Forms have expected fields
- No new console errors attributable to the tested flow

**Test critical interactions:** derive locators or element references from the selected driver's latest inspected state, perform the click/fill/press action, then inspect the resulting state. Do not guess selectors or reuse stale references.

**Take screenshots:** capture viewport and full-page evidence when the selected driver supports it. Materialize transient screenshots only under a collision-resistant run directory in `<workspace-root>/.tmp/ce-test-browser/`, where `<workspace-root>` comes from `jj workspace root` and falls back to the current project directory. Keep them out of the Jujutsu working-copy change. When a later workflow needs durable evidence, copy only that evidence to its owned artifact location; otherwise in-app evidence is sufficient.

## Human verification (when required)

| Flow Type | What to Ask |
|-----------|-------------|
| OAuth | "Please sign in with [provider] and confirm it works" |
| Email | "Check your inbox for the test email and confirm receipt" |
| Payments | "Complete a test purchase in sandbox mode" |
| SMS | "Verify you received the SMS code" |
| External APIs | "Confirm the [service] integration is working" |

Ask the user with the platform's question tool (the list is in SKILL.md step 6), or present numbered options and wait:

```
Human Verification Needed

This test touches [flow type]. Please:
1. [Action to take]
2. [What to verify]

Did it work correctly?
1. Yes - continue testing
2. No - describe the issue
```

## Handle failures

1. **Document the failure:**
   - Capture a screenshot of the error state with the selected driver
   - Note the exact reproduction steps

2. **Ask the user how to proceed:**

   ```
   Test Failed: [route]

   Issue: [description]
   Console errors: [if any]

   How to proceed?
   1. Fix now - debug and fix the failing test
   2. Skip - continue testing other pages
   ```

3. **If "Fix now":** investigate, propose a fix, apply, and re-run the failing test. Keep the fix in the resolved target's Jujutsu scope and do not move or publish another bookmark. If this path composes, edits, validates, or recommends a change description: Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. The mandated sentence's `git log` wording is not an operational instruction; inspect history with `jj log`. Runtime project instructions and `jj log` take precedence. Preserve the tested fix's meaning while adapting syntax dynamically. Apply compatible Go guidance only for quality, clarity, and structure. Do not impose a fixed prefix, type, scope, subject, body, layout, template, or example. Do not add product branding, generated-by text, or creator, model, provider, tool, agent, runtime, workflow, or co-author attribution.
4. **If "Skip":** log as skipped, continue

## Test summary

```markdown
## Browser Test Results

**Test Scope:** PR #[number] / [Jujutsu revision or bookmark]
**Server:** http://localhost:<port>

### Pages Tested: [count]

| Route | Status | Notes |
|-------|--------|-------|
| `/users` | Pass | |
| `/settings` | Pass | |
| `/dashboard` | Fail | Console error: [msg] |
| `/checkout` | Skip | Requires payment credentials |

### Console Errors: [count]
- [List any errors found]

### Human Verifications: [count]
- OAuth flow: Confirmed
- Email delivery: Confirmed

### Failures: [count]
- `/dashboard` - [issue description]

### Result: [PASS / FAIL / PARTIAL]
```
