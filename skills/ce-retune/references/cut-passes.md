# Cut Passes (Phase 4)

### Quoted Go source guidance (not a mandatory repository template)

The following verbatim excerpts are from https://go.dev/wiki/CommitMessage. Repository-local syntax ALWAYS wins; the Go illustration does not prescribe message syntax here. Keep the runtime full-guide/history comparison below.

> Commit messages, also known as CL (changelist) descriptions, should be formatted per https://go.dev/doc/contribute#commit_messages. For example,
>
> ```text
> net/http: handle foo when bar
>
> [longer description here in the body]
>
> Fixes #12345
> ```
>
> Notably, for the subject (the first line of description):
>
> - the name of the package affected by the change goes before the colon
> - the part after the colon uses the verb tense + phrase that completes the blank in, “this change modifies Go to **___**”
> - the verb after the colon is lowercase
> - there is no trailing period
> - it should be kept as short as possible (many git viewing tools prefer under ~72 characters, though Go isn’t super strict about this).
>
> For the body (the rest of the description):
>
> - the text should be wrapped to ~72 characters (to appease git viewing tools, mainly), unless you really need longer lines (e.g. for ASCII art, tables, or long links).
> - the Fixes line goes after the body with a blank newline separating the two. (It is acceptable but not required to use a trailing period, such as Fixes #12345.).
> - there is no Markdown in the commit message.
> - we **do not** use `Signed-off-by` lines. Don’t add them. Our Gerrit server & GitHub bots enforce CLA compliance instead.
> - similarly, we do not use Co-authored-by and Assisted-by lines. Don’t add them.
> - when referencing CLs, prefer saying “CL nnn” or using a go.dev/cl/nnn shortlink over a direct Gerrit URL or git hash, since that’s more future-proof.
> - when moving code between repos, include the CL, repository name, and git hash that it was moved from/to, so it is easier to trace history/blame.

A pass applies **one problem class** across the corpus and stops. The work fails in two places: agents overwriting each other, and edits left half-applied. Both are prevented by protocol, not care.

`references/workflow-shapes.md` carries the cross-phase orchestration catalog. This file is the Phase 4 procedure only.

## The pass loop

1. Pick one class from the Phase 3 findings (`references/corpus-audit.md`), or one regression class from `references/halt-taxonomy.md`. One class per pass, no bundling.
2. Write the **file-assignment manifest**: unit -> the agent that edits it -> exact paths. Every copy of a shared asset goes to a single named agent (below).
3. If the rewrite has cross-referencing strings, author the **contract file** first, serially (below).
4. Dispatch one agent per unit through whatever sub-agent primitive the platform provides. Each prompt carries the class, the contract path if any, its own paths, and the forbidden paths.
5. **Reconcile** every block touched (below). This is the step that gets skipped.
6. Run the project's own test suite. A pinned string that disappeared is a finding to report with its test path, never a test to edit.
7. Collect each agent's applied/skipped report. Then measure (Phase 5) and commit the pass alone.

Eight passes landed in the engagement that produced this skill. Every one reduced to the same class. Resist widening a pass to "also fix the obvious thing". A pass that changed two classes cannot be attributed by the next measurement.

## One problem per agent, disjoint files

Fanning out by **problem** looks natural and collides immediately. A single class, say a phrasing that implies an absent reader, appears in twenty files, and the next class appears in eleven of the same twenty. Two agents open one file, both write, the second write wins, and the loss is silent because each agent's own diff looks correct.

Fan out by **unit** instead: one agent edits one skill directory and applies the class everywhere inside it. The file assignment is then a partition of the filesystem, and the invariant is checkable before dispatch: every path appears in exactly one manifest row.

| Manifest column | Content |
|---|---|
| unit | the directory the agent edits, e.g. `skills/<name>/` |
| paths | explicit glob or file list inside it |
| forbidden | shared assets and anything outside `unit`, listed by path |
| class | the one problem being applied |
| contract | path to the canonical mapping, or `none` |

State the forbidden set in the prompt as paths, not as a rule to infer. An agent told "do not touch shared files" will decide for itself what is shared.

## Isolation: separate JJ workspaces or disjoint paths in one workspace

Disjoint paths in one tree are enough when nothing an agent runs mutates state outside its own paths. That covers most cut passes: edits are text, the manifest is a partition, and a single tree keeps the diff readable and the commit trivial.

Pay for a separate JJ workspace when any of these is true:

- Agents run builds, formatters, generators, or anything that writes outside its unit, such as lockfiles, caches, generated output, or a repo-root config.
- An agent needs to run the suite or the harness to check its own edit. Concurrent runs in one workspace race on scratch and working-copy state.
- Agents describe changes, create revisions, or move bookmarks. Parallel agents must not mutate the same working copy or shared bookmarks.
- A pass may need to be abandoned wholesale, and a clean discard is worth more than a shared diff.

Otherwise the isolation cost is real: N checkouts to create, N results to merge, and merge conflicts reintroduced on exactly the files the manifest was designed to keep apart.

Detect existing isolation first and reuse it unchanged, including its name and colocation. Harness-native workspace lifecycle takes precedence; if it cannot meet the naming and colocation requirements for a new workspace, report a safe blocker. For every new workspace, capture the local date once and persist one identity `YYYYMMDD-meaningful-kebab-slug` across retries, resumes, and midnight. Derive the slug from the task, PR, or verified revision, normalize a caller name without double-prefixing, and use the identity for both the registered name and destination basename beneath the existing local `.tmp` parent. Check both registrations and destinations; append `-2`, `-3`, etc. on collisions, never a timestamp, PID, or random suffix. Do not rename existing source or PR bookmarks.

From the absolute source root, create only from a verified base:

```sh
(cd "$source_root" && jj workspace add --colocate --name "$identity" --revision "$verified_base" "$absolute_destination")
(cd "$absolute_destination" && jj git colocation status)
```

Run every JJ command with the absolute target workspace root as cwd, never relying on `-R` to change cwd. Keep scratch and harness output under that workspace's `.tmp`. Repository-scoped `gh` commands require `GIT_DIR=$(jj git root)` evaluated in that same absolute root.

Completion is not cleanup permission. Before authorized destructive cleanup, stop workers, leave the target, and move the harness session to a surviving workspace. Verify exact registered name/path, run ownership, disposability, cleanup authority, and integration when required. Inspect tracked, conflicted, ignored, and untracked state; ignored/untracked files are not protected by snapshots. Preserve recovery bookmarks and copy evidence outside the target, then read it back. Never delete unrelated, still-referenced, non-disposable, or ambiguous content. From the surviving absolute root use `jj workspace remove "$verified_name"`; verify both registration and directory are gone. A warning or failure retains state and reports a blocker, with no force-delete fallback. `jj workspace forget` only unregisters and preserves files; never combine it with filesystem deletion.

## The shared-asset trap

Some corpora hold byte-identical copies of a file inside several units, deliberately, with a parity test asserting the copies match. A per-unit agent editing "its" copy breaks parity, and the breakage shows up as a test failure in a *different* pass, attributed to the wrong change.

Discover them before dispatch. Shape (POSIX shell; hash every candidate file, key by basename, report pairs appearing in more than one path):

```
find . -type f \( -name '*.md' -o -name '*.py' -o -name '*.sh' \) -exec shasum {} + \
  | awk '{ n = $2; sub(/.*\//, "", n); print $1, n }' \
  | sort | uniq -c | awk '$1 > 1'
```

Read the output two ways. A basename with **one** hash across many paths is a maintained shared asset: assign every copy to exactly one agent, list it as forbidden for everyone else, and have that agent propagate the edit to all copies in the same pass. A basename with **several** hashes across paths is drift that already happened. That is a finding, not necessarily yours to fix in this pass.

Whether a duplication should exist at all is a proposal-time question, decided in `references/corpus-audit.md`. A pass never settles it by factoring out. Assign the copies to one agent, propagate to every copy, leave the mandate alone.

## Author the contract before a parallel rewrite

When one class spans many files and the strings **cross-reference each other** (a phrase in one unit that another unit quotes, a marker other prose routes to, a shared field name), the rewrite cannot be decided in parallel. `references/workflow-shapes.md` carries what breaks if you skip either the contract or the fan-out.

Serialize the decision. One high-effort agent (or you) writes the canonical mapping to a file first:

```
old string (exact)  ->  new string (exact)  |  rationale  |  units affected
```

Per-unit agents then apply it **verbatim** and report any occurrence the contract does not cover rather than improvising a variant. An uncovered occurrence is a contract gap to resolve serially, not an invitation to extend the contract locally.

Corollary: **gathering the inventory is parallelizable; deciding the canonical rewrite is not.** Fan out to find every occurrence, then collapse to one author to decide the mapping, then fan out to apply it.

## Reconcile

After editing, re-read every block touched and fix what the edit itself broke. A half-applied cut is worse than no cut. It leaves prose that is internally inconsistent, which is a defect the corpus did not have before.

Check each of these on every touched file:

- A reference (path, section name, phase number) pointing at something the pass removed.
- A numbered or ordered sequence with a hole, or with a step whose ordinal no longer matches what it depends on.
- An instruction whose precondition was deleted, so it now applies unconditionally or never.
- A reference file nothing routes to any more. Either restore the route or remove the file. An orphan reference is loaded by nobody and rots.
- Two surviving sentences that now contradict each other. Pick one and delete the other. Do not leave both and let the model choose.
- Frontmatter, description, or activation text that no longer matches what the unit does after the cut.
- A cut that landed in a duplicated shared asset without the sibling copies following.

## Assertions on mechanical edits

When a pass applies many exact replacements, do it under assertions rather than by hand. For each target, assert the string matches **exactly once** in its file, and abort before writing anything if any target matches zero times or more than once.

Exactly-once is the part that makes the check worth running. Zero matches means an earlier pass already rewrote the anchor. More than one means the anchor is ambiguous and the edit would land in the wrong place. In the engagement this caught an anchor a previous pass had already changed, and because the check ran before any write, nothing was partially applied. The pass was re-derived against current content instead of repaired afterward.

Fail closed, all-or-nothing per file at minimum. A script that writes files 1 through 7 and dies on 8 leaves a state no one can review.

## Report the skips

**Report what you deliberately did not cut, and why.** An agent that applied 100% of its proposals has almost certainly over-cut. A meaningful skip rate is the expected outcome, not underperformance. In the engagement's audit, 81 of 616 proposed cuts were defended and kept.

## The over-cut failure mode

Removing a "you must" does not remove the decision. It hands the decision to the model. `references/halt-taxonomy.md` class 10 carries the mechanism and the observed failure. The line that resolved it without restoring the old prose was **a unit decides its own internal delegation; whether a step runs at all is not its call.**

The pass-loop rule: for every mandate you remove, name what now decides, and check that the new decider is allowed to decide it. If the answer is "the model, at its discretion, whether a required step happens", then that mandate is a required check, and it stays. This class is also invisible to a probe that never enters the skipped phase. That is why Phase 5 audits the phases the instrument cannot reach, and why one clean run proves nothing (`references/noise-floor.md`).

## Discipline that survives contact

- **Fix at the smallest layer that defines the behavior.** Reword only when rewording is the smallest mechanism; prefer deleting the structure that made the wording necessary.
- **Field names, enums, greppable markers and security guards are data.** They stay. What goes is the justification clause around them that teaches the model a separate consumer is waiting.
- **Never edit tests to make a suite green.** A removed string a test pins is a finding to report, not a test to weaken.
- One problem per agent, each editing a disjoint file set so parallel work cannot collide.

## Reading the failure (Phase 5)

A failure that moves to a later phase is progress and names the next target. A failure at the same site means the fix missed. A run that completes the task while skipping the workflow is a different defect than a halt, and only shows up if Phase 1's two metrics stayed separate.

**Audit the phases the instrument cannot reach.** A probe that skips a phase can never fail in it, so a green streak certifies only what it exercised. List the phases your task never enters, read those files, and treat what you find there as equal in weight to what the runs found. Some of the most consequential defects live where no test looks.

**Report the limit.** Name the paths that remain unmeasured and what would be needed to measure them. Do not let a cleared bar imply coverage it does not have.

## Ship (Phase 6)

Commit each pass separately with its own message so the history says which change was made and why, and so release tooling can classify intent. Keep the measurement artifacts.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.

Before composing, read the full guide and compare several recent subjects and bodies using `(cd "$workspace_root" && jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\\n"')`, replacing the placeholder with the task-verified history head. Repository-local syntax always wins: examine prefixes/packages, casing, tense, subject/body separation, wrapping, and issue references. With no history, follow explicit instructions and compatible Go guidance without inventing precedent. Do not include Markdown or Co-authored-by/Assisted-by attribution in messages. Record the message with `(cd "$workspace_root" && jj describe -m "<message composed from the standards above>")`.

Then write the finding down where the next person will hit it: the mechanism, the before and after, the measured numbers, and the hypotheses that died. **Record the ones that died.** They are what stops the next attempt from re-running a dead end, and they are the part every write-up omits.
