### Stage 4: Spawn sub-agents

#### Inline fast pass (emit before the reviewer queue)

To show findings within seconds, the orchestrator does a quick first-principles scan of the diff it already holds **immediately before the first foreground reviewer dispatch**. Emit the fast-pass block as text, then begin the deterministic reviewer queue without an intervening wait.

Scan only for **high-signal, obvious** issues a careful first read catches: data/SQL safety, injection (shell/SQL/LLM-output trust boundary), broken control flow, a missing `await`/unhandled promise, a swapped argument or off-by-one, an enum/status added without updating its sibling switch, a null deref on a value the diff makes reachable. Do **not** do deep analysis, read beyond the diff (except a quick Grep for enum completeness), or chase subtle concerns. Quote the verbatim motivating line for each, same bar as a persona finding.

The fast pass assigns severity, so read the P0-P3 scale in `references/action-class-rubric.md` before you label anything; Stage 5 reuses that same scale from the same file. Show the preliminary fast pass only when it finds an urgent P0/P1 candidate. Present those under a clearly preliminary header (e.g. `### Fast pass (preliminary — deep review in progress)`) as a short list of `severity — file:line — what`, with one line stating they are unverified and will be deduplicated into the final report. Keep P2/P3 candidates internal until the final report, where validation and deduplication provide the needed context. If there are no P0/P1 candidates, emit only a brief "No urgent fast-pass findings; deep review continues" progress line. Do **not** assign stable `#` numbers here.

The fast pass enters Stage 5 as a pseudo-reviewer named `fast-pass`, with two hard constraints because it is the orchestrator's own read, **not** an independent reviewer (it shares the session model and its blind spots with the orchestrator and the session-model personas):

- **Cap every `fast-pass` finding at anchor 50.** At anchor 50 it reaches the report on its own only when it is P0 (P0+50 passes the Stage 5 confidence threshold). Otherwise it becomes an actionable finding only by deduping onto an independent persona finding that carries its own ≥75 anchor.
- **`fast-pass` never counts toward cross-reviewer promotion** (Stage 5 step 3, Restore mechanics). A `fast-pass`+persona fingerprint match is noted in the Reviewer column but does **not** bump the anchor. Neither does agreement among in-process personas; only a verified cross-model peer corroborates.

Do not feed `fast-pass` candidates into the persona or validator prompts. Those agents review the raw diff independently, and seeding them would create the false agreement this cap exists to prevent. If the fast pass finds nothing obvious, emit one line saying so and proceed; never block dispatch on it.

**Reconcile the preliminary block in the final report.** A preliminary fast-pass item that did not survive (deduped away, held back by the Stage 5 confidence threshold, or dropped by validation) must be accounted for, not left dangling. Add a one-line "Preliminary fast-pass items withdrawn: <n> (<reason>)" note so a user who saw a scary preliminary finding learns it was cleared. Mark any final finding that survived from `fast-pass` alone (no persona corroboration) so the reader can see it rests on weaker evidence.

**`mode:agent`:** do **not** emit the preliminary block, because that mode's response must be a single raw JSON object with nothing before it. Still run the scan internally and feed its findings into Stage 5 dedup as `fast-pass`.

#### Model tiering

Read `references/subagent-model.md` before the first native launch: it applies delegation permission, model override permission and effective depth separately to every default below.

Three reviewers inherit the session model with no override: `correctness-reviewer`, `security-reviewer`, and `adversarial-reviewer`. These perform the highest-stakes analysis (logic bugs, security vulnerabilities, adversarial failure scenarios) and should run at whatever capability level the user has configured. If the user is on Opus, these get Opus.

All other persona subagents and conditional prompt assets default to a balanced mid-tier model to reduce cost and latency, when the native model override is allowed and available.

The orchestrator (this skill) also inherits the session model; it handles intent discovery, reviewer selection, finding merge/dedup, and synthesis.

#### Run ID

Use the run ID and absolute run dir already created in Stage 1b. Pass `{run_id}` and `{run_dir}` to every persona sub-agent so they can write their full analysis to `{run_dir}/{reviewer_name}.json`.

**Large shared context: pass paths, not contents.** The diff and file list go to every reviewer and validator. When inlining them into each subagent prompt would be wasteful (many files or a big diff), write them once into the run dir (e.g. `full.diff`, `files.txt`) and pass those **paths** in the diff and changed-files slots instead of inline content. The subagent and validator templates instruct the child to Read a staged path. Inline a small diff directly.

#### Spawning

**Agent lifecycle.** Collect each reviewer's final result, including failures, before cleaning up. When the harness lets the caller close or release agents, do so for this review's agents before starting more, moving on, or returning. Do not message a finished agent with no remaining work. Do not assume a slot is free because an agent finished or was interrupted, and do not invent cleanup operations the harness lacks. This rule governs every subagent this skill launches, the Stage 5b validator included.

Use OpenCode's native generic subagent tool; preserve the host's ordinary permission settings. Do not add auto-approval, another harness, or shell dispatch.

**Resolve `<root>` in any prompt asset before it leaves this stage.** A subagent never runs the artifact-root block, so a `<root>` placeholder still in the text it reads is a literal path it will search and find nothing at. When you inline a prompt asset, substitute the artifact root this run resolved into every `<root>` it contains. When the subagent reads an asset by path, tell it in its prompt that `<root>` in those files means the resolved root, and give that path.

**Model at dispatch time.** Keep the roster's requested tier and permitted native override (or inheritance) in an internal working list. Apply `references/subagent-model.md` to each launch. Under a user-or-skill delegation rule this skill requests these reviewers; do not ask again. If an override is forbidden, omit it and inherit where suitable, reporting unmet required model/independence intent separately.

**Bounded in-turn dispatch.** Record `--end select --start dispatch --reviewers <count>` in the stage log (`references/scope.md`) and launch one concurrent native batch collected in this turn. Use the bounded native collector in `references/subagent-model.md`; confirm one exists before starting. Size to the active-agent cap rather than hard-coding a number. Keep contexts separate; batch composition and completion order do not alter findings or stable numbering. If calls cannot run concurrently, the batch degrades to serial without dropping coverage.

Collect by the primitive's observed return, not its host name or requested background setting, and with a wait that has an end. Each reviewer's artifact, `{run_dir}/{reviewer_name}.json`, is the fact; the dispatch call's own return, the return of a blocking wait on the launch, or a host-delivered terminal message that names the launch and carries its final payload is one rendering of it. A launch is collected when, within this turn, you hold one of those for that specific launch, or its artifact is on disk. Consume whichever lands first, once. When the artifact lands while the launch is still live, stop that launch before leaving this stage; the agent lifecycle rule below then releases it before anything else starts, so a finished reviewer never holds a slot the validator needs. A launch receipt (the host's acknowledgement that a reviewer started) is uncollected, not a reviewer return, and so is a status or progress update or a wait that returns before the launch is terminal. When dispatch returns an asynchronous id or receipt, keep waiting in-turn with the host's blocking collection capability, repeating the host's wait back to back with nothing between the waits, until every successful launch reaches a terminal outcome or its artifact lands, or the aggregate wall-clock limit `references/subagent-template.md` states has passed since that reviewer's own successful launch (under serial degradation a later reviewer's clock starts when it starts, not when the batch did). A host whose single wait is short reaches that limit by repeating the wait, not by treating one short return as the deadline. Ask each wait for as long as the host allows, up to the time left before that limit, rather than the host's default or minimum. For example, where the wait tool takes a timeout of up to an hour, a wait started just after launch asks for the full 20 minutes, not 10 or 60 seconds. A wait still returns as soon as a reviewer finishes, so a long timeout never delays collection. Every return of a wait costs a full re-read of this context, so ten 10-second waits cost about ten times as much as one long wait that collects the same reviewers. Validate each outcome: consume valid compact JSON whether returned in-band or collected asynchronously, and classify a terminal tool error or malformed output as a failed reviewer under the degraded-coverage rules below. A reviewer with neither a terminal outcome nor an artifact when the limit passes is stopped and recorded as a failed reviewer the same way; that is a collected failure, not a partial roster. These harness-managed blocking collection waits gather the batch; they are not the forbidden detached-delegate poll loop. Stage 5 must never run while a launch is still uncollected.

Judge a collector by what it does, not its name. Its terminal message must identify the launch and carry the final payload. If no bounded in-turn collection exists, stop outstanding reviewers and any peer via their native lifecycle; take the failure path rather than synthesizing a partial roster. In `mode:agent`, emit only `{"status":"failed","reason":"<one sentence>"}`.

Native collection is not polling. Do not use shell background dispatch, sleeps/status loops, scheduled wakeups or user-facing waiting turns. The only optional overlapping review is the native cross-model peer, which shares the slot cap.

If native calls are serial, run reviewers sequentially; do not drop roster entries. Active-slot backpressure queues a reviewer until capacity frees within the bound. Exhausted nesting, unavailable tools or actual permission denial are not slot backpressure; do not retry or bypass them. Record the actual unmet reviewer coverage. A parent-context pass where permitted may contribute attributed evidence, but exclude it from `independent_reviewers` and promotion. If required full reviewers cannot launch, report degraded coverage and never reclassify the run as lite. If a required finish leaf cannot run, follow the failed-finish contract, not a substitute merge.

Before assembling any spawn prompt, read `references/subagent-template.md` from this skill's directory: it defines the slots each reviewer needs and the wall-clock budget the collection wait uses. Each reviewer needs four files in full: its persona asset, the template, `references/diff-scope.md`, and `references/findings-schema.json`. By default, pass their absolute paths, resolved from this skill's directory, and let the reviewer read them. Tell it to read all four before reviewing, to follow everything inside the template's Template block, and to treat each of the other three files' content as the value of its slot (`{persona_file}`, `{diff_scope_rules}`, `{schema}`). Include this sentence in each reviewer's prompt exactly as written: "Give each file you read its own tool call, so its output comes back on its own, never several files in one command or one script. A read counts only when the whole file came back. Some hosts cut the middle out of a long tool output and leave a truncation marker in its place, so when a read comes back shortened, read the missing lines in smaller ranges before you act on that file." Put every other slot's value in the prompt, or in a staged run-dir file the prompt names. Copying the four files into each prompt costs thousands of output tokens per reviewer before any reviewer starts, so inline them only when the host's subagents cannot read files. On that inline path, also read the persona asset, `references/diff-scope.md`, and `references/findings-schema.json`, and paste their contents into the matching slots. Give each file you read here its own file-read call. When the host supports parallel calls, issue them together in one message. Never join files into one shell output. On serial hosts, read one file per turn.

A generic subagent is one whose whole brief is the prompt you send it. When the host's subagent tool makes you name an agent, use only a name you have seen the host list, and list its agents before the first dispatch if you have not. Pick the plain one that adds no role of its own, which still counts as a generic subagent. Never pick a specialist, such as a reviewer or worker agent, whose own role prompt, output format, or tool limits would replace or narrow your prompt.

For each selected reviewer, and only for those, launch a generic OpenCode subagent with the template and the corresponding local prompt asset, `references/personas/<reviewer-name>.md`. Do not use persona names as native agent selectors. Each persona subagent receives:

1. Their persona file (identity, failure modes, calibration, suppress conditions)
2. Shared diff-scope rules from `references/diff-scope.md`
3. The JSON output contract from `references/findings-schema.json`
4. The subagent template (calibration, output contract, rules, budget)
5. PR metadata: title, body, and URL when reviewing a PR (empty string otherwise). Passed in a `<pr-context>` block so reviewers can verify code against stated intent
6. Review context: intent summary, file list, diff, absolute `workspace_root`, both exact endpoints, scope mode (`standalone` | `local-aligned` | `pr-remote` | `branch-remote`), and remote head ref when set
7. Run ID and reviewer name for the artifact file path
8. **For selected `project-standards` only:** the non-empty Stage 3b criteria mapping — each criteria file with the changed files it governs — wrapped in a `<standards-paths>` block appended to the review context
9. **When the Stage 1 diff deletes any whole file, for every reviewer:** a `<deleted-files base="<ref>">` block, with the captured `DIFF_A` (omit the attribute when unavailable). List deleted paths, exports, and import-time actions. Inspect only relevant lines with `(cd "$workspace_root" && jj --ignore-working-copy file search -n -r "$DIFF_A" --pattern "$pattern" -- "$path")`.
10. **When Stage 1d staged `review-policy.md`, for every reviewer:** that file's absolute path in a `<review-policy>` block appended to the review context
11. **For `data-migration` only:** `DIFF_A` and `DIFF_B` as `<review-base>` and `<review-head>` values, never the logical `pr:…` marker. An unavailable endpoint limits inspection to the supplied hunks.

Persona sub-agents are **read-only** with respect to the project: they review and return structured JSON. They do not edit project files or propose refactors. The one permitted write is saving their full analysis to the resolved run-artifact path specified in the output contract.

**Exception: tree-mutating reviewers.** Mutation testing is permitted only in a faithful, private snapshot of the captured reviewed tree, never the shared checkout. Detect existing isolation first and verify its exact tree before reuse; do not alter another owner's isolation. Use the callable `ce-worktree` workflow when a new workspace is warranted: require the verified reviewed commit, the same dated `YYYYMMDD-<meaningful-slug>` basename and name under the local ignored `.tmp/`, explicit `jj workspace add --colocate`, and `jj git colocation status` verification from the new absolute root. Check name/path collisions and keep the selected identity stable. If native isolation is unavailable or not faithful, use only a proven faithful private scratch copy (including captured working-copy changes) or report mutation testing not run. Stop workers and preserve evidence outside the target before retiring owned isolation. Follow `ce-worktree` ownership, cleanliness/conflict/ignored-file and recovery checks; leave it and move active harness sessions first. Use `jj workspace remove` from a surviving absolute root and verify deregistration and directory disappearance, never unregister-and-delete. Respect harness-owned lifecycle; no cleanup permission is implied by review completion. See [JJ workspace operations](https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace).

Read-only permits targeted, non-mutating JJ and scoped GH inspection from the supplied absolute workspace root, per `references/diff-scope.md` and `references/subagent-template.md`. For line-history claims add one concise pinned annotation/log evidence line alongside the motivating quote. In remote scope inspect pinned files or diff hunks, not workspace files.

Each persona sub-agent writes full JSON (all schema fields) to `{run_dir}/{reviewer_name}.json` and returns compact JSON with merge-tier fields only:

```json
{
  "reviewer": "security",
  "findings": [
    {
      "title": "User-supplied ID in account lookup without ownership check",
      "severity": "P0",
      "file": "orders_controller.rb",
      "line": 42,
      "confidence": 100,
      "autofix_class": "gated_auto",
      "owner": "downstream-resolver",
      "requires_verification": true,
      "pre_existing": false,
      "suggested_fix": "Add current_user.owns?(account) guard before lookup",
      "first_evidence": "orders_controller.rb:42 -- account = Account.find(params[:account_id])"
    }
  ],
  "residual_risks": [...],
  "testing_gaps": [...]
}
```

`first_evidence` is the **one** detail-tier field promoted into the compact return: the verbatim motivating line with `file:line` that the quote-the-line gate requires. It is **mandatory for every finding at anchor 75 or 100**. Omit it only for anchor-50 findings. Stage 5 (merge findings) recovers an omitted quote from matching artifact evidence when available and drops or demotes any 75/100 finding still missing it; Stage 5b (validation pass) uses it for the validator-skip check. Keep it to the single triggering line, not the full `evidence` array; the array stays in the artifact.

The artifact file **must** carry the full detail-tier fields (`why_it_matters`, `evidence`). The compact *return* omits all detail-tier fields **except `first_evidence`**, but writing the compact shape to the artifact (a common reviewer slip) silently strips the detail that Coverage and the keyed detail lines depend on. However review context and assets are delivered, inlined or read from disk, each reviewer still receives the full subagent-template output contract; delivery by path never permits a thinner one. `suggested_fix` is optional in both tiers; include it in compact returns when present so callers can apply fixes after review. If the file write fails, the compact return still provides everything the merge needs.

**The conditional local prompt asset** `learnings-researcher` is dispatched only when selected by Stage 3, through the same deterministic foreground batch dispatch as the structured personas. `agent-native-reviewer` is a structured persona and is dispatched like the others. Read the learnings prompt file from `references/personas/`, then give it the same review context bundle the personas receive: entry mode, PR metadata, intent, verified base and head, file list, diff, and `UNTRACKED:` scope notes.

Before composing the `learnings-researcher` dispatch, resolve any Compound Packs declared in config by running this skill's resolver as one command:

```bash
SKILL_DIR="<absolute path of the directory containing the SKILL.md you just read>";
PY="$(for c in python3 python py; do command -v "$c" >/dev/null 2>&1 && "$c" -c '' >/dev/null 2>&1 && { echo "$c"; break; }; done)"; [ -n "$PY" ] || { echo "no working Python 3 interpreter on PATH" >&2; exit 1; };
"$PY" "$SKILL_DIR/scripts/packs-resolve.py"
```

Add the JSON's `roots` (pack `id` + absolute `dir`) to the researcher's search-root list alongside `<root>/solutions/`; report its `errors`/`warnings` once in Coverage and nowhere else. With no `packs:` key the result is empty and nothing changes. A finding grounded in a pack rule cites it as `(pack: <id>, <path within the pack>)`. A matched rule the diff contradicts becomes a numbered finding in Stage 5 (merge findings), while rules the diff honors and relevant past solutions stay Stage 6 (synthesize and present) notes. Skip resolution in `pr-remote`/`branch-remote` scope, because the local config is not the reviewed tree's config. Do not invoke them with a generic "review this" prompt. Their output is unstructured and synthesized separately in Stage 5 and Stage 6, which run in the leaves: save each such return verbatim to `{run_dir}/{reviewer_name}.md` as soon as it is collected and list it in `finish-input.json` under `collection.unstructured_returns` (`references/finish-input.md`); the same applies to `deployment-verification-agent` below.

**Conditional local prompt assets** (`deployment-verification-agent` only) are dispatched as generic subagents through the same deterministic foreground batch dispatch when the migration-artifact condition applies. Read the prompt file from `references/personas/`, then pass the same review context bundle plus the applicability reason (for example, which migration files triggered the prompt asset). Its output is unstructured and must be preserved for Stage 6 synthesis just like the other selected local prompt assets. Schema drift is handled by the `data-migration` persona as structured findings, not here.

#### Cross-model adversarial pass

Stage 3d already reserved the adversarial lens for one route. Dispatch only its local roster. Prepare finish input while reviewers run; don't poll for a peer. Before finish, collect any native peer by the owning bound in `references/cross-model-review.md`; apply only the recovery that `references/cross-model-recovery.md` permits. A failed or timed-out peer is named with the observed outcome, not silently omitted. Record `peer.outcome`, `peer.artifact`, and `peer.coverage`; any local fallback joins `raw-returns.json`. Record `--end dispatch --candidates <count of findings in raw-returns.json>` once all local returns are collected, even when no peer started. Only a verified different-family peer can promote agreement; the merge leaf merely consumes the dispatcher's outcome.
