# Routes, server, and reporting

Read this before determining test scope (workflow step 2). It carries the scope commands, route-mapping starting points, port and server commands, what to check on each page, human-facing prompts, and summary format.

## Determine the changed files

Set `workspace_root` to the absolute root reported by `jj workspace root` in the target workspace. Run the following scope commands from that root so file paths are workspace-relative. See the [JJ command table](https://docs.jj-vcs.dev/latest/git-command-table/) and [revset reference](https://docs.jj-vcs.dev/latest/revsets/).

- **PR number:** use the PR's own changed-file list. Set `pr_number` to the requested number.

  ```bash
  (
    cd "$workspace_root" || exit 1
    GIT_DIR=$(jj git root) || exit 1
    export GIT_DIR
    gh pr view "$pr_number" --json files -q '.files[].path'
  )
  ```

- **`current`, no argument, or a named branch:** use `@` for the current change, or resolve the exact named JJ bookmark for a named branch (qualify the remote if needed). An empty `@` can still sit above changes to test. Use the project's intended base bookmark, or the repository's verified `trunk()` if no base is specified. Resolve the base and head to single full commit IDs (`base` and `head`) using `jj log --no-graph -r '<revset>' -T 'commit_id ++ "\n"'`; do not substitute another ref if either fails to resolve. Find the common ancestor and compare its tree to the head:

  ```bash
  (cd "$workspace_root" && jj log --no-graph -r "heads(::$base & ::$head)" -T 'commit_id ++ "\n"')
  ```

  Verify that this returned exactly one real merge-base commit and set `merge_base` to its full ID.

  ```bash
  (cd "$workspace_root" && jj diff --from "$merge_base" --to "$head" --summary)
  ```

  Use the file paths from the summary for route mapping. Account for deleted files and both paths of renames rather than treating a compact rename display as one path.

Report an unresolved scope (including a missing or ambiguous base/head or a failed PR lookup) as a preflight blocker with what would clear it. Don't treat lookup failures as an empty changed-file list or change the workspace/bookmarks to make the lookup succeed.

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

**Take screenshots:** capture viewport and full-page evidence when the selected driver supports it. Materialize screenshots under the target workspace's ignored `.tmp/rocketclaw/ce-test-browser/` when a later workflow or report needs file paths; otherwise in-app evidence is sufficient.

## Human verification (when required)

| Flow Type | What to Ask |
|-----------|-------------|
| OAuth | "Please sign in with [provider] and confirm it works" |
| Email | "Check your inbox for the test email and confirm receipt" |
| Payments | "Complete a test purchase in sandbox mode" |
| SMS | "Verify you received the SMS code" |
| External APIs | "Confirm the [service] integration is working" |

In manual mode, ask with the OpenCode question capability following SKILL.md step 6, or present numbered options and wait when that fallback applies:

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

3. **If "Fix now":** investigate, propose a fix, apply, re-run the failing test
4. **If "Skip":** log as skipped, continue

## Test summary

```markdown
## Browser Test Results

**Test Scope:** PR #[number] / [bookmark name] / [current change]
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
