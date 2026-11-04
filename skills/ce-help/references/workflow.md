# Moving work through RocketClaw

Two questions get separate answers. The state of the work decides where it starts. The user's preference decides how hands-on they stay from there.

## Where the work starts

Go by what is already settled.

| What is settled | Start with |
|---|---|
| Nothing yet; they want to know what is worth working on | `ce-ideate`. In a repo, a chosen idea goes on to `ce-brainstorm`, not straight to `ce-plan`. |
| A direction, but the scope or product shape is open, or several solutions could fit | `ce-brainstorm` |
| A named technology or approach that needs a yes or no | `ce-pov` |
| What to build, but how it should work or feel needs trying | `ce-prototype` |
| The outcome is clear (a detailed issue, a PRD, a clear description) and the work is multi-step or touches a risk surface | `ce-plan`. A brainstorm helps but is not required. |
| Small or medium work scoped well enough to start without a plan | `ce-work` with a plain request. It sizes the work and recommends planning if it turns out large. |
| A failure or wrong behavior whose cause is not known, including "why is this slow?" | `ce-debug`. With a known cause and an obvious fix, just fix it or use `ce-work`. |

To choose between `ce-brainstorm` and `ce-plan`, ask whether two reasonable people would build different things from this request. If they would, start with `ce-brainstorm`. It is cheap to try on a small idea, because its lightest tier ends in chat with no file. If the user is unsure of the problem itself, that also points to `ce-brainstorm`.

## How `ce-brainstorm`, `ce-plan`, and `ce-work` connect

`ce-brainstorm` writes requirements, `ce-plan` adds implementation planning to that same file without reopening the product decisions, and `ce-work` builds from the result. `ce-work` will not build from requirements alone.

## How hands-on to stay

`lfg` is optional. It is a way to hand off the remaining steps, and it can start at any of the points below. Staying hands-on and handing off are both valid, so this is the user's preference, not a right or wrong answer. If they have not signaled a preference, show both and say what each one means. If they have, follow it.

| Where they are | Run the next skill | Hand off |
|---|---|---|
| A clear request, nothing written yet | `ce-plan`, or `ce-work` if it needs no plan | `lfg <request>` |
| Just finished `ce-brainstorm` | `ce-plan` | `lfg` |
| `ce-plan` wrote a plan this session | `ce-work` | `lfg` |
| A plan from an earlier session | `ce-work <path>` if it is implementation-ready, otherwise `ce-plan <path>` | `lfg <path>` |
| A bug | `ce-debug` | `lfg <bug>` |

What the choice comes down to:

- Running the skills separately gives the user a checkpoint between them.
- `ce-work` also reaches a PR, so a PR is not a reason to choose `lfg`. Someone who wants to read the code before anything is pushed can ask `ce-work` to commit only.
- `lfg` does not wait for approval of the plan, diff, or findings, and it pushes without asking. Merging normally stays with the user.

These are workflow-authorized routine actions, not permission to bypass host denial, unknown push authority, conflicts, or ambiguous/dirty state. `ce-commit-push-pr` and `ce-babysit-pr` do not repeat approvals for authorized commit/push/PR work or monitoring. Authorized factual stale-description maintenance preserves user content and issue links without a preview/yes-no gate. An optional existing-description rewrite outside that maintenance or explicit apply still needs separate approval; declining it does not block monitoring, and description-only requests stay draft-only. Verified clean-head alignment and authorized watch/rearm need no extra ask; an empty `@` above the exact remote PR head is already aligned. Before declaring no PR/work from empty `@`, inspect `@-` bookmarks, remote branch, and associated PR. Preserve unrelated/ignored work, watch opt-out, and final merge/needs-human boundaries.

When recommending or composing a commit message, read the full https://go.dev/wiki/CommitMessage guide first. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards. Compare several recent full subjects and bodies from the actual relevant verified history head, for example `(cd "$workspace_root" && jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\n"')`. Analyze prefix/package, case/tense, separation, wrapping, and issue placement; project instructions and observed history syntax win over incompatible Go guidance. Preserve the exact reviewed range and never substitute a fixed remote head. With no history, use project/user instructions and compatible Go quality guidance without inventing precedent. Do not prescribe a fixed message syntax.

The `lfg` guide page owns how it handles each starting point and what each stage does, so fetch it before describing them.

### SOURCE GUIDANCE — not a mandatory repository template

> Commit messages, also known as CL (changelist) descriptions, should be formatted per https://go.dev/doc/contribute#commit_messages. For example,

```text
net/http: handle foo when bar

[longer description here in the body]

Fixes #12345
```

> Notably, for the subject (the first line of description):
> - the name of the package affected by the change goes before the colon
> - the part after the colon uses the verb tense + phrase that completes the blank in, “this change modifies Go to **___**”
> - the verb after the colon is lowercase
> - there is no trailing period
> - it should be kept as short as possible (many git viewing tools prefer under ~72 characters, though Go isn’t super strict about this).

> For the body (the rest of the description):
> - the text should be wrapped to ~72 characters (to appease git viewing tools, mainly), unless you really need longer lines (e.g. for ASCII art, tables, or long links).
> - the Fixes line goes after the body with a blank newline separating the two. (It is acceptable but not required to use a trailing period, such as Fixes #12345.).
> - there is no Markdown in the commit message.
> - similarly, we do not use Co-authored-by and Assisted-by lines. Don’t add them.

## What already runs on its own

Do not send someone to repeat a step a skill runs itself. `ce-work` carries work through simplification, review, and the PR, and that PR gets watched. `ce-debug` can carry a fix through review and a PR. `ce-plan` reviews its own plan. Check the recommended skill's guide page for its current chain and thresholds.

`ce-compound` is the exception on the `ce-work` route: the user runs it when the work taught something the final code does not show. `lfg` can run it, and a standing instruction can make it automatic. Refreshing existing learnings is a job of `ce-compound`. The old `ce-compound-refresh` name still works: it prints a deprecation notice and runs that job.
