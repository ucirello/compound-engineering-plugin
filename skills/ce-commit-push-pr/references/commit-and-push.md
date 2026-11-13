# Committing and pushing

If stack construction already committed its layers, continue to Step 4; Step 5 publishes them. On the default bookmark first follow `branch-creation.md`.

Scan changed paths for naturally distinct concerns; at most two or three logical groups, whole files only. Ambiguity favors one change. Name owned paths explicitly in `jj commit <paths> -m "<message composed from the standards above>"`; do not commit the whole working copy indiscriminately. Honor `exclude:<paths>` without saving, moving, or committing those files and report their exclusion. Inspect the resulting change and remaining working copy to confirm the exact group. Do not rewrite other people's changes or lose their authorship. Preserve human contribution credit required by the repository, using exact recorded identities, never invented emails; compatible Go guidance does not override project-local credit requirements.

## Message standards — read before every composition

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.

Before composing, read the **full** Go guide at runtime. Resolve the history head from the actual task and repository (including the verified layer parent/head in stack mode), not a hardcoded default branch. From the target workspace's absolute root run `jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\n"'`. Compare several complete subjects **and bodies** for prefixes/package names, casing, tense, subject/body separation, wrapping and reference placement. Project instructions and that repository-local syntax always win over differing Go guidance; apply compatible guidance to clarity, quality and structure within the observed pattern. If no history exists use explicit project/user instructions and Go guidance without inventing precedent.

When a plan's Implementation Unit ID is already in hand, record the applicable U-ID in the runtime-composed message using local conventions. Do not hunt for a plan; omit for mixed/unclear units. Record the actual changed behavior and any required issue/PR references without imposing fixed syntax.

### Verbatim Go source example and guidance (illustrative, not a mandatory repository template)

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

Apply the **Project publishing gate** before pushing. Reverify the intended feature bookmark, exact committed head, remote and push authority. Move only that owned bookmark to the verified committed change when necessary, then use `jj git push --remote <verified-remote> --bookmark <feature>` (with `--allow-new` only for an authorized new remote bookmark). Never push an unnamed working-copy tip or guess a current branch. If clean and already published this is a no-op.
