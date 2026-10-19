### Stage 4: Spawn sub-agents

Read `references/dispatch-capabilities.md` before dispatch; its permission, model, depth, fallback, and coverage contract applies to every launch below.

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

Three reviewers inherit the session model with no override: `correctness-reviewer`, `security-reviewer`, and `adversarial-reviewer`. These perform the highest-stakes analysis (logic bugs, security vulnerabilities, adversarial failure scenarios) and should run at whatever capability level the user has configured. If the user is on Opus, these get Opus.

All other persona subagents and local prompt assets prefer the platform's mid-tier model to reduce cost and latency, only when the host permits selecting it. Otherwise use a suitable inherited model and record the unmet tier intent.

The orchestrator (this skill) also inherits the session model; it handles intent discovery, reviewer selection, finding merge/dedup, and synthesis.

#### Run ID

Use the run ID and absolute run dir already created in Stage 1b. Pass `{run_id}` and `{run_dir}` to every persona sub-agent so they can write their full analysis to `{run_dir}/{reviewer_name}.json`.

**Large shared context: pass paths, not contents.** The diff and file list go to every reviewer and validator. When inlining them into each subagent prompt would be wasteful (many files or a big diff), write them once into the run dir (e.g. `full.diff`, `files.txt`) and pass those **paths** in the diff and changed-files slots instead of inline content. The subagent and validator templates instruct the child to Read a staged path. Inline a small diff directly.

#### Spawning

**Agent lifecycle.** Collect each reviewer's final result, including failures, before cleaning up. When the harness lets the caller close or release agents, do so for this review's agents before starting more, moving on, or returning. Do not message a finished agent with no remaining work. Do not assume a slot is free because an agent finished or was interrupted, and do not invent cleanup operations the harness lacks. This rule governs every subagent this skill launches, the Stage 5b validator included.

Omit the `mode` parameter when dispatching sub-agents so the user's configured permission settings apply. Do not pass `mode: "auto"`.

**Resolve `<root>` in any prompt asset before it leaves this stage.** A subagent never runs the artifact-root block, so a `<root>` placeholder still in the text it receives is a literal path it will search and find nothing at. Whenever you read a prompt asset here, by any of the dispatch routes below, substitute the artifact root this run resolved into every `<root>` it contains.

**Record model intent separately from execution permission.** As you select reviewers in Stage 3, record each reviewer's intended tier and the permitted actual route in an internal working list. Do not display tier bookkeeping in the team announcement:

- **Session model** (no override; inherits the session model): `correctness-reviewer`, `security-reviewer`, and `adversarial-reviewer` only.
- **Mid-tier intent**: every other persona and local prompt asset. Resolve the balanced tier with `opencode.models` and pass it only when the native primitive supports it and host policy authorizes the override. In particular, a rule requiring an explicit user model request is not satisfied by this skill or configuration. Otherwise omit `model` and inherit when suitable. Task wording alone does not select a model. Record an unmet fixed-route or different-model requirement as incomplete coverage.

Apply this decision on every native subagent call, including triage, finish leaves, and validation. Never turn tier intent into a permission bypass.

**Bounded in-turn dispatch.** Record `--end select --start dispatch --reviewers <count>` in the stage log (`references/scope.md`) as the batch launches, then dispatch the selected reviewers as one **concurrent batch collected in this turn** rather than serially. Launch so that a bounded collector exists before the first reviewer starts: ask for background execution off only where the foreground call returns a collector you can bound; where the foreground call blocks until the child exits and cannot be bounded, launch with background execution and collect with the host's bounded in-turn wait. Spawn as many reviewers as the host's active-agent cap accepts, and size each batch to the cap the host actually accepts; never hard-code a number. Reviewers are independent by construction (none is fed another's output; see the independence rule above), so batch composition and completion order cannot change any finding, and stable numbers are assigned downstream after the post-merge sort. Where the harness does not run same-message calls concurrently, this identical dispatch **degrades to serial** automatically. That is the correct floor, not a failure.

Collect by the primitive's observed return, not its host name or requested background setting, and with a wait that has an end. Each reviewer's artifact, `{run_dir}/{reviewer_name}.json`, is the fact; the dispatch call's own return, the return of a blocking wait on the launch, or a host-delivered terminal message that names the launch and carries its final payload is one rendering of it. A launch is collected when, within this turn, you hold one of those for that specific launch, or its artifact is on disk. Consume whichever lands first, once. When the artifact lands while the launch is still live, stop that launch before leaving this stage; the agent lifecycle rule below then releases it before anything else starts, so a finished reviewer never holds a slot the validator needs. A launch receipt (the host's acknowledgement that a reviewer started) is uncollected, not a reviewer return, and so is a status or progress update or a wait that returns before the launch is terminal. When dispatch returns an asynchronous id or receipt, keep waiting in-turn with the host's blocking collection capability, repeating the host's wait back to back with nothing between the waits, until every successful launch reaches a terminal outcome or its artifact lands, or the aggregate wall-clock limit `references/subagent-template.md` states has passed since that reviewer's own successful launch (under serial degradation a later reviewer's clock starts when it starts, not when the batch did). A host whose single wait is short reaches that limit by repeating the wait, not by treating one short return as the deadline. Validate each outcome: consume valid compact JSON whether returned in-band or collected asynchronously, and classify a terminal tool error or malformed output as a failed reviewer under the degraded-coverage rules below. A reviewer with neither a terminal outcome nor an artifact when the limit passes is stopped and recorded as a failed reviewer the same way; that is a collected failure, not a partial roster. These harness-managed blocking collection waits gather the batch; they are not the forbidden detached-delegate poll loop. Stage 5 must never run while a launch is still uncollected.

Judge a collector by what it actually does, not its name. A tool is a blocking wait only when it blocks until the launch is terminal. A message is the outcome only when it identifies the launch and carries the final payload, so a notification that reports progress or a state change is not a terminal result. When the host offers no in-turn way to reach a terminal outcome for a launched reviewer, or no wait that can be bounded by any means (a bounded wait, or background execution plus the host's bounded wait), there is no reliable blocking collection path: stop the launched work and take the mode's failure path instead of ending the turn to wait, emitting progress, or synthesizing a partial roster. Hand every persisted peer to its owning cleanup (the cleanup steps `references/cross-model-review.md` defines) before taking that failure path; no return may abandon detached work. In `mode:agent`, emit only `{"status":"failed","reason":"<one sentence>"}`.

This in-turn native batch is not detached work. Never use background bash/CLI dispatch, status-file polling, sleeps, scheduled wakeups, shell no-ops, or "still waiting" turns for either local reviewers or the peer. Native bounded waiting and result delivery remain permitted.

If native parallel calls are unavailable but delegation is permitted and depth remains, run reviewers sequentially. Queue only temporary active-agent capacity errors for later batches. An exhausted nesting limit is not temporary backpressure: record the actual depth error and use only the fallback allowed by `dispatch-capabilities.md` and the chosen depth path. Respect a genuine prohibition or permission denial without retries. A rejected optional model argument is not a delegation denial; use a permitted suitable inherited model where allowed, with unmet model intent disclosed. A parent-context pass contributes attributed evidence only, is excluded from `independent_reviewers`, and cannot earn agreement promotion. Required independent coverage that cannot run remains incomplete.

Before assembling any spawn prompt, read these three files from this skill's directory now: `references/subagent-template.md`, `references/diff-scope.md`, and `references/findings-schema.json`. They define the dispatch shape and the JSON contract every subagent needs, and you cannot construct a valid spawn without them. Read each required reference and selected persona asset with its own file-read call. When the host supports parallel calls, issue them together in one message. Never join files into one shell output. On serial hosts, read one file per turn.

For each selected reviewer, and only for those, read the corresponding local prompt asset from `references/personas/<reviewer-name>.md` and spawn a generic native subagent using the subagent template. Do not use `subagent_type`, typed `Agent` names, or platform-level persona registration. Each persona subagent receives:

1. Their persona file content (identity, failure modes, calibration, suppress conditions)
2. Shared diff-scope rules from `references/diff-scope.md`
3. The JSON output contract from `references/findings-schema.json`
4. PR metadata: title, body, and URL when reviewing a PR (empty string otherwise). Passed in a `<pr-context>` block so reviewers can verify code against stated intent
5. Review context: intent summary, file list, diff, scope mode (`local-aligned` | `pr-remote` | `branch-remote`), and remote head ref (`PR_HEAD_REF` or `<branch-head-ref>`) when set
6. Run ID and reviewer name for the artifact file path
7. **For selected `project-standards` only:** the non-empty Stage 3b criteria mapping — each criteria file with the changed files it governs — wrapped in a `<standards-paths>` block appended to the review context
8. **For `data-migration` only:** the resolved review base ref from Stage 1 (determine scope; the `BASE:` marker), wrapped in `<review-base>` inside the review context so schema drift checks never assume `main`

Persona sub-agents are **read-only** with respect to the project: they review and return structured JSON. They do not edit project files or propose refactors. The one permitted write is saving their full analysis to the resolved run-artifact path specified in the output contract.

**Exception: tree-mutating reviewers.** Mutation testing runs only on a faithful private snapshot, never the shared tree. Detect existing harness isolation first and verify its immutable revision and local changes; do not rename/recreate existing isolation. For new JJ isolation, use `ce-worktree` with a single captured local creation date and `YYYYMMDD-<meaningful-task-slug>` identity shared by workspace name and destination basename under the source workspace's local `.tmp/` layout. Normalize caller names without double-prefixing; retain the chosen identity across retries/resumes/midnight and append `-2`, `-3`, etc. for registration/path collisions. Preserve source bookmarks. Request supported native colocated JJ creation and verify both required naming and colocation; unsupported capability is a blocker, not permission for Git-only isolation. Manual creation, only when lifecycle authority permits, is `(cd "$workspace_root" && jj workspace add --colocate --name "<dated-identity>" --revision "<verified-reviewed-head>" "<absolute-owned-destination>")`, followed by `(cd "<absolute-owned-destination>" && jj git colocation status)`. Adopt any active harness session through its supported mechanism. Verify the snapshot exactly matches the reviewed tree, including local changes; otherwise use an authorized faithful scratch copy under local `.tmp/` or report mutation testing unavailable. Never mutate a mismatched tree.

Retire only authorized, run-owned disposable workspaces: stop workers, leave the target, move active sessions to a surviving workspace, verify exact registered name/path/ownership and required integration, preserve recovery references, and copy/read back required evidence outside the target. Inspect conflicts, tracked changes, ignored and untracked content; removal snapshots do not protect ignored/untracked data. From the surviving absolute root use `jj workspace remove <verified-name>`, not separate Git cleanup or forget-plus-delete. Verify deregistration **and directory disappearance**; warnings may leave files. On incomplete cleanup retain state and report, never force-delete. Keep bookmark deletion separate and preserve recovery/best/archive/still-needed references. `jj workspace forget` is only for explicit unregister-with-files-preserved intent. Harness-owned lifecycle authority and existing cleanup authorization still apply; completion alone authorizes no deletion.

Read-only means non-mutating, not no shell. From the workspace's absolute root use `jj diff`, `jj file show`, `jj file annotate`, and `jj log`; repository-scoped `gh` uses `GIT_DIR=$(jj git root)`. When a finding depends on history, attach one concise provenance evidence line in addition to its motivating source quote; omit history theater for diff-local bugs and never dump full-file annotations. Remote scope inspects only the verified reviewed revision or diff hunks, never unrelated workspace files. Reviewers must not edit project files, move bookmarks, describe changes, push, create PRs, or otherwise mutate project state.

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

The artifact file **must** carry the full detail-tier fields (`why_it_matters`, `evidence`). The compact *return* omits all detail-tier fields **except `first_evidence`**, but writing the compact shape to the artifact (a common reviewer slip) silently strips the detail that Coverage and the keyed detail lines depend on. However review context is delivered, inlined or staged to disk for a large diff, each reviewer still receives the full subagent-template output contract; staging context never permits a thinner one. `suggested_fix` is optional in both tiers; include it in compact returns when present so callers can apply fixes after review. If the file write fails, the compact return still provides everything the merge needs.

**Generic conditional local prompt assets** (`agent-native-reviewer`, `learnings-researcher`) are dispatched only when selected by Stage 3, through the same deterministic foreground batch dispatch as the structured personas. Read their prompt files from `references/personas/`, then give them the same review context bundle the personas receive: entry mode, any PR metadata gathered in Stage 1, intent summary, review base bookmark when known, `BASE:` marker, file list, diff, and `UNTRACKED:` scope notes.

Before composing the `learnings-researcher` dispatch, resolve any Compound Packs declared in config by running this skill's resolver as one command:

```bash
SKILL_DIR="<absolute path of the directory containing the SKILL.md you just read>";
PY="$(for c in python3 python py; do command -v "$c" >/dev/null 2>&1 && "$c" -c '' >/dev/null 2>&1 && { echo "$c"; break; }; done)"; [ -n "$PY" ] || { echo "no working Python 3 interpreter on PATH" >&2; exit 1; };
"$PY" "$SKILL_DIR/scripts/packs-resolve.py"
```

Add the JSON's `roots` (pack `id` + absolute `dir`) to the researcher's search-root list alongside `<root>/solutions/`; report its `errors`/`warnings` once in Coverage and nowhere else. With no `packs:` key the result is empty and nothing changes. A finding grounded in a pack rule cites it as `(pack: <id>, <path within the pack>)`. A matched rule the diff contradicts becomes a numbered finding in Stage 5 (merge findings), while rules the diff honors and relevant past solutions stay Stage 6 (synthesize and present) notes. Skip resolution in `pr-remote`/`branch-remote` scope, because the local config is not the reviewed tree's config. Do not invoke them with a generic "review this" prompt. Their output is unstructured and synthesized separately in Stage 5 and Stage 6, which run in the leaves: save each such return verbatim to `{run_dir}/{reviewer_name}.md` as soon as it is collected and list it in `finish-input.json` under `collection.unstructured_returns` (`references/finish-input.md`); the same applies to `deployment-verification-agent` below.

**Conditional local prompt assets** (`deployment-verification-agent` only) are dispatched as generic subagents through the same deterministic foreground batch dispatch when the migration-artifact condition applies. Read the prompt file from `references/personas/`, then pass the same review context bundle plus the applicability reason (for example, which migration files triggered the prompt asset). Its output is unstructured and must be preserved for Stage 6 synthesis just like the other selected local prompt assets. Schema drift is handled by the `data-migration` persona as structured findings, not here.

#### Cross-model adversarial pass

Stage 3d reserved the permitted native peer or selected the local fallback. Launch that reserved peer in the native batch, under `dispatch-capabilities.md`; never resolve a different recipient silently or launch a detached helper. Use `cross-model-recovery.md` for actual failure classification and any permitted fallback.

After the fast pass, collect all native reviewer and peer outcomes in-turn. Prepare `finish-input.json`, classify the peer under its native reference, stop/release run-owned children where supported, and record `peer.outcome`, `peer.artifact`, and `peer.coverage`. A permitted fallback joins `raw-returns.json`. Record peer end and dispatch end/candidate count in the stage log even when the peer did not run. The merge leaf only folds the classified artifact. Failures/timeouts do not erase the other review evidence, but missing required coverage stays incomplete and is named in Coverage. Agreement promotion requires top-level `independence_verified: true`; false/absent evidence and same-model child agreement never prove cross-model corroboration.

The peer return enters Stage 5 as reviewer `adversarial-<provider>`, like any persona artifact. A pass that never started is recorded as not run (or as the in-process fallback when selected); a started peer that fails, times out, dies, or is reaped is named with its terminal state rather than vanishing silently.
