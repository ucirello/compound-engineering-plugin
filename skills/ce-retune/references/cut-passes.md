# Cut Passes (Phase 4)

A pass applies **one problem class** across the corpus and stops. The work fails in two places: agents overwriting each other, and edits left half-applied. Both are prevented by protocol, not care.

`references/workflow-shapes.md` carries the cross-phase orchestration catalog. This file is the Phase 4 procedure only.

## The pass loop

1. Pick one class from the Phase 3 findings (`references/corpus-audit.md`), or one regression class from `references/halt-taxonomy.md`. One class per pass, no bundling.
2. Write the **ownership manifest**: unit -> owning agent -> exact JJ fileset. Shared assets get a single named owner (below).
3. If the rewrite has cross-referencing strings, author the **contract file** first, serially (below).
4. Dispatch one agent per unit through whatever sub-agent primitive the platform provides, each prompt carrying: the class, the contract path if any, its own paths, and the forbidden paths.
5. **Reconcile** every block touched (below). This is the step that gets skipped.
6. Run the project's own test suite. A pinned string that disappeared is a finding to report with its test path, never a test to edit.
7. Collect each agent's applied/skipped report. Then measure (Phase 5) and finish the pass as one JJ change according to Phase 6.

Eight passes landed in the engagement that produced this skill. Every one reduced to the same class. Resist widening a pass to "also fix the obvious thing" — a pass that changed two classes cannot be attributed by the next measurement.

## Ownership: one problem per agent, disjoint files

Fanning out by **problem** looks natural and collides immediately: a single class — say, a phrasing that implies an absent reader — appears in twenty files, and the next class appears in eleven of the same twenty. Two agents open one file, both write, the second write wins, and the loss is silent because each agent's own diff looks correct.

Fan out by **unit** instead: one agent owns one skill directory and applies the class everywhere inside it. Ownership is then a partition expressed as JJ filesets, and the invariant is checkable before dispatch: every path selected by `jj file list` appears in exactly one manifest row.

| Manifest column | Content |
|---|---|
| unit | the directory the agent owns, e.g. `skills/<name>/` |
| paths | explicit JJ fileset or file list inside it |
| forbidden | shared assets and anything outside `unit`, listed by path |
| class | the one problem being applied |
| contract | path to the canonical mapping, or `none` |

State the forbidden set in the prompt as paths, not as a rule to infer. An agent told "do not touch shared files" will decide for itself what is shared.

## Isolation: separate JJ workspaces or disjoint filesets in one workspace

Disjoint filesets in one workspace are enough when nothing an agent runs mutates state outside its own fileset. That covers most cut passes: edits are text, the manifest is a partition, and one working-copy change keeps `jj diff` readable and the pass easy to inspect.

Create a named JJ workspace per agent with `jj workspace add --name <workspace-name> -r <base-revset> <destination>` when any of these is true:

- Agents run builds, formatters, generators, or anything that writes outside its unit — lockfiles, caches, generated output, a repo-root config.
- An agent needs to run the suite or the harness to check its own edit; concurrent runs in one workspace race on scratch and working-copy files.
- Agents describe, rebase, split, squash, or abandon changes, or move bookmarks; each workspace needs its own working-copy change.
- A pass may need to be abandoned wholesale, and an isolated change is worth more than a shared diff.

Otherwise the isolation cost is real: N workspaces to create, N working-copy changes to inspect and integrate, and conflicts reintroduced on exactly the filesets the manifest was designed to keep apart. Refer to another workspace's current change with the `<workspace-name>@` revset. After the barrier, inspect the participating changes with `jj log` and `jj diff -r <revset>`, then integrate each accepted disjoint change into the pass change with `jj squash --from <source-revset> --into <pass-revset>`.

## The shared-asset trap

Some corpora hold byte-identical copies of a file inside several units, deliberately, with a parity test asserting the copies match. A per-unit agent editing "its" copy breaks parity, and the breakage surfaces as a test failure in a *different* pass, attributed to the wrong change.

Discover them before dispatch. Shape (POSIX shell, including Git Bash; select versioned candidates with a JJ fileset, hash each file, key by basename, and report basenames appearing in more than one path):

```
jj file list 'glob:"**/*.md" | glob:"**/*.py" | glob:"**/*.sh"' | xargs shasum \
  | awk '{ n = $2; sub(/.*\//, "", n); print $1, n }' \
  | sort | uniq -c | awk '$1 > 1'
```

Read the output two ways. A basename with **one** hash across many paths is a maintained shared asset: assign it exactly one owner, list it as forbidden for everyone else, and have that owner propagate the edit to all copies in the same pass. A basename with **several** hashes across paths is drift that already happened — a finding, not necessarily yours to fix in this pass.

Whether a duplication should exist at all is a proposal-time question, gated in `references/corpus-audit.md`. A pass never settles it by factoring out: assign an owner, propagate to every copy, leave the mandate alone.

## Author the contract before a parallel rewrite

When one class spans many files and the strings **cross-reference each other** — a phrase in one unit that another unit quotes, a marker other prose routes to, a shared field name — the rewrite cannot be decided in parallel. `references/workflow-shapes.md` carries what breaks if you skip either the contract or the fan-out.

Serialize the decision. One high-effort agent (or you) writes the canonical mapping to a file first:

```
old string (exact)  ->  new string (exact)  |  rationale  |  units affected
```

Per-unit agents then apply it **verbatim** and report any occurrence the contract does not cover rather than improvising a variant. An uncovered occurrence is a contract gap to resolve serially, not an invitation to extend the contract locally.

Corollary: **gathering the inventory is parallelizable; deciding the canonical rewrite is not.** Fan out to find every occurrence, then collapse to one author to decide the mapping, then fan out to apply it.

## Reconcile

After editing, use the pass fileset to re-read every block touched and fix what the edit itself broke. A half-applied cut is worse than no cut: it leaves prose that is internally inconsistent, which is a defect the corpus did not have before.

Check each of these on every touched file:

- A reference — path, section name, phase number — pointing at something the pass removed.
- A numbered or ordered sequence with a hole, or with a step whose ordinal no longer matches what it depends on.
- An instruction whose precondition was deleted, so it now fires unconditionally or never.
- A reference file nothing routes to any more. Either restore the route or remove the file; an orphan reference is loaded by nobody and rots.
- Two surviving sentences that now contradict each other. Pick one and delete the other; do not leave both and let the model choose.
- Frontmatter, description, or activation text that no longer matches what the unit does after the cut.
- A cut that landed in a duplicated shared asset without the sibling copies following.

## Assertions on mechanical edits

When a pass applies many exact replacements, do it under assertions rather than by hand: for each target, assert the string matches **exactly once** in its file, and abort before writing anything if any target matches zero times or more than once.

Exactly-once is the load-bearing part. Zero matches means an earlier pass already rewrote the anchor; more than one means the anchor is ambiguous and the edit would land in the wrong place. In the engagement this caught an anchor a previous pass had already changed, and because the check ran before any write, nothing was partially applied — the pass was re-derived against current content instead of repaired afterward.

Fail closed, all-or-nothing per file at minimum. A script that writes files 1 through 7 and dies on 8 leaves a state no one can review.

## Report the skips

**Report what you deliberately did not cut, and why.** An agent that applied 100% of its proposals has almost certainly over-cut. A meaningful skip rate is the expected outcome, not underperformance: in the engagement's audit, 81 of 616 proposed cuts were defended and kept.

## The over-cut failure mode

Removing a "you must" does not remove the decision. It hands the decision to the model. `references/halt-taxonomy.md` class 10 carries the mechanism and the observed failure; the line that resolved it without restoring the old prose was **a unit decides its own internal delegation; whether a step runs at all is not its call.**

The pass-loop rule: for every mandate you remove, name what now decides, and check that the new decider is allowed to decide it. If the answer is "the model, at its discretion, whether a required step happens" — that is a required gate, and it stays. This class is also invisible to a probe that never enters the skipped phase, which is why Phase 5 audits the phases the instrument cannot reach and why one clean run proves nothing (`references/noise-floor.md`).

## Discipline that survives contact

- **Fix at the smallest owning layer.** Reword only when rewording is the smallest mechanism; prefer deleting the structure that made the wording necessary.
- **Field names, enums, greppable markers and security guards are data.** They stay. What goes is the justification clause around them that teaches the model a separate consumer is waiting.
- **Never edit tests to make a suite green.** A removed string a test pins is a finding to report, not a test to weaken.
- One problem per agent, each owning a disjoint file set so parallel work cannot collide.

## Reading the failure (Phase 5)

A failure that moves to a later phase is progress and names the next target. A failure at the same site means the fix missed. A run that completes the task while skipping the workflow is a different defect than a halt, and only shows up if Phase 1's two metrics stayed separate.

**Audit the phases the instrument cannot reach.** A probe that skips a phase can never fail in it, so a green streak certifies only what it exercised. List the phases your task never enters, read those files, and treat what you find there as equal in weight to what the runs found. Some of the most consequential defects live where no test looks.

**Report the limit.** Name the paths that remain unmeasured and what would be needed to measure them. Do not let a cleared bar imply coverage it does not have.

## Ship (Phase 6)

Keep each pass as a separate JJ change so history says which measured change was made and why, and release tooling can classify intent. Before composing, editing, validating, or recommending its description, follow this rule: Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Inspect the current project's descriptions with `jj log`; runtime-local syntax and conventions win, and Go guidance applies only where compatible. Derive the description from the measured pass and local history instead of supplying fixed syntax, examples, or templates. Set or edit it with `jj describe <pass-revset>`, then start the next pass with `jj new <pass-revset>`. Keep the measurement artifacts.

Then write the finding down where the next person will hit it: the mechanism, the before and after, the measured numbers, and the hypotheses that died. **Record the ones that died.** They are what stops the next attempt from re-running a dead end, and they are the part every write-up omits.
