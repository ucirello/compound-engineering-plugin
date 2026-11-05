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

Three reviewers inherit the session model with no override: `correctness-reviewer`, `security-reviewer`, and `adversarial-reviewer`. These perform the highest-stakes analysis (logic bugs, security vulnerabilities, adversarial failure scenarios) and should run at whatever capability level the user has configured. If the user is on Opus, these get Opus.

All other persona subagents and local prompt assets prefer the platform's mid-tier model when model-selection permission allows it; otherwise inherit a suitable session model and disclose unmet requirements. Use native `opencode.models` and subagents, never another harness dispatcher.

The orchestrator (this skill) also inherits the session model; it handles intent discovery, reviewer selection, finding merge/dedup, and synthesis.

#### Run ID

Use the run ID and absolute run dir already created in Stage 1b. Pass `{run_id}` and `{run_dir}` to every persona sub-agent so they can write their full analysis to `{run_dir}/{reviewer_name}.json`.

**Large shared context: pass paths, not contents.** The diff and file list go to every reviewer and validator. When inlining them into each subagent prompt would be wasteful (many files or a big diff), write them once into the run dir (e.g. `full.diff`, `files.txt`) and pass those **paths** in the diff and changed-files slots instead of inline content. The subagent and validator templates instruct the child to Read a staged path. Inline a small diff directly.

#### Spawning

**Agent lifecycle.** Collect each reviewer's final result, including failures, before cleaning up. When the harness lets the caller close or release agents, do so for this review's agents before starting more, moving on, or returning. Do not message a finished agent with no remaining work. Do not assume a slot is free because an agent finished or was interrupted, and do not invent cleanup operations the harness lacks. This rule governs every subagent this skill launches, the Stage 5b validator included.

Omit the `mode` parameter when dispatching sub-agents so the user's configured permission settings apply. Do not pass `mode: "auto"`.

**Resolve `<root>` in any prompt asset before it leaves this stage.** A subagent never runs the artifact-root block, so a `<root>` placeholder still in the text it reads is a literal path it will search and find nothing at. When you inline a prompt asset, substitute the artifact root this run resolved into every `<root>` it contains. When the subagent reads an asset by path, tell it in its prompt that `<root>` in those files means the resolved root, and give that path.

**Model override at dispatch time.** As you select reviewers in Stage 3 (select reviewers), **record the model you will pass for each reviewer in an internal working list**. That list is your external memory (the role the old printed `[session model]`/`[mid-tier]` labels served), and it must exist and be honored even though it is no longer rendered in the user-facing announce:

- **Session model** (no override; inherits the session model): `correctness-reviewer`, `security-reviewer`, and `adversarial-reviewer` only.
- **Mid-tier intent**: every other persona and local agent. Resolve an available balanced model through `opencode.models` only when the host permits choosing it. A tool's optional model field is not permission: if explicit user model authorization is required and absent, omit it and inherit when suitable. Keep configured tiers as intent and disclose any unmet fixed-route requirement.

Conversation model requests outrank role configuration, then project preferences, then default tiers, within the host's actual model-selection permissions. A project/skill preference is not an explicit user model request when the host requires one. Never silently substitute for a required fixed route or claim same-model reviewers satisfy cross-model coverage.

Apply this permission-aware list on every native subagent call, including validators and finish leaves. This skill explicitly requests delegation under a user-or-skill rule; no second approval is needed. Unconditional prohibition, actual denial, missing tool and effective nesting capacity remain distinct constraints. Classify the actual error and never evade policy/depth through another harness. Use allowed parent/inline fallback only where its independence contract permits, naming lost coverage.

**Bounded in-turn dispatch.** Record `--end select --start dispatch --reviewers <count>` in the stage log (`references/scope.md`) as the batch launches, then dispatch the selected reviewers as one **concurrent batch collected in this turn** rather than serially. Launch so that a bounded collector exists before the first reviewer starts: ask for background execution off only where the foreground call returns a collector you can bound; where the foreground call blocks until the child exits and cannot be bounded, launch with background execution and collect with the host's bounded in-turn wait. Spawn as many reviewers as the host's active-agent cap accepts, and size each batch to the cap the host actually accepts; never hard-code a number. Reviewers are independent by construction (none is fed another's output; see the independence rule above), so batch composition and completion order cannot change any finding, and stable numbers are assigned downstream after the post-merge sort. Where the harness does not run same-message calls concurrently, this identical dispatch **degrades to serial** automatically. That is the correct floor, not a failure.

Collect by the primitive's observed return, not its host name or requested background setting, and with a wait that has an end. Each reviewer's artifact, `{run_dir}/{reviewer_name}.json`, is the fact; the dispatch call's own return, the return of a blocking wait on the launch, or a host-delivered terminal message that names the launch and carries its final payload is one rendering of it. A launch is collected when, within this turn, you hold one of those for that specific launch, or its artifact is on disk. Consume whichever lands first, once. When the artifact lands while the launch is still live, stop that launch before leaving this stage; the agent lifecycle rule below then releases it before anything else starts, so a finished reviewer never holds a slot the validator needs. A launch receipt (the host's acknowledgement that a reviewer started) is uncollected, not a reviewer return, and so is a status or progress update or a wait that returns before the launch is terminal. When dispatch returns an asynchronous id or receipt, keep waiting in-turn with the host's blocking collection capability, repeating the host's wait back to back with nothing between the waits, until every successful launch reaches a terminal outcome or its artifact lands, or the aggregate wall-clock limit `references/subagent-template.md` states has passed since that reviewer's own successful launch (under serial degradation a later reviewer's clock starts when it starts, not when the batch did). A host whose single wait is short reaches that limit by repeating the wait, not by treating one short return as the deadline. Ask each wait for as long as the host allows, up to the time left before that limit, rather than the host's default or minimum. For example, where the wait tool takes a timeout of up to an hour, a wait started just after launch asks for the full 20 minutes, not 10 or 60 seconds. A wait still returns as soon as a reviewer finishes, so a long timeout never delays collection. Every return of a wait costs a full re-read of this context, so ten 10-second waits cost about ten times as much as one long wait that collects the same reviewers. Validate each outcome: consume valid compact JSON whether returned in-band or collected asynchronously, and classify a terminal tool error or malformed output as a failed reviewer under the degraded-coverage rules below. A reviewer with neither a terminal outcome nor an artifact when the limit passes is stopped and recorded as a failed reviewer the same way; that is a collected failure, not a partial roster. These harness-managed blocking collection waits gather the batch; they are not the forbidden detached-delegate poll loop. Stage 5 must never run while a launch is still uncollected.

Judge a collector by what it actually does, not its name. A tool is a blocking wait only when it blocks until the launch is terminal. A message is the outcome only when it identifies the launch and carries the final payload, so a notification that reports progress or a state change is not a terminal result. When the host offers no in-turn way to reach a terminal outcome for a launched reviewer, or no wait that can be bounded by any means (a bounded wait, or background execution plus the host's bounded wait), there is no reliable blocking collection path: stop the launched work and take the mode's failure path instead of ending the turn to wait, emitting progress, or synthesizing a partial roster. Hand every persisted peer to its owning cleanup (the cleanup steps `references/cross-model-review.md` defines) before taking that failure path; no return may abandon detached work. In `mode:agent`, emit only `{"status":"failed","reason":"<one sentence>"}`.

This in-turn batch is not a detached shell delegate. Native blocking waits and result delivery are allowed; background model CLIs, shell sleep/status loops, scheduled wakeups and progress-only waiting turns are forbidden for both local reviewers and the cross-model pass. A native peer may overlap only when terminal collection is reliable; otherwise collect it synchronously before local dispatch.

If the platform has no parallel sub-agent primitive at all, run the reviewers sequentially; stages, output format, and the merge pipeline are unchanged. Treat active-agent/thread/concurrency-limit spawn errors as backpressure (the host asking you to wait for capacity), not reviewer failure: a slot the host rejects for capacity stays queued and is retried in a later batch as active reviewers free capacity. A requested batch larger than the host cap clamps down to what the host accepts, dropping no reviewer. If queued reviewers cannot dispatch and neither active work nor supported release can recover capacity, proceed with the user-visible degraded/no-subagent review path. Do not shrink the roster, ask the user, or record a reviewer as failed for capacity backpressure. Record a reviewer as failed only after a successful dispatch fails, or when dispatch fails for a non-capacity reason that survives correcting the invocation. A reviewer pass performed in the parent context may contribute attributed evidence, but it is not independent: exclude it from `independent_reviewers`, never use its agreement for promotion, and name the lost independent coverage.

Before assembling any spawn prompt, read `references/subagent-template.md` from this skill's directory: it defines the slots each reviewer needs and the wall-clock budget the collection wait uses. Each reviewer needs four files in full: its persona asset, the template, `references/diff-scope.md`, and `references/findings-schema.json`. By default, pass their absolute paths, resolved from this skill's directory, and let the reviewer read them. Tell it to read all four before reviewing, to follow everything inside the template's Template block, and to treat each of the other three files' content as the value of its slot (`{persona_file}`, `{diff_scope_rules}`, `{schema}`). Put every other slot's value in the prompt, or in a staged run-dir file the prompt names. Copying the four files into each prompt costs thousands of output tokens per reviewer before any reviewer starts, so inline them only when the host's subagents cannot read files. On that inline path, also read the persona asset, `references/diff-scope.md`, and `references/findings-schema.json`, and paste their contents into the matching slots. Give each file you read here its own file-read call. When the host supports parallel calls, issue them together in one message. Never join files into one shell output. On serial hosts, read one file per turn.

A generic subagent is one whose whole brief is the prompt you send it. When the host's subagent tool makes you name an agent, use only a name you have seen the host list, and list its agents before the first dispatch if you have not. Pick the plain one that adds no role of its own, which still counts as a generic subagent. Never pick a specialist, such as a reviewer or worker agent, whose own role prompt, output format, or tool limits would replace or narrow your prompt.

For each selected reviewer, and only those, spawn a native generic subagent seeded with the template and `references/personas/<reviewer-name>.md`. Do not select a platform-level specialist whose role replaces this brief; a required agent-name field carries the observed plain generic agent. Each receives:

1. Their persona file (identity, failure modes, calibration, suppress conditions)
2. Shared diff-scope rules from `references/diff-scope.md`
3. The JSON output contract from `references/findings-schema.json`
4. The subagent template (calibration, output contract, rules, budget)
5. PR metadata: title, body, and URL when reviewing a PR (empty string otherwise). Passed in a `<pr-context>` block so reviewers can verify code against stated intent
6. Review context: intent summary, file list, diff, scope mode (`local-aligned` | `pr-remote` | `branch-remote`), and remote head ref (`PR_HEAD_REF` or `<branch-head-ref>`) when set
7. Run ID and reviewer name for the artifact file path
8. **For selected `project-standards` only:** the non-empty Stage 3b criteria mapping — each criteria file with the changed files it governs — wrapped in a `<standards-paths>` block appended to the review context
9. **For whole-file deletions:** include `<deleted-files base="<captured-base>">` with exports and import-time registrations/effects. In PR-remote use `PR_BASE_REF`, omitting the attribute if unavailable. Search `jj file show -r <captured-base> <path>` output locally for those facts rather than dumping full bodies into this context.
10. **When Stage 1d staged `review-policy.md`, for every reviewer:** that file's absolute path in a `<review-policy>` block appended to the review context
11. **For `data-migration` only:** the resolved review base ref from Stage 1 (determine scope; the `BASE:` marker), wrapped in `<review-base>` inside the review context so schema drift checks never assume `main`

Persona sub-agents are **read-only** with respect to the project: they review and return structured JSON. They do not edit project files or propose refactors. The one permitted write is saving their full analysis to the resolved run-artifact path specified in the output contract.

**Exception: tree-mutating reviewers.** Mutation testing operates only in a faithful isolated snapshot, never the shared workspace. Detect existing harness-owned isolation first and preserve its verified name and lifecycle authority. For a new JJ workspace use `(cd "$workspace_root" && jj workspace add --colocate --name "<unique-owned-name>" --revision "<captured-head>" "<absolute-owned-local-.tmp-destination>")`; verify `jj git colocation status` and the captured head from the destination's absolute root. If using ce-worktree, capture the local date once and choose `YYYYMMDD-<meaningful-kebab-slug>`, one identity for workspace name and destination basename, checking registrations and paths for collisions and adding `-2`, `-3` suffixes. Keep names stable across retries/resumes/midnight; do not rename existing isolation or PR/source bookmarks. Prefer supported harness-native colocated JJ isolation and session adoption; unmet capabilities are blockers, not Git fallback. A faithful local `.tmp/` copy that preserves current reviewed changes is allowed when workspace isolation is unavailable; verify exact tree fidelity before mutation. Read-only siblings stay on the shared workspace.

Cleanup requires authorization: stop workers, leave the target and move active harness sessions to a surviving workspace, verify exact registered name/path/run ownership, integration if required, conflicts and tracked/ignored/untracked content, and copy/read back evidence outside it while retaining recovery references. Never remove ambiguous, unrelated, still-referenced or non-disposable content. Use `jj workspace remove <verified-name>` from the surviving absolute root and verify both deregistration and directory disappearance. Warnings may leave files; retain state/report the blocker, never force-delete or fall back to Git. `jj workspace forget` is unregister-only while preserving files. Bookmark cleanup is separate and preserves recovery/archive references. See https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace .

Read-only means non-mutating, not no shell. Use `jj diff`, `jj file show`, `jj file annotate -r <captured-head> <path>`, targeted `jj log` and repository-scoped `GIT_DIR=$(jj git root) gh pr view`, always from the absolute target workspace root. Never execute Git. When a claim depends on line history, attach one concise provenance item from annotation/history at the reviewed head in addition to its motivating-line quote; omit history theater on diff-local defects. Remote scope uses only the verified reviewed tree, never workspace file contents. Do not edit project files, switch trees, describe changes, push or create PRs.

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

**Generic conditional local prompt assets** (`agent-native-reviewer`, `learnings-researcher`) dispatch only when selected in Stage 3, through the same foreground batch. Read their persona files and give them the same entry mode, PR metadata, intent, known base bookmark, captured base/head, file list, diff and untracked exclusions.

Before composing the `learnings-researcher` dispatch, resolve any Compound Packs declared in config by running this skill's resolver as one command:

```bash
SKILL_DIR="<absolute path of the directory containing the SKILL.md you just read>";
PY="$(for c in python3 python py; do command -v "$c" >/dev/null 2>&1 && "$c" -c '' >/dev/null 2>&1 && { echo "$c"; break; }; done)"; [ -n "$PY" ] || { echo "no working Python 3 interpreter on PATH" >&2; exit 1; };
"$PY" "$SKILL_DIR/scripts/packs-resolve.py"
```

Add the JSON's `roots` (pack `id` + absolute `dir`) to the researcher's search-root list alongside `<root>/solutions/`; report its `errors`/`warnings` once in Coverage and nowhere else. With no `packs:` key the result is empty and nothing changes. A finding grounded in a pack rule cites it as `(pack: <id>, <path within the pack>)`. A matched rule the diff contradicts becomes a numbered finding in Stage 5 (merge findings), while rules the diff honors and relevant past solutions stay Stage 6 (synthesize and present) notes. Skip resolution in `pr-remote`/`branch-remote` scope, because the local config is not the reviewed tree's config. Do not invoke them with a generic "review this" prompt. Their output is unstructured and synthesized separately in Stage 5 and Stage 6, which run in the leaves: save each such return verbatim to `{run_dir}/{reviewer_name}.md` as soon as it is collected and list it in `finish-input.json` under `collection.unstructured_returns` (`references/finish-input.md`); the same applies to `deployment-verification-agent` below.

**Conditional local prompt assets** (`deployment-verification-agent` only) dispatch as native generic subagents in the same foreground batch when the migration-artifact condition applies. Read its persona file and pass the same bundle plus the applicability reason. Preserve its unstructured output for Stage 6. The data-migration persona handles schema drift as structured findings.

#### Cross-model adversarial pass

Stage 3d already bound the native adversarial route and local roster. Do not substitute or restart it here except under the bounded owning recovery rules. Dispatch only that settled local roster.

Prepare `finish-input.json` while the native reviewer batch runs; never poll the peer. Collect every native launch to terminal within its bound, then apply `cross-model-review.md` and `cross-model-recovery.md` for trusted fold-in, bounded recovery and native cleanup. Persist `peer.outcome`, `peer.artifact`, and `peer.coverage`; any permitted local fallback joins `raw-returns.json`. Record `--end peer`, then `--end dispatch --candidates <count>` once all local returns are collected. The merge leaf folds the recorded artifact and does not dispatch or decide peer routing. Failure/timeout remains visible and required unmet coverage remains incomplete. Only attested `independence_verified: true` permits cross-model confidence promotion; record whether the adversarial lens ran natively cross-model or through local fallback.

The peer return enters Stage 5 as reviewer `adversarial-<provider>`, like any persona artifact. A pass that never started is recorded as not run (or as the in-process fallback when selected); a started peer that fails, times out, dies, or is reaped is named with its terminal state rather than vanishing silently.
