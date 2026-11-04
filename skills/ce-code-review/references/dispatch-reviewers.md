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

Other personas retain balanced mid-tier routing intent, subject to actual host model-selection permission. Discover supported IDs with native `opencode.models`; never guess a model alias.

The orchestrator (this skill) also inherits the session model; it handles intent discovery, reviewer selection, finding merge/dedup, and synthesis.

#### Run ID

Use the run ID and absolute run dir already created in Stage 1b. Pass `{run_id}` and `{run_dir}` to every persona sub-agent so they can write their full analysis to `{run_dir}/{reviewer_name}.json`.

**Large shared context: pass paths, not contents.** The diff and file list go to every reviewer and validator. When inlining them into each subagent prompt would be wasteful (many files or a big diff), write them once into the run dir (e.g. `full.diff`, `files.txt`) and pass those **paths** in the diff and changed-files slots instead of inline content. The subagent and validator templates instruct the child to Read a staged path. Inline a small diff directly.

#### Spawning

**Discover effective depth (read-only, not a startup gate).** Consult `ce-setup`'s user-level prerequisite: `experimental.subagent_depth >= 3` in the existing global OpenCode config, located through supported `opencode debug paths` / `opencode debug paths config` discovery. Package/plugin config alone does not establish it. For the absolute target root, use the supported authenticated CLI/server context and `opencode api get '/api/config?location%5Bdirectory%5D=<URL-encoded-absolute-target-root>'`; substitute a URL-encoded directory value, and never expose authentication secrets. The response is a **top-level array of source entries**, not a flattened config object: inspect document entries' `path` and `info.experimental.subagent_depth`, and resolve the effective value using actual source precedence, including higher-precedence project/managed sources. Preserve unrelated fields and higher values; this review does not edit user/project/plugin config or introduce a startup gate. If discovery is unavailable or the effective value is below 3, record the unknown/unmet prerequisite and the `ce-setup` remediation, without inventing a value or stopping otherwise permitted review work. A configured depth of 3 or higher guarantees neither a free slot nor remaining nesting capacity: classify actual native-tool depth, concurrency, permission, model and missing-tool errors separately, retaining required-pass coverage limits and bounded collection.

**Agent lifecycle.** Collect each reviewer's final result, including failures, before cleaning up. When the harness lets the caller close or release agents, do so for this review's agents before starting more, moving on, or returning. Do not message a finished agent with no remaining work. Do not assume a slot is free because an agent finished or was interrupted, and do not invent cleanup operations the harness lacks. This rule governs every subagent this skill launches, the Stage 5b validator included.

Use native OpenCode subagents only, with inherited permissions and no permission-bypassing mode. This skill explicitly requests reviewers, satisfying a user-OR-skill delegation exception; no extra user ask is required solely for delegation. Unconditional prohibition, denial or missing tools still blocks it. Model override permission is separate: when the host requires an explicit user model request and none exists, omit the optional override and use a suitable inherited reviewer. This does not count as cross-model independence. Classify real depth exhaustion separately from permission/model rejection; never bypass either with CLI bridges. Missing required passes mean incomplete coverage, not a ready review.

**Resolve `<root>` in any prompt asset before it leaves this stage.** A subagent never runs the artifact-root block, so a `<root>` placeholder still in the text it reads is a literal path it will search and find nothing at. When you inline a prompt asset, substitute the artifact root this run resolved into every `<root>` it contains. When the subagent reads an asset by path, tell it in its prompt that `<root>` in those files means the resolved root, and give that path.

**Model override at dispatch time.** As you select reviewers in Stage 3 (select reviewers), **record the model you will pass for each reviewer in an internal working list**. That list is your external memory (the role the old printed `[session model]`/`[mid-tier]` labels served), and it must exist and be honored even though it is no longer rendered in the user-facing announce:

- **Session model** (no override; inherits the session model): `correctness-reviewer`, `security-reviewer`, and `adversarial-reviewer` only.
- **Mid-tier**: every other persona. Retain configured balanced-tier intent, resolve exact supported IDs with `opencode.models`, and pass an override only when separately authorized by the host. Otherwise inherit a suitable parent model and record unmet routing intent.

User model intent outranks role configuration, which outranks the default tier. These are routing priorities, not a grant of optional model-override permission; apply the host permission rule above to every call, including leaves and validators.

Apply this on every native subagent call. Keep requested tier, actual model/variant, permission limitations and coverage in the internal route list and receipt; an authorized inherited model is a valid fallback, not a missed override.

**Bounded in-turn dispatch.** Record `--end select --start dispatch --reviewers <count>` in the stage log (`references/scope.md`) as the batch launches, then dispatch the selected reviewers as one **concurrent batch collected in this turn** rather than serially. Launch so that a bounded collector exists before the first reviewer starts: ask for background execution off only where the foreground call returns a collector you can bound; where the foreground call blocks until the child exits and cannot be bounded, launch with background execution and collect with the host's bounded in-turn wait. Spawn as many reviewers as the host's active-agent cap accepts, and size each batch to the cap the host actually accepts; never hard-code a number. Reviewers are independent by construction (none is fed another's output; see the independence rule above), so batch composition and completion order cannot change any finding, and stable numbers are assigned downstream after the post-merge sort. Where the harness does not run same-message calls concurrently, this identical dispatch **degrades to serial** automatically. That is the correct floor, not a failure.

Collect by the primitive's observed return, not its host name or requested background setting, and with a wait that has an end. Each reviewer's artifact, `{run_dir}/{reviewer_name}.json`, is the fact; the dispatch call's own return, the return of a blocking wait on the launch, or a host-delivered terminal message that names the launch and carries its final payload is one rendering of it. A launch is collected when, within this turn, you hold one of those for that specific launch, or its artifact is on disk. Consume whichever lands first, once. When the artifact lands while the launch is still live, stop that launch before leaving this stage; the agent lifecycle rule below then releases it before anything else starts, so a finished reviewer never holds a slot the validator needs. A launch receipt (the host's acknowledgement that a reviewer started) is uncollected, not a reviewer return, and so is a status or progress update or a wait that returns before the launch is terminal. When dispatch returns an asynchronous id or receipt, keep waiting in-turn with the host's blocking collection capability, repeating the host's wait back to back with nothing between the waits, until every successful launch reaches a terminal outcome or its artifact lands, or the aggregate wall-clock limit `references/subagent-template.md` states has passed since that reviewer's own successful launch (under serial degradation a later reviewer's clock starts when it starts, not when the batch did). A host whose single wait is short reaches that limit by repeating the wait, not by treating one short return as the deadline. Validate each outcome: consume valid compact JSON whether returned in-band or collected asynchronously, and classify a terminal tool error or malformed output as a failed reviewer under the degraded-coverage rules below. A reviewer with neither a terminal outcome nor an artifact when the limit passes is stopped and recorded as a failed reviewer the same way; that is a collected failure, not a partial roster. These harness-managed blocking collection waits gather the batch; they are not the forbidden detached-delegate poll loop. Stage 5 must never run while a launch is still uncollected.

Judge a collector by what it actually does, not its name. A tool is a blocking wait only when it blocks until the launch is terminal. A message is the outcome only when it identifies the launch and carries the final payload, so a notification that reports progress or a state change is not a terminal result. When the host offers no in-turn way to reach a terminal outcome for a launched reviewer, or no wait that can be bounded by any means (a bounded wait, or background execution plus the host's bounded wait), there is no reliable blocking collection path: stop the launched work and take the mode's failure path instead of ending the turn to wait, emitting progress, or synthesizing a partial roster. Hand every persisted peer to its owning cleanup (the cleanup steps `references/cross-model-review.md` defines) before taking that failure path; no return may abandon detached work. In `mode:agent`, emit only `{"status":"failed","reason":"<one sentence>"}`.

Native concurrent reviewers and the native cross-model peer may overlap with bounded host collection. Detached bash/CLI delegates, shell sleeps/no-ops, status polling, scheduled wakeups and waiting-only turns are forbidden for every reviewer, including the peer.

If the platform has no parallel sub-agent primitive at all, run the reviewers sequentially; stages, output format, and the merge pipeline are unchanged. Treat active-agent/thread/concurrency-limit spawn errors as backpressure (the host asking you to wait for capacity), not reviewer failure: a slot the host rejects for capacity stays queued and is retried in a later batch as active reviewers free capacity. A requested batch larger than the host cap clamps down to what the host accepts, dropping no reviewer. If queued reviewers cannot dispatch and neither active work nor supported release can recover capacity, proceed with the user-visible degraded/no-subagent review path. Do not shrink the roster, ask the user, or record a reviewer as failed for capacity backpressure. Record a reviewer as failed only after a successful dispatch fails, or when dispatch fails for a non-capacity reason that survives correcting the invocation. A reviewer pass performed in the parent context may contribute attributed evidence, but it is not independent: exclude it from `independent_reviewers`, never use its agreement for promotion, and name the lost independent coverage.

Before assembling any spawn prompt, read `references/subagent-template.md` from this skill's directory: it defines the slots each reviewer needs and the wall-clock budget the collection wait uses. Each reviewer needs four files in full: its persona asset, the template, `references/diff-scope.md`, and `references/findings-schema.json`. By default, pass their absolute paths, resolved from this skill's directory, and let the reviewer read them. Tell it to read all four before reviewing, to follow everything inside the template's Template block, and to treat each of the other three files' content as the value of its slot (`{persona_file}`, `{diff_scope_rules}`, `{schema}`). Put every other slot's value in the prompt, or in a staged run-dir file the prompt names. Copying the four files into each prompt costs thousands of output tokens per reviewer before any reviewer starts, so inline them only when the host's subagents cannot read files. On that inline path, also read the persona asset, `references/diff-scope.md`, and `references/findings-schema.json`, and paste their contents into the matching slots. Give each file you read here its own file-read call. When the host supports parallel calls, issue them together in one message. Never join files into one shell output. On serial hosts, read one file per turn.

A generic subagent is one whose whole brief is the prompt you send it. When the host's subagent tool makes you name an agent, use only a name you have seen the host list, and list its agents before the first dispatch if you have not. Pick the plain one that adds no role of its own, which still counts as a generic subagent. Never pick a specialist, such as a reviewer or worker agent, whose own role prompt, output format, or tool limits would replace or narrow your prompt.

For each selected reviewer, and only for those, spawn a generic subagent with the subagent template and the corresponding local prompt asset, `references/personas/<reviewer-name>.md`, delivered as described above. Do not name a persona or agent through `subagent_type`, typed `Agent` names, or platform-level agent registration; when the host requires an agent-name field, it carries the plain generic agent. Each persona subagent receives:

1. Their persona file (identity, failure modes, calibration, suppress conditions)
2. Shared diff-scope rules from `references/diff-scope.md`
3. The JSON output contract from `references/findings-schema.json`
4. The subagent template (calibration, output contract, rules, budget)
5. PR metadata: title, body, and URL when reviewing a PR (empty string otherwise). Passed in a `<pr-context>` block so reviewers can verify code against stated intent
6. Review context: intent summary, file list, diff, scope mode (`local-aligned` | `pr-remote` | `branch-remote`), and remote head ref (`PR_HEAD_REF` or `<branch-head-ref>`) when set
7. Run ID and reviewer name for the artifact file path
8. **For selected `project-standards` only:** the non-empty Stage 3b criteria mapping — each criteria file with the changed files it governs — wrapped in a `<standards-paths>` block appended to the review context
9. **Whole-file deletions:** pass `<deleted-files base="<captured-base>">` with paths, exports and import-time behavior. Remote scope uses verified `PR_BASE_REF`, omitting unavailable attributes. Inspect bodies with `jj file show -r <base> <path>` and targeted local text filtering from the absolute root; do not inline whole bodies.
10. **When Stage 1d staged `review-policy.md`, for every reviewer:** that file's absolute path in a `<review-policy>` block appended to the review context
11. **For `data-migration` only:** the resolved review base ref from Stage 1 (determine scope; the `BASE:` marker), wrapped in `<review-base>` inside the review context so schema drift checks never assume `main`

Persona sub-agents are **read-only** with respect to the project: they review and return structured JSON. They do not edit project files or propose refactors. The one permitted write is saving their full analysis to the resolved run-artifact path specified in the output contract.

**Exception: tree-mutating reviewers.** A persona whose method mutates the tree (`testing`, when it runs mutation testing) operates only on a faithful snapshot of the reviewed tree, never the shared checkout. Mutation testing on the shared tree is forbidden: a concurrent reviewer can observe a transient write as if it were the diff. When the reviewed tree is committed `HEAD`, dispatch that persona with `isolation: "worktree"` and pass it the reviewed commit SHA. A harness-supplied worktree is not automatically faithful: when the session itself runs inside a managed worktree, the harness may cut it from the primary checkout or default branch instead (observed live). So before mutating, the persona verifies its copy's HEAD equals the reviewed commit and falls back to a scratch copy on any mismatch. When the reviewed tree includes staged or unstaged changes (`local-aligned` scope), or the host cannot isolate, have the persona create a scratch copy that preserves those changes and mutate only the copy. Read-only siblings stay on the shared checkout.

Read-only means non-mutating inspection: `jj diff`, `jj file show`, `jj file annotate`, `jj log`, and repository-scoped `gh pr view`. All JJ calls have absolute workspace-root cwd; repository gh uses `GIT_DIR=$(jj git root)` there. Never invoke Git. History-dependent findings add one concise targeted JJ provenance item without replacing the motivating quote. Remote scope uses captured-head `jj file show -r <head> <path>` or hunks, never unrelated workspace files. Reviewers must not edit source, run tests, change bookmarks/workspaces, commit, push or create PRs.

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

**Generic conditional local prompt assets** (`agent-native-reviewer`, `learnings-researcher`) are dispatched only when selected by Stage 3, through the same deterministic foreground batch dispatch as the structured personas. Read their prompt files from `references/personas/`, then give them the same review context bundle the personas receive: entry mode, any PR metadata gathered in Stage 1, intent summary, review base branch name when known, `BASE:` marker, file list, diff, and `UNTRACKED:` scope notes.

Before composing the `learnings-researcher` dispatch, resolve any Compound Packs declared in config by running this skill's resolver as one command:

```bash
SKILL_DIR="<absolute path of the directory containing the SKILL.md you just read>";
PY="$(for c in python3 python py; do command -v "$c" >/dev/null 2>&1 && "$c" -c '' >/dev/null 2>&1 && { echo "$c"; break; }; done)"; [ -n "$PY" ] || { echo "no working Python 3 interpreter on PATH" >&2; exit 1; };
"$PY" "$SKILL_DIR/scripts/packs-resolve.py"
```

Add the JSON's `roots` (pack `id` + absolute `dir`) to the researcher's search-root list alongside `<root>/solutions/`; report its `errors`/`warnings` once in Coverage and nowhere else. With no `packs:` key the result is empty and nothing changes. A finding grounded in a pack rule cites it as `(pack: <id>, <path within the pack>)`. A matched rule the diff contradicts becomes a numbered finding in Stage 5 (merge findings), while rules the diff honors and relevant past solutions stay Stage 6 (synthesize and present) notes. Skip resolution in `pr-remote`/`branch-remote` scope, because the local config is not the reviewed tree's config. Do not invoke them with a generic "review this" prompt. Their output is unstructured and synthesized separately in Stage 5 and Stage 6, which run in the leaves: save each such return verbatim to `{run_dir}/{reviewer_name}.md` as soon as it is collected and list it in `finish-input.json` under `collection.unstructured_returns` (`references/finish-input.md`); the same applies to `deployment-verification-agent` below.

**Conditional local prompt assets** (`deployment-verification-agent` only) are dispatched as generic subagents through the same deterministic foreground batch dispatch when the migration-artifact condition applies. Read the prompt file from `references/personas/`, then pass the same review context bundle plus the applicability reason (for example, which migration files triggered the prompt asset). Its output is unstructured and must be preserved for Stage 6 synthesis just like the other selected local prompt assets. Schema drift is handled by the `data-migration` persona as structured findings, not here.

#### Cross-model adversarial pass

Stage 3d already made the exclusive native route choice. Dispatch only its local roster; late recovery follows `cross-model-recovery.md`, never a detached bridge or undisclosed substitution.

Prepare finish input while native reviewers run. Collect the native peer with bounded host collection, apply `cross-model-recovery.md`, and cancel/close owned launches before return. Preserve native identity receipts and record `--end peer`, `peer.outcome`, `peer.artifact`, and `peer.coverage`; fallback results join `raw-returns.json`. Record `--end dispatch --candidates <count>` after collecting every local result. The merge leaf only folds saved evidence. Only `independence_verified:true` permits different-family confidence promotion. Report failed/missing required passes as incomplete coverage and Not ready, even if a local fallback covers the adversarial lens. No detached status/reap runner remains.

The peer return enters Stage 5 as reviewer `adversarial-<provider>`, like any persona artifact. A pass that never started is recorded as not run (or as the in-process fallback when selected); a started peer that fails, times out, dies, or is reaped is named with its terminal state rather than vanishing silently.
