# Workflow Shapes

Which orchestration shape fits each phase, and what breaks when you pick the wrong one.

## Native OpenCode execution

- **Delegation:** This skill explicitly requests the subagents described below. Where the host permits user- or skill-requested delegation, dispatch through OpenCode's native subagent tool; no second approval is needed. Each dispatch must open a fresh context and return a readable result. Respect an unconditional prohibition, a missing tool, or a denial.
- **Models:** Resolve configured or explicitly requested routes and tiers with `opencode.models`; preserve their intent. Model selection permission is separate from delegation permission. If a model override is forbidden, omit it and use the inherited model only where it satisfies the phase's requirements. Separate contexts on the same model do not establish cross-model coverage. Report unsatisfied requirements rather than silently substituting.
- **Depth and capacity:** Check the configuration sources for the actual project location with `opencode api get '/api/config?location%5Bdirectory%5D=<URL-encoded-absolute-root>'`; apply OpenCode's configuration precedence to verify the effective depth setting, not a response field pretending to report remaining capacity. The [installation prerequisite](https://opencode.ai/v2/docs/config) is `experimental.subagent_depth` of at least `3`, but remaining nesting capacity and concurrency are distinct. Bound the number in flight to the actual host cap, leaving excess work queued; plan the wave count rather than assuming flat cost.

Classify a rejected dispatch from the actual error and whether a child launched: correct a pre-launch argument rejection once when the correction is allowed; queue on transient concurrency saturation. Distinguish missing tools, permission denial, and exhausted nesting depth. Do not retry a denial or evade a depth limit with shell or another harness. Other failures follow the phase's own safe direction: report unlaunched or failed units and incomplete coverage, and do not advance past a required check. In the corpus audit, an unrecovered launch failure blocks the audit: never run the missing side inline.

## The shapes

| Phase | Shape | Why | Failure when mismatched |
|---|---|---|---|
| Archive mining | Serial, local, zero model calls | Classification is a deterministic function of fields present in each log; you will re-run it as the taxonomy changes | Agent-per-log gives a different taxonomy each pass, so the exclusion set cannot be re-derived or audited |
| A/A and A/B runs | Serial within an arm, interleaved across arms, nothing else running | Contention is a confound; interleaving spreads service drift evenly across arms | Concurrent runs inflate duration and can manufacture a timeout that reads as a halt |
| Corpus audit | Fan out by unit, pipelined into per-unit adversarial defense | Units are independent and each needs a full directory read; defense for a unit needs only that unit's findings | A barrier between audit and defense costs the slowest unit and buys nothing |
| Cross-cutting rewrite | One agent authors the contract, then fan out application | The replacement text must be identical everywhere to stay greppable and revertable | No contract: N phrasings of one rewrite. No fan-out: context exhaustion, silent skips |
| Cut passes | Fan out by disjoint file sets, one agent edits every copy of a shared byte-identical asset, barrier before verification | Concurrent edits to one file lose each other; verification must see one tree | Overlapping file sets produce a tree nobody wrote and nobody can bisect |
| Verification | Fan out by independent check, never by file | The checks need different tools and different judgment, and one must be a read no grep can do | Splitting by file runs the same suite N times and skips the coherence read entirely |
| Residual critic | One agent, last, scoped to what did not land | A fresh reader with no stake in the passes is the only one who will call a pass partial | A critic asked to verify the work reports green, which is worth nothing |

## Per phase

**Archive mining is serial and local.** The temptation is to dispatch one agent per log file because there are hundreds of them. Resist it. A script is faster, deterministic, and re-runnable, and re-runnability is the point. The correction that decides whether a baseline is usable at all, excluding empty transcripts and error exits, changes the taxonomy after you have already classified everything, so you will run the classifier more than once. A script re-runs for free and produces the same answer. An agent fleet re-costs the whole archive and produces a slightly different answer. See `references/baseline-mining.md` for the fields and the taxonomy.

**A/A and A/B runs are serial per arm and interleaved across arms.** Never run measurement concurrently with anything else you intend to measure. Metrics differ in how they survive contention, and the distinction decides whether a contended run is salvageable:

- **Robust to contention:** did it complete, did it follow the workflow, which phase it reached, token counts. A run either entered a phase or it did not, regardless of what else was executing.
- **Destroyed by contention:** wall-clock duration and everything derived from it, including anything that depends on a timeout. A contended run that times out mid-phase is indistinguishable from a corpus-caused halt, which is the exact failure this skill is trying to attribute.

So a contended run can still support a completion or adherence claim. It cannot support a latency claim, and it cannot be counted as a halt. Protocol and sample-size math are in `references/noise-floor.md`.

**The corpus audit fans out by unit and pipelines into defense.** One agent per skill directory, each reading that directory in full. That full read is what makes per-unit parallelism worth its cost, and it is why one agent cannot do all the units. Pipeline the adversarial defense stage per unit. A unit's defender needs that unit's findings plus the project's own documented learnings, tests, and history, never the global finding list, so a defense can start the moment its audit returns. A global barrier here only makes every defender wait on the slowest auditor.

Budget the defense stage as first-class work, not a review formality. It is the stage that removes cuts, and the removals are the phase's product as much as the proposals are. If you compress the phase for time, compress the number of units in flight, not the defense. Dispatch shape and finding schema live in `references/corpus-audit.md`.

**A cross-cutting rewrite writes the contract first, then fans out.** When one pattern must change in many units, have a single agent author the canonical contract: the exact text to remove, the exact text to replace it with, and the boundary cases where it does not apply. Then fan out application against that contract.

- **Skip the contract** and N agents produce N phrasings of one rewrite. The change stops being greppable, so you cannot confirm coverage. It stops being revertable as a unit. And when the next measurement fails you cannot tell whether the cause is the change or one agent's variant of it.
- **Skip the fan-out** and one agent reads 30 directories until its usable context is gone. The failure is not an error. It is degradation: the late units get shallow work or get silently skipped, and the output looks complete.

**Cut passes use disjoint file sets, one agent for every copy of a shared asset, then a barrier.** One problem per pass, one agent per pass, and file sets that do not intersect. Byte-identical duplicated assets are the trap. If two passes each touch their own copy of the same file, you get divergence that a parity test catches at best and ships at worst. Assign every copy of a duplicated asset to exactly one agent, even when that agent's problem is not the one the copy most obviously belongs to. Close the fan-out with a barrier before verification. Verification reads a tree, and a tree with a pass still landing in it is not the tree you will ship. Loop mechanics are in `references/cut-passes.md`.

**Verification fans out by independent check.** The axes are different tools and different judgment, so they parallelize cleanly while splitting by file does not:

| Check | What it can see | What it cannot |
|---|---|---|
| Mechanical suite | Pinned strings, schemas, parity between duplicated assets | Whether the surviving prose still makes sense |
| Packaging and manifest checks | Install-time validity, catalog and inventory drift | Runtime behavior |
| Residual-pattern sweep | Remaining instances of the class you just removed, including in files no pass edited | Instances phrased differently from the pattern |
| Coherence read | Dangling cross-references, orphaned "as described above", a phase whose predecessor was deleted | Anything requiring the full suite |

Run the mechanical suite once, as one check, not once per agent. Keep the coherence read in the fan-out and give it a human-style instruction: read the changed files end to end and name anything that no longer follows. It is the only check that finds a reference left pointing at removed text, and no grep will do it.

**The residual critic is one agent, run last.** Give it the pass list, the registered bar, and the measured results, and ask for one line per intended change: landed, partial, or not landed, plus what a next pass would have to do. Instruct it explicitly that declaring success is not its job and that returning an empty list requires naming what it checked to reach that conclusion. Without that framing it will summarize the work approvingly, which tells you nothing you did not already believe.

## Cross-cutting rules

**Fan out by disjoint file ownership, never by item.** Disjoint file ownership means each agent edits its own set of files and no file appears in two agents' sets. One item routinely touches several files and one file routinely hosts several items, so an item-partitioned fan-out silently produces two agents writing the same file. Partition the file set first, then assign each item to the agent that edits its files. An item spanning two agents' file sets is either one agent's job with both files, or it is a contract-then-fan-out (above), not a split.

**A barrier is only justified when the next stage needs cross-item context.** Legitimate: deduplicating findings across all units, an early exit that depends on a total count, a synthesis that compares items against each other. Not legitimate: "I want the list flattened before I continue." That is orchestrator convenience, and it costs you the slowest agent in every wave.

**Pass large context by path plus a short gist.** Give an agent the file paths it must read and two or three sentences of why, not the inlined contents. Inlining spends the orchestrator's context to fill an agent's, which is backwards. The fresh context window is the reason you dispatched.

**Every artifact of this method needs a path decided before the phase that writes it.** The registration and the scored run table (`references/noise-floor.md`), the phase-marker map and the extractor (`references/baseline-mining.md`), the ruled finding set (`references/corpus-audit.md`), the file-assignment manifest and the rewrite contract (`references/cut-passes.md`). Assign paths together at engagement start. The registration must be re-readable by a skeptic after results exist. The extractor and map must be re-runnable when the taxonomy changes. A contract or manifest passed only through a dispatch prompt cannot be checked afterward against what the agents actually did. The durable ones (registration, final scored table, write-up) belong in the repo's own docs location. Put all scratch, including fallback and error captures, under a run directory in the source workspace's ignored `.tmp/` (or local `.tmp/` where there is no JJ workspace); put evidence needed after cleanup outside any disposable workspace.

**Give a schema to anything you will aggregate.** If the orchestrator will count, sort, dedup, or compare results, specify the fields and the enum values in the dispatch prompt. Parsing prose across dozens of returns is where item counts quietly stop matching.

**Budget the serial segments.** A one-agent contract phase blocks its entire fan-out, and a barrier before verification blocks on the slowest pass. When reporting elapsed time, name the serial segments separately instead of letting the total read as the shape's natural speed. Otherwise the next person concludes the fan-out was slow and removes the contract.

**State what a fan-out did not cover.** Units that queued past the cap and never ran, units an agent skipped, files outside every agent's set: list them. Silent truncation is indistinguishable from full coverage in the result, and a coverage claim you did not verify is the same defect as a bar chosen after the fact.

## JJ workspace lifecycle

Used by `references/noise-floor.md` and `references/cut-passes.md`. Resolve the absolute source workspace root with `jj workspace root`; run every JJ command from the intended workspace's absolute root. Detect existing isolation first and retain its verified name and state; do not nest merely to isolate the coordinator. A/A still requires two distinct source workspaces. Respect harness ownership: prefer supported harness creation/adoption when it can supply the required colocated JJ workspaces, and verify the result. An existing workspace that does not meet requirements is not a license to rename, recreate, or modify it; report unmet compatibility, creation, or adoption requirements without silently running unisolated.

For each new run-owned workspace, resolve the exact intended base to a single commit ID. Capture the local creation date once and use `YYYYMMDD-<meaningful-kebab-case-slug>` as both the registered name and directory basename (e.g., `20261008-retune-build-a` and `20261008-retune-build-b`). Normalize caller-supplied names without double-prefixing. Place the absolute destination under the source workspace's ignored `.tmp/` run directory. Check both registrations and destinations for collisions and append `-2`, `-3`, etc.; retain the selected name through retries and resumes. Do not rename source bookmarks.

For direct creation, use [JJ's workspace commands](https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace); verify registration, base, and colocation before dispatch or measurement. Harness-created workspaces require the same verification. Give each worker its absolute workspace path and use supported OpenCode session adoption when a session itself must move.

```bash
(cd "$workspace_root" && jj workspace add --colocate --name "$name" --revision "$verified_base" "$absolute_owned_destination")
(cd "$absolute_owned_destination" && jj git colocation status)
```

Retire only authorized, run-owned workspaces. Stop workers, leave the target, and move any active OpenCode session to a surviving workspace. Verify the target's exact registered name, absolute path, and ownership; prove accepted changes are integrated where required; preserve any recovery references; and copy and read back required traces, receipts, and other evidence outside the target. Inspect tracked changes, conflicts, and ignored or still-untracked files: the removal snapshot does not protect those last two. Leave unrelated, ambiguous, still-referenced, or non-disposable workspaces alone. Respect the harness's authority for harness-owned resources, not a separate cleanup bypass. From a surviving workspace run:

```bash
(cd "$surviving_workspace_root" && jj workspace remove "$verified_workspace_name")
```

Verify deregistration with `jj workspace list` from that surviving root **and** check the target directory disappeared. A successful exit alone is insufficient. If removal fails or is incomplete, leave remaining state and report the blocker; never force-delete or fall back to Git. `jj workspace forget` is for unregistering while preserving files, not removal. Bookmark deletion is a separate action; preserve best, archive, and recovery bookmarks and any references still needed.
