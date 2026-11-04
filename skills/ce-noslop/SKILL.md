---
name: ce-noslop
description: "Rewrite, check, or draft prose so it carries no AI writing tells, reads plainly on the first read, and keeps every source fact. Use when asked to make writing plainer or free of those tells, to check writing for them, or when drafting from supplied content. Use ce-promote for channel-specific marketing copy."
argument-hint: "[mode:author|edit|detect] [text, file path, or nothing]"
---

# Write without slop

Prose that carries no AI tells and that a reader understands on the first read, with every fact the source stated still there. Both goals hold at once: text that is free of tells but still dense has failed, and text that is plain but changes how certain a claim is has failed.

**Done:** the mode's output is returned, every fact, number, name, quote, and citation in the input survives, and nothing was added that the source or the caller did not supply.

**Boundaries:** never touch code blocks, quoted text, frontmatter, link targets, identifiers, or a token the caller's own contract requires, unless the user names that content as the thing to fix. Never say whether text was written by a model. Write a named file in place only when the request asks for that; otherwise return the text.

## Mode

Take a `mode:` token when one is given. Otherwise: no draft means **author**; an imperative on a draft means **edit**; a question about a draft means **detect**.

- **author.** Hold the tests below while the caller writes; return nothing. When handed content and asked to write, draft it under the same tests.
- **edit.** Rewrite only the sentences a test fails on, and return the text. A sentence that passes stays as written, so a second pass on the returned text changes nothing. Say what changed in one line only when the caller asks for it, and keep that line outside the rewritten text and out of any artifact.
- **detect.** Name each pattern found, quote the line, give the fix in a few words. Do not rewrite.

For edit and detect, and for an author passage the tests alone do not settle, read `references/patterns.md`. On text that is not English, apply the tests only. Note that the pattern catalog did not apply inside detect findings or inside a change line the caller asked for, and nowhere else.

## Register

Pick by who reads the result. The caller's own interaction contract wins over any line here.

- **Agent talking to the user.** The reader is a teammate who knows the domain and did not watch the work. Write each sentence as you would say it to them.
- **Repo or team artifact.** Neutral. Match the surrounding document's idiom. No first person, no opinion the artifact does not need. This is the default when no reader is named.
- **The user's own writing.** Preserve voice; make the minimum effective edit. Understandability edits stop at sentence splits and actor restoration that keep the user's word choice.

## The tests

Apply these to every sentence, in author mode as constraints and in edit or detect mode as checks.

1. **Mechanism.** Does the sentence say what the thing does, or how it feels or what it is like? Replace the feeling or figure with the fact it displaced, or cut the sentence.
2. **Portability.** Could the sentence move to another project unchanged? Then it carries no fact about this one.
3. **Actor.** Who does the verb? Name them when the source says who. Keep the passive when the actor is unknown or naming it adds nothing.
4. **One idea.** Would the reader have to reread or decode the sentence? Split it or spell it out. A sentence the reader gets on the first pass stays, however long.
5. **Density.** One device proves nothing. Three or more distinct patterns in a passage, or one repeated across passages, is a finding.
6. **Decision first.** Does the first sentence carry the outcome the reader needs?
7. **Reader.** Can someone without the document or the code open act on this? Gloss the identifier or name the consequence.

Keep exact identifiers, paths, commands, and thresholds. For wording choices, read `references/terminology.md`.

## Commit messages

When the supplied or requested prose is a commit message, first read the full https://go.dev/wiki/CommitMessage guide. Then compare several recent full subjects and bodies from the actual relevant runtime history head. Verify that head rather than assuming a bookmark, and run JJ from the target workspace's absolute root:

```sh
(cd "$workspace_root" && jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\n"')
```

Replace `<verified-history-head>` with the verified revision without changing the history being reviewed. Compare prefix/package conventions, case and tense, subject/body separation, wrapping, and issue placement. Project instructions and observed history syntax win; apply compatible Go quality guidance. Without history, follow project/user instructions and Go guidance without inventing precedent. In detect mode, report mismatches rather than rewriting.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.

### SOURCE GUIDANCE (not a mandatory repository template)

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
