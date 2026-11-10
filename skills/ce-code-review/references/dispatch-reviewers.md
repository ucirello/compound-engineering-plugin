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

The tiers below are capability defaults. Read `references/subagent-model.md` before the first native spawn; model permission and configured choices override cost tier defaults.

Three reviewers inherit the session model with no override: `correctness-reviewer`, `security-reviewer`, and `adversarial-reviewer`. These perform the highest-stakes analysis (logic bugs, security vulnerabilities, adversarial failure scenarios) and should run at whatever capability level the user has configured. If the user is on Opus, these get Opus.

Other personas and local prompt assets prefer balanced capability for latency/cost, subject to configured choices and model-override permission in the Spawning rules.

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
- **Mid-tier**: every other persona and local prompt asset. When permitted, resolve a balanced capable model through native `opencode.models`; otherwise inherit a suitable parent model and disclose any configured override not applied. Task wording does not select a model. Never guess product aliases or work around host model restrictions.

If the user's or project's active instructions or the live prompt name a model for this subagent, use that model instead of the default tier above. They can name it by the subagent's tier, by its prompt-asset name, or for the subagents being dispatched. Without such an instruction, a model configured for this subagent's role takes precedence over the default tier. Following a named model is not a missed override, and neither is a model configured for this subagent's role.

Apply this to **every native subagent call**, leaves and validators included. Record requested and applied model/effort plus permission/availability gaps. Do not silently ignore a configured role choice; inheritance on a host without permitted overrides is a disclosed limitation, not permission to launch another harness.

**Bounded in-turn dispatch.** Record `--end select --start dispatch --reviewers <count>` in the stage log (`references/scope.md`) as the batch launches, then dispatch the selected reviewers as one **concurrent batch collected in this turn** rather than serially. Launch so that a bounded collector exists before the first reviewer starts: ask for background execution off only where the foreground call returns a collector you can bound; where the foreground call blocks until the child exits and cannot be bounded, launch with background execution and collect with the host's bounded in-turn wait. Spawn as many reviewers as the host's active-agent cap accepts, and size each batch to the cap the host actually accepts; never hard-code a number. Reviewers are independent by construction (none is fed another's output; see the independence rule above), so batch composition and completion order cannot change any finding, and stable numbers are assigned downstream after the post-merge sort. Where the harness does not run same-message calls concurrently, this identical dispatch **degrades to serial** automatically. That is the correct floor, not a failure.

Collect by the primitive's observed return, not its host name or requested background setting, and with a wait that has an end. Each reviewer's artifact, `{run_dir}/{reviewer_name}.json`, is the fact; the dispatch call's own return, the return of a blocking wait on the launch, or a host-delivered terminal message that names the launch and carries its final payload is one rendering of it. A launch is collected when, within this turn, you hold one of those for that specific launch, or its artifact is on disk. Consume whichever lands first, once. When the artifact lands while the launch is still live, stop that launch before leaving this stage; the agent lifecycle rule below then releases it before anything else starts, so a finished reviewer never holds a slot the validator needs. A launch receipt (the host's acknowledgement that a reviewer started) is uncollected, not a reviewer return, and so is a status or progress update or a wait that returns before the launch is terminal. When dispatch returns an asynchronous id or receipt, keep waiting in-turn with the host's blocking collection capability, repeating the host's wait back to back with nothing between the waits, until every successful launch reaches a terminal outcome or its artifact lands, or the aggregate wall-clock limit `references/subagent-template.md` states has passed since that reviewer's own successful launch (under serial degradation a later reviewer's clock starts when it starts, not when the batch did). A host whose single wait is short reaches that limit by repeating the wait, not by treating one short return as the deadline. Ask each wait for as long as the host allows, up to the time left before that limit, rather than the host's default or minimum. For example, where the wait tool takes a timeout of up to an hour, a wait started just after launch asks for the full 20 minutes, not 10 or 60 seconds. A wait still returns as soon as a reviewer finishes, so a long timeout never delays collection. Every return of a wait costs a full re-read of this context, so ten 10-second waits cost about ten times as much as one long wait that collects the same reviewers. Validate each outcome: consume valid compact JSON whether returned in-band or collected asynchronously, and classify a terminal tool error or malformed output as a failed reviewer under the degraded-coverage rules below. A reviewer with neither a terminal outcome nor an artifact when the limit passes is stopped and recorded as a failed reviewer the same way; that is a collected failure, not a partial roster. These harness-managed blocking collection waits gather the batch; they are not the forbidden detached-delegate poll loop. Stage 5 must never run while a launch is still uncollected.

Judge a collector by what it actually does, not its name. A tool is a blocking wait only when it blocks until the launch is terminal. A message is the outcome only when it identifies the launch and carries the final payload, so a notification that reports progress or a state change is not a terminal result. When the host offers no in-turn way to reach a terminal outcome for a launched reviewer, or no wait that can be bounded by any means (a bounded wait, or background execution plus the host's bounded wait), there is no reliable blocking collection path: stop the launched work and take the mode's failure path instead of ending the turn to wait, emitting progress, or synthesizing a partial roster. Hand every persisted peer to its owning cleanup (the cleanup steps `references/cross-model-review.md` defines) before taking that failure path; no return may abandon detached work. In `mode:agent`, emit only `{"status":"failed","reason":"<one sentence>"}`.

Native bounded waiting/result delivery is allowed. Detached shell/CLI review, sleeps, status-file polls, scheduled wakeups and user-facing "still waiting" turns are forbidden, for peers and local reviewers alike. The cross-model peer is also a native subagent and consumes native concurrency capacity.

If the platform has no parallel sub-agent primitive at all, run the reviewers sequentially; stages, output format, and the merge pipeline are unchanged. Treat active-agent/thread/concurrency-limit spawn errors as backpressure (the host asking you to wait for capacity), not reviewer failure: a slot the host rejects for capacity stays queued and is retried in a later batch as active reviewers free capacity. A requested batch larger than the host cap clamps down to what the host accepts, dropping no reviewer. If queued reviewers cannot dispatch and neither active work nor supported release can recover capacity, proceed with the user-visible degraded/no-subagent review path. Do not shrink the roster, ask the user, or record a reviewer as failed for capacity backpressure. Record a reviewer as failed only after a successful dispatch fails, or when dispatch fails for a non-capacity reason that survives correcting the invocation. A reviewer pass performed in the parent context may contribute attributed evidence, but it is not independent: exclude it from `independent_reviewers`, never use its agreement for promotion, and name the lost independent coverage.

Before assembling any spawn prompt, read `references/subagent-template.md` from this skill's directory: it defines the slots each reviewer needs and the wall-clock budget the collection wait uses. Each reviewer needs four files in full: its persona asset, the template, `references/diff-scope.md`, and `references/findings-schema.json`. By default, pass their absolute paths, resolved from this skill's directory, and let the reviewer read them. Tell it to read all four before reviewing, to follow everything inside the template's Template block, and to treat each of the other three files' content as the value of its slot (`{persona_file}`, `{diff_scope_rules}`, `{schema}`). Include this sentence in each reviewer's prompt exactly as written: "Give each file you read its own tool call, so its output comes back on its own, never several files in one command or one script. A read counts only when the whole file came back. Some hosts cut the middle out of a long tool output and leave a truncation marker in its place, so when a read comes back shortened, read the missing lines in smaller ranges before you act on that file." Put every other slot's value in the prompt, or in a staged run-dir file the prompt names. Copying the four files into each prompt costs thousands of output tokens per reviewer before any reviewer starts, so inline them only when the host's subagents cannot read files. On that inline path, also read the persona asset, `references/diff-scope.md`, and `references/findings-schema.json`, and paste their contents into the matching slots. Give each file you read here its own file-read call. When the host supports parallel calls, issue them together in one message. Never join files into one shell output. On serial hosts, read one file per turn.

A generic subagent is one whose whole brief is the prompt you send it. When the host's subagent tool makes you name an agent, use only a name you have seen the host list, and list its agents before the first dispatch if you have not. Pick the plain one that adds no role of its own, which still counts as a generic subagent. Never pick a specialist, such as a reviewer or worker agent, whose own role prompt, output format, or tool limits would replace or narrow your prompt.

For selected reviewers only, spawn a generic native subagent with the template and `references/personas/<reviewer-name>.md`, delivered as above. Do not use persona names as registered agent types; a required agent-name field carries the host's observed plain generic agent. Each receives:

1. Their persona file (identity, failure modes, calibration, suppress conditions)
2. Shared diff-scope rules from `references/diff-scope.md`
3. The JSON output contract from `references/findings-schema.json`
4. The subagent template (calibration, output contract, rules, budget)
5. PR metadata: title, body, and URL when reviewing a PR (empty string otherwise). Passed in a `<pr-context>` block so reviewers can verify code against stated intent
6. Review context: intent summary, file list, diff, scope mode (`local-aligned` | `pr-remote` | `branch-remote`), and remote head ref (`PR_HEAD_REF` or `<branch-head-ref>`) when set
7. Run ID and reviewer name for the artifact file path
8. **For selected `project-standards` only:** the non-empty Stage 3b criteria mapping — each criteria file with the changed files it governs — wrapped in a `<standards-paths>` block appended to the review context
9. **Whole-file deletions, for every reviewer:** a `<deleted-files base="<ref>">` block with the exact verified review base (`PR_BASE_REF` in remote PR scope; omit when unavailable). List each deleted path's exports and import-time registrations/config plugins/top-level calls. Search targeted `jj file show -r <ref> <path>` output to obtain those facts; do not dump whole bodies into context or read a mismatched workspace.
10. **When Stage 1d staged `review-policy.md`, for every reviewer:** that file's absolute path in a `<review-policy>` block appended to the review context
11. **For `data-migration` only:** the resolved review base ref from Stage 1 (determine scope; the `BASE:` marker), wrapped in `<review-base>` inside the review context so schema drift checks never assume `main`

Persona sub-agents are **read-only** with respect to the project: they review and return structured JSON. They do not edit project files or propose refactors. The one permitted write is saving their full analysis to the resolved run-artifact path specified in the output contract.

**Exception: tree-mutating reviewers.** Mutation testing operates only on a faithful scratch copy under the target root's `.tmp/`, never the shared checkout. Pin the reviewed full head ID and verify copy contents, including snapshotted working-copy changes and required untracked inputs. Existing harness isolation retains harness ownership; never replace its registration or assume it copied the right tree. Prefer a plain scratch copy without a task-workspace lifecycle. If a JJ workspace is actually needed, delegate creation/reuse and guarded removal to `ce-worktree`'s dated-name, explicit `--colocate`, exact-base and ownership/recovery contract; do not improvise a workspace bridge. Read-only siblings stay on the shared tree.

**Isolation lifecycle when a workspace is necessary.** The parent owns this lifecycle; leaves never delegate it further. Detect/reuse an already isolated exact-base workspace first, preserving its existing name and native harness ownership. Before new creation verify supported harness adoption, navigation and lifecycle management; otherwise report a compatibility blocker. For a new owned workspace, capture local `YYYYMMDD` once; normalize a meaningful task/PR/revision slug without doubling the date prefix, use `YYYYMMDD-<slug>` identically for registration and destination basename under the surviving workspace's local `.tmp/`, and check both `jj workspace list` and disk. Resolve collisions with `-2`, `-3`, etc.; keep the same chosen identity on retry/resume, not PID/random names. From the surviving absolute root run `jj workspace add --colocate --name <dated-name> --revision <verified-reviewed-head> <absolute-owned-destination>`, then from the new absolute root verify `jj git colocation status` and exact contents/base. Adopt the destination via supported native session navigation or an explicit authorized handoff and verify worker cwd before mutation. Unsupported naming/colocation/adoption is a compatibility blocker, never a Git fallback. Leave PR/source bookmarks unchanged.

Before removing, stop/collect all workers and move any active native session outside the target. Verify exact registration name, absolute path, ownership and authorization. Inspect tracked changes, conflicts, ignored and untracked files; a snapshot does not protect the latter two. Preserve integration/recovery refs and copy evidence outside the target, then read it back. Only from a surviving absolute root run `jj workspace remove <verified-name>`; verify deregistration **and** directory removal. Warnings, retained files or incomplete cleanup are blockers; no forced filesystem deletion, direct Git or guessed name. `jj workspace forget` is unregister-only and preserves files, never a cleanup substitute.

Read-only means non-mutating project inspection, not no shell. Use `jj diff`, `jj file show`, targeted `jj file annotate` and `jj log` with the exact reviewed endpoints, from the supplied absolute workspace root. Before repository-scoped `gh`, export `GIT_DIR=$(jj git root)` there. Never direct Git. A history-dependent claim attaches one concise commit/author/date/subject provenance line, additional to the motivating quote; no full-file dump or provenance theater on diff-local bugs. In remote scope, revision-specific reads/annotation/log target the verified reviewed head, never workspace Read/Grep. No project edits, branch/workspace changes, descriptions/commits, push or PR mutations.

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

**RocketClaw local prompt asset** `learnings-researcher` runs only when selected, through the same deterministic native batch as personas. `agent-native-reviewer` remains a structured persona. Read the learnings asset and pass entry mode, PR metadata, intent, known base bookmark, `BASE`, file list, diff and exclusion notes.

Before composing `learnings-researcher` dispatch, resolve declared RocketClaw Packs with this retained mechanical resolver, run from the absolute target workspace root:

```bash
SKILL_DIR="<absolute path of the directory containing the SKILL.md you just read>";
PY="$(for c in python3 python py; do command -v "$c" >/dev/null 2>&1 && "$c" -c '' >/dev/null 2>&1 && { echo "$c"; break; }; done)"; [ -n "$PY" ] || { echo "no working Python 3 interpreter on PATH" >&2; exit 1; };
"$PY" "$SKILL_DIR/scripts/packs-resolve.py"
```

Add the JSON's `roots` (pack `id` + absolute `dir`) to the researcher's search-root list alongside `<root>/solutions/`; report its `errors`/`warnings` once in Coverage and nowhere else. With no `packs:` key the result is empty and nothing changes. A finding grounded in a pack rule cites it as `(pack: <id>, <path within the pack>)`. A matched rule the diff contradicts becomes a numbered finding in Stage 5 (merge findings), while rules the diff honors and relevant past solutions stay Stage 6 (synthesize and present) notes. Skip resolution in `pr-remote`/`branch-remote` scope, because the local config is not the reviewed tree's config. Do not invoke them with a generic "review this" prompt. Their output is unstructured and synthesized separately in Stage 5 and Stage 6, which run in the leaves: save each such return verbatim to `{run_dir}/{reviewer_name}.md` as soon as it is collected and list it in `finish-input.json` under `collection.unstructured_returns` (`references/finish-input.md`); the same applies to `deployment-verification-agent` below.

**RocketClaw conditional local asset** `deployment-verification-agent` runs as a generic native subagent in the same batch when migration artifacts and risk warrant it. Read its asset; pass ordinary context plus the concrete applicability reason. Preserve its unstructured output for Stage 6. Structured schema drift stays with `data-migration`, not this asset.

#### Cross-model adversarial pass

Stage 3d already made the exclusive route choice and, when applicable, started the native peer. Dispatch only that roster; recovery and fallback follow `cross-model-recovery.md`, never a shell bridge or silent recipient/model change.

Prepare `finish-input.json` while native reviewers run. Collect the peer through bounded native result delivery, never polls; classify recovery/fallback in this parent context before leaves run. Preserve normalized receipts and evidence, release owned native launches where supported, record `--end peer`, and fill `peer.outcome`, `peer.artifact`, `peer.coverage`; a fallback's compact return joins `raw-returns.json`. Once all local outcomes are collected, close dispatch with `--end dispatch --candidates <count>`, even without a peer. Merge only consumes the recorded outcome. Agreement promotion and validator shortcuts require top-level `independence_verified: true`; false/absent independence is attributed evidence only. Coverage distinguishes requested cross-model, actually served identity, in-process fallback, started failure and uncovered lens; no silent full-review claim.

The peer return enters Stage 5 as reviewer `adversarial-<provider>`, like any persona artifact. A pass that never started is recorded as not run (or as the in-process fallback when selected); a started peer that fails, times out, dies, or is reaped is named with its terminal state rather than vanishing silently.
