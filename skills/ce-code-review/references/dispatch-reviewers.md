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

All other persona subagents and local prompt assets prefer the configured mid-tier model to reduce cost and latency, only when actual host policy authorizes overrides. Otherwise inherit and disclose unmet configured routing. Delegation permission is not model-override permission.

The orchestrator (this skill) also inherits the session model; it handles intent discovery, reviewer selection, finding merge/dedup, and synthesis.

#### Run ID

Use the run ID and absolute run dir already created in Stage 1b. Pass `{run_id}` and `{run_dir}` to every persona sub-agent so they can write their full analysis to `{run_dir}/{reviewer_name}.json`.

**Large shared context: pass paths, not contents.** The diff and file list go to every reviewer and validator. When inlining them into each subagent prompt would be wasteful (many files or a big diff), write them once into the run dir (e.g. `full.diff`, `files.txt`) and pass those **paths** in the diff and changed-files slots instead of inline content. The subagent and validator templates instruct the child to Read a staged path. Inline a small diff directly.

#### Spawning

**Agent lifecycle.** Collect each reviewer's final result, including failures, before cleaning up. When the harness lets the caller close or release agents, do so for this review's agents before starting more, moving on, or returning. Do not message a finished agent with no remaining work. Do not assume a slot is free because an agent finished or was interrupted, and do not invent cleanup operations the harness lacks. This rule governs every subagent this skill launches, the Stage 5b validator included.

Use native OpenCode generic subagents and inherit permission settings; do not pass an auto-approval mode. This loaded skill explicitly requests reviewer delegation under a user-or-loaded-skill host policy, with no second approval. An unconditional higher policy, actual denial or missing native tool still blocks delegation; never bypass it with shell/other-harness dispatch. Discover effective package and consuming global/project `experimental.subagent_depth` (integer >=3), separately from permission and capacity. Setup documents merging into existing global `~/.config/opencode/opencode.json` or existing JSONC, locating the actual global directory with `opencode debug paths` / `opencode debug paths config`, preserving sibling settings/higher depth and avoiding competing documents. Package config alone does not configure consumers; higher precedence must not lower depth. Do not edit host settings during review.

**Resolve `<root>` in any prompt asset before it leaves this stage.** A subagent never runs the artifact-root block, so a `<root>` placeholder still in the text it reads is a literal path it will search and find nothing at. When you inline a prompt asset, substitute the artifact root this run resolved into every `<root>` it contains. When the subagent reads an asset by path, tell it in its prompt that `<root>` in those files means the resolved root, and give that path.

**Model override at dispatch time.** As you select reviewers in Stage 3 (select reviewers), **record the model you will pass for each reviewer in an internal working list**. That list is your external memory (the role the old printed `[session model]`/`[mid-tier]` labels served), and it must exist and be honored even though it is no longer rendered in the user-facing announce:

- **Session model** (no override; inherits the session model): `correctness-reviewer`, `security-reviewer`, and `adversarial-reviewer` only.
- **Mid-tier**: every other persona/local prompt asset prefers the balanced configured tier (Sonnet-class is a compatibility example). Discover exact provider/model and supported variants with `opencode.models`. Only pass a model when actual host override policy permits it; if a user model request is required, config/tier alone is not sufficient. Otherwise omit the override, inherit and disclose the unmet route. Same-model distinct reviewers do not count as cross-model independence.

Within actual override authority, live user model/effort requests outrank role configuration, then the preferred tier. Preserve layered `config.local.yaml` / `config.yaml` and example choices; validate availability through native discovery. Never silently substitute an explicit model. If authority or availability prevents the route, record requested and inherited/actual models and lost coverage.

Apply the model/permission decision on every native subagent call and record it in the internal list. A preferred tier is never authority to override the host's user-request requirement.

**Bounded in-turn dispatch.** Record `--end select --start dispatch --reviewers <count>` in the stage log (`references/scope.md`) as the batch launches, then dispatch the selected reviewers as one **concurrent batch collected in this turn** rather than serially. Launch so that a bounded collector exists before the first reviewer starts: ask for background execution off only where the foreground call returns a collector you can bound; where the foreground call blocks until the child exits and cannot be bounded, launch with background execution and collect with the host's bounded in-turn wait. Spawn as many reviewers as the host's active-agent cap accepts, and size each batch to the cap the host actually accepts; never hard-code a number. Reviewers are independent by construction (none is fed another's output; see the independence rule above), so batch composition and completion order cannot change any finding, and stable numbers are assigned downstream after the post-merge sort. Where the harness does not run same-message calls concurrently, this identical dispatch **degrades to serial** automatically. That is the correct floor, not a failure.

Collect by the primitive's observed return, not its host name or requested background setting, and with a wait that has an end. Each reviewer's artifact, `{run_dir}/{reviewer_name}.json`, is the fact; the dispatch call's own return, the return of a blocking wait on the launch, or a host-delivered terminal message that names the launch and carries its final payload is one rendering of it. A launch is collected when, within this turn, you hold one of those for that specific launch, or its artifact is on disk. Consume whichever lands first, once. When the artifact lands while the launch is still live, stop that launch before leaving this stage; the agent lifecycle rule below then releases it before anything else starts, so a finished reviewer never holds a slot the validator needs. A launch receipt (the host's acknowledgement that a reviewer started) is uncollected, not a reviewer return, and so is a status or progress update or a wait that returns before the launch is terminal. When dispatch returns an asynchronous id or receipt, keep waiting in-turn with the host's blocking collection capability, repeating the host's wait back to back with nothing between the waits, until every successful launch reaches a terminal outcome or its artifact lands, or the aggregate wall-clock limit `references/subagent-template.md` states has passed since that reviewer's own successful launch (under serial degradation a later reviewer's clock starts when it starts, not when the batch did). A host whose single wait is short reaches that limit by repeating the wait, not by treating one short return as the deadline. Validate each outcome: consume valid compact JSON whether returned in-band or collected asynchronously, and classify a terminal tool error or malformed output as a failed reviewer under the degraded-coverage rules below. A reviewer with neither a terminal outcome nor an artifact when the limit passes is stopped and recorded as a failed reviewer the same way; that is a collected failure, not a partial roster. These harness-managed blocking collection waits gather the batch; they are not the forbidden detached-delegate poll loop. Stage 5 must never run while a launch is still uncollected.

Judge a collector by what it actually does, not its name. A tool is a blocking wait only when it blocks until the launch is terminal. A message is the outcome only when it identifies the launch and carries the final payload, so a notification that reports progress or a state change is not a terminal result. When the host offers no in-turn way to reach a terminal outcome for a launched reviewer, or no wait that can be bounded by any means (a bounded wait, or background execution plus the host's bounded wait), there is no reliable blocking collection path: stop the launched work and take the mode's failure path instead of ending the turn to wait, emitting progress, or synthesizing a partial roster. Hand every persisted peer to its owning cleanup (the cleanup steps `references/cross-model-review.md` defines) before taking that failure path; no return may abandon detached work. In `mode:agent`, emit only `{"status":"failed","reason":"<one sentence>"}`.

Native concurrent reviewer dispatch and bounded in-turn collection are allowed. Detached shell/CLI dispatchers, sleep/status-file polling and scheduled wakeups are not. The cross-model peer uses the same native lifecycle, not a detached exception. Never invent tools or end the turn to wait for an uncollected launch.

Without parallel native dispatch, run permitted reviewers sequentially, preserving stages/schema/merge. Capacity errors queue the reviewer until owned active work is collected/released; clamp batches to actual capacity without dropping lenses. If no supported release or active work can restore capacity, report degraded coverage. Classify depth separately by effective configuration, model rejection separately by discovery, and actual denial/missing tooling separately by policy/capability. Never retry denial or bypass with another harness. At most one same-route transient infrastructure retry within the original budget. Parent inline passes may supply attributed evidence only where the contract permits, never independent-reviewer membership or promotion; lost required independent coverage stays incomplete.

Before assembling any spawn prompt, read `references/subagent-template.md` from this skill's directory: it defines the slots each reviewer needs and the wall-clock budget the collection wait uses. Each reviewer needs four files in full: its persona asset, the template, `references/diff-scope.md`, and `references/findings-schema.json`. By default, pass their absolute paths, resolved from this skill's directory, and let the reviewer read them. Tell it to read all four before reviewing, to follow everything inside the template's Template block, and to treat each of the other three files' content as the value of its slot (`{persona_file}`, `{diff_scope_rules}`, `{schema}`). Put every other slot's value in the prompt, or in a staged run-dir file the prompt names. Copying the four files into each prompt costs thousands of output tokens per reviewer before any reviewer starts, so inline them only when the host's subagents cannot read files. On that inline path, also read the persona asset, `references/diff-scope.md`, and `references/findings-schema.json`, and paste their contents into the matching slots. Give each file you read here its own file-read call. When the host supports parallel calls, issue them together in one message. Never join files into one shell output. On serial hosts, read one file per turn.

A generic subagent is one whose whole brief is the prompt you send it. When the host's subagent tool makes you name an agent, use only a name you have seen the host list, and list its agents before the first dispatch if you have not. Pick the plain one that adds no role of its own, which still counts as a generic subagent. Never pick a specialist, such as a reviewer or worker agent, whose own role prompt, output format, or tool limits would replace or narrow your prompt.

For each selected reviewer, and only those, spawn a native generic subagent with the template and local `references/personas/<reviewer-name>.md` asset. Use a discovered plain generic agent rather than a platform-registered specialist whose own instructions could replace this contract. Each persona receives:

1. Their persona file (identity, failure modes, calibration, suppress conditions)
2. Shared diff-scope rules from `references/diff-scope.md`
3. The JSON output contract from `references/findings-schema.json`
4. The subagent template (calibration, output contract, rules, budget)
5. PR metadata: title, body, and URL when reviewing a PR (empty string otherwise). Passed in a `<pr-context>` block so reviewers can verify code against stated intent
6. Review context: intent summary, file list, diff, scope mode (`local-aligned` | `pr-remote` | `branch-remote`), and remote head ref (`PR_HEAD_REF` or `<branch-head-ref>`) when set
7. Run ID and reviewer name for the artifact file path
8. **For selected `project-standards` only:** the non-empty Stage 3b criteria mapping — each criteria file with the changed files it governs — wrapped in a `<standards-paths>` block appended to the review context
9. **Whole-file deletions, for every reviewer:** a `<deleted-files base="<captured-base-id>">` block listing paths, exports and import-time effects. Use Stage 1's exact diff base (`PR_BASE_REF` in remote PR scope), omitting the attribute if unavailable. Search targeted output of `(cd "$workspace_root" && jj file show -r '<base-id>' '<path>')`; do not load whole deleted bodies into this context or substitute another base.
10. **When Stage 1d staged `review-policy.md`, for every reviewer:** that file's absolute path in a `<review-policy>` block appended to the review context
11. **For `data-migration` only:** the resolved review base ref from Stage 1 (determine scope; the `BASE:` marker), wrapped in `<review-base>` inside the review context so schema drift checks never assume `main`

Persona sub-agents are **read-only** with respect to the project: they review and return structured JSON. They do not edit project files or propose refactors. The one permitted write is saving their full analysis to the resolved run-artifact path specified in the output contract.

**Exception: tree-mutating reviewers.** Mutation testing may run only on a faithful private scratch copy below the reviewed workspace's absolute `.tmp`, never the shared checkout. Detect existing isolation first and preserve harness ownership; verify the copy's captured head and local changes before mutation. Do not assume a harness worktree starts from the reviewed tree. If faithful isolation cannot be established, leave the check unrun and disclose it. Read-only siblings stay on the reviewed workspace.

Read-only means non-mutating, not no shell access. Never invoke the Git executable. Use `jj diff`, `jj file show`, `jj file annotate` and `jj log` with cwd the absolute reviewed workspace root; repository-scoped gh receives GIT_DIR captured by `jj git root` there. History-dependent claims append one concise provenance item (hash, human author, date/subject), never replacing the motivating-line quote or dumping whole-file history. Remote changed-file evidence comes from `jj file show -r '<captured-head>' '<path>'`, annotation at that head, or supplied hunks; never local workspace versions. No project edits, revision switching, commits, pushes or PR mutations.

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

**Generic conditional local prompt assets** (`agent-native-reviewer`, `learnings-researcher`) are dispatched only when selected by Stage 3, through the same native batch. Read their prompt files from `references/personas/`, then give them the same context: entry mode, PR metadata, intent, known base bookmark, exact endpoints, file list, diff and excluded-path notes.

Before composing the `learnings-researcher` dispatch, resolve any Compound Packs declared in config by running this skill's resolver as one command:

```bash
SKILL_DIR="<absolute path of the directory containing the SKILL.md you just read>";
PY="$(for c in python3 python py; do command -v "$c" >/dev/null 2>&1 && "$c" -c '' >/dev/null 2>&1 && { echo "$c"; break; }; done)"; [ -n "$PY" ] || { echo "no working Python 3 interpreter on PATH" >&2; exit 1; };
"$PY" "$SKILL_DIR/scripts/packs-resolve.py"
```

Add the JSON's `roots` (pack `id` + absolute `dir`) to the researcher's search-root list alongside `<root>/solutions/`; report its `errors`/`warnings` once in Coverage and nowhere else. With no `packs:` key the result is empty and nothing changes. A finding grounded in a pack rule cites it as `(pack: <id>, <path within the pack>)`. A matched rule the diff contradicts becomes a numbered finding in Stage 5 (merge findings), while rules the diff honors and relevant past solutions stay Stage 6 (synthesize and present) notes. Skip resolution in `pr-remote`/`branch-remote` scope, because the local config is not the reviewed tree's config. Do not invoke them with a generic "review this" prompt. Their output is unstructured and synthesized separately in Stage 5 and Stage 6, which run in the leaves: save each such return verbatim to `{run_dir}/{reviewer_name}.md` as soon as it is collected and list it in `finish-input.json` under `collection.unstructured_returns` (`references/finish-input.md`); the same applies to `deployment-verification-agent` below.

**Conditional local prompt assets** (`deployment-verification-agent` only) use the same native generic dispatch when the migration-artifact condition applies. Pass its persona, the same review context and triggering paths. Preserve its unstructured output for Stage 6. Structured schema drift findings belong to `data-migration`.

#### Cross-model adversarial pass

Stage 3d binds the exclusive native adversarial route. Dispatch only that roster; any failure uses `cross-model-recovery.md` without duplicate adversarial reads or recipient substitution.

Prepare finish input while native reviewers run. Collect the peer by the same bounded native lifecycle, validate/fold its artifact, record `--end peer`, and persist `peer.outcome`, `peer.artifact`, `peer.coverage` in `finish-input.json`. A fallback return joins `raw-returns.json`. After all local returns, record `--end dispatch --candidates <n>`. Leaves do not decide peer routing. Report failures and lost required coverage, not an implicitly complete pass. Promotion requires top-level `independence_verified: true`; absent/false is attributed evidence only. Release owned launches, retain receipts, and never use a deleted runner or detached shell dispatcher.

The peer enters Stage 5 as `adversarial-<provider>`. Never-started is not run (or the named local fallback); failed, timed-out, malformed or stopped native launches retain their observed terminal state and lost coverage rather than vanishing silently.
