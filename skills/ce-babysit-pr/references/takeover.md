# Takeover

Continue someone else's open PR in a replacement PR when the user asks: usually because babysit cannot push to the contributor's branch, or the contributor has stopped responding. The original contributors keep their credit, and the original PR stays open unless the user permits closing it.

**Result:** an open replacement PR under watch whose history carries the original commits with their authors, plus babysit's own changes as separate commits. **Safe failure direction:** when the source cannot be fetched or credit cannot be carried, stop and report rather than open an uncredited replacement.

Take over only on the user's request in an interactive run, and only from an open source PR.

1. **Assess first.** Run the assessment and verdict in `references/intake.md` on the source PR. A Close verdict ends the takeover with that evidence. Update and Rework continue here instead of stopping; with Rework, the replacement carries the described rework.
2. **Bookmark from the source.** Fetch and verify the exact source repository/head bookmark/commit with JJ (intake verifies the live head against the PR OID), never substitute a local ref. Retain original commits and human authors. Use intake's owned-workspace safeguards. Make your changes separately.

   Before composing any new commit: Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards. Read the FULL Go guide at runtime and compare several recent full subjects and bodies with `(cd "$workspace_root" && jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\n"')`. Resolve the actual task/repository history anchor, never hardcode a main branch or replace the review range. Infer prefixes, package syntax, case, tense, body spacing/wrapping and issue style from several messages; repository instructions/history win over incompatible Go conventions. With no history use project/user and compatible Go guidance without invented precedent. Use `jj describe -m "<message composed from the standards above>"`; do not add assistant attribution trailers.
   Illustrative Go source, NOT a mandatory repository template:

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

3. **Update it** before it is pushed: rebase the replacement branch onto the fresh base and apply the comparison rules in steps 2-4 of the verified update in `references/intake.md`. No one else has this branch yet, so the stack, dependent-PR, and lease rules do not apply. Nothing in a takeover touches the source branch.
4. **Recheck the source** for new commits or feedback since you started. Read each new commit the way the assessment read the original series before carrying it over, and fold feedback that still applies into your own changes. Record the source head SHA you finished from.
5. **Confirm before the first push when the source is a fork, or when any carried commit changes CI workflows or code CI runs.** Pushing the replacement to this repository runs that code with the repository's secrets and without GitHub's fork-PR approval gate, so say so and push only after the user confirms.
6. **Open the replacement** through `ce-commit-push-pr mode:pipeline`, passing the source PR URL and the original commit authors (from the source PR's commits) as credit context for the description. Pipeline mode skips `ce-commit-push-pr`'s own handoff to babysit, so this run stays the only watcher. The replacement targets the source PR's base branch and keeps its draft state; when it opened otherwise, correct it (`gh pr edit "<new-N>" --repo "<[host/]owner/repo>" --base "<source-baseRefName>"`, `gh pr ready "<new-N>" --repo "<[host/]owner/repo>" --undo`) before watching.
7. **Watch the replacement.** When this run already took its first snapshot (a takeover requested mid-watch), stop that watcher and continue the invocation on the new PR the way a stack transition does (`references/setup.md`): `--continue-invocation` with the recorded invocation id, start time, and budget, and the posture re-stated. Otherwise no invocation exists yet: start the new PR's first snapshot as `references/tick.md` describes.

Never close the source PR without the user's explicit permission. The report names the source PR, its head SHA at handoff, the replacement PR, and how credit was carried.
