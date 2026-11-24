# Evidence and Delegation

Read before grounding or delegation on the full path. The skill body owns interaction and completion; this reference owns the run directory, the evidence pass, and capability fallbacks.

## Interaction method

The skill body's interaction rule decides whether a question is needed. When it is, use the host's question capability already in the current tool list; never call a user-facing question tool to discover whether it exists. If no such tool is available, ask in chat only when a person is participating. Otherwise return the missing information to the calling workflow.

## Model tiers

Dispatch is tiered by task shape, never hardcoded to a model name:

- **Extraction tier** — the work-recap scout and each behavior-trace scout: search-and-quote work. Use the cheapest capable model when model override is permitted; otherwise inherit if suitable.
- **Ceiling tier** — the explainer composition, including its `Check yourself` section. This runs in the main conversation on the orchestrator's model; nothing is dispatched for it.

The scout dispatches below are explicit requests from this skill. If the host permits delegation when the user **or a loaded skill** requests it, proceed without asking again. Respect an unconditional prohibition, actual denial, or missing tool. Use the native OpenCode subagent tool, not a shell-launched agent or another harness.

Resolve model intent from the user's or project's active instructions or live prompt, then any configured route for this scout role, then the default tier. An explicit instruction may name the tier, prompt asset, or dispatched scout. Use the project's active RocketClaw route from `.rocketclaw/config.yaml` and `.rocketclaw/config.local.yaml`, if set; `config.example.yml` describes available settings, not active choices. Where a model override is permitted, use `opencode.models` to discover the exact available provider/model ID and pass it through the native tool. Permission to delegate is not permission to choose a model: omit the model argument when overrides are forbidden or unsupported, and inherit when suitable. Disclose any unmet fixed route; inherited or inline work cannot stand in for a required distinct model.

**Degradation rule.** Check effective OpenCode `experimental.subagent_depth` separately from permission; use `opencode debug paths config` to locate config and check applicable overrides when needed. Classify failures by the actual evidence: exhausted nesting, delegation denial, model argument rejection, and missing native tool are different. Retry concurrency or active-agent-limit backpressure only after a slot frees; correct a malformed invocation only if allowed. For an unsupported model argument, use a permitted inherited route if suitable. Do not retry a denied operation or evade a nesting limit. If the scout cannot launch, run its evidence work inline with the same prompt, read budget and dossier, when allowed, and disclose that fallback in one line. If inline cannot satisfy a requirement, report the gap rather than claiming equivalent coverage.

A generic subagent is one whose whole brief is the prompt you send it. When the host's subagent tool makes you name an agent, use only a name you have seen the host list, and list its agents before the first dispatch if you have not. Pick the plain one that adds no role of its own, which still counts as a generic subagent. Never pick a specialist, such as a reviewer or worker agent, whose own role prompt, output format, or tool limits would replace or narrow your prompt.

## Run directory

Create `$RUN_DIR` with this block before writing an artifact or a scout dossier. First set `workspace_root` to the absolute target root from `jj workspace root`; verify `.tmp/` is ignored there before writing. If truly outside JJ, use the absolute local working directory instead. A failure to identify the root of a repository-backed run is a blocker, not a reason to use global storage. The block rejects symlinks or scratch directories owned by another user:

```bash
case "$workspace_root" in /*) ;; *) exit 1 ;; esac
SCRATCH_ROOT="${workspace_root%/}/.tmp/rocketclaw/ce-explain"
for dir in "${workspace_root%/}/.tmp" "${workspace_root%/}/.tmp/rocketclaw" "$SCRATCH_ROOT"; do
  if [ -L "$dir" ] || ! (umask 077; mkdir -p -- "$dir") ||
     [ -L "$dir" ] || [ ! -d "$dir" ] || [ ! -O "$dir" ] || [ ! -w "$dir" ]; then
    printf 'Unsafe or unwritable scratch directory: %s\n' "$dir" >&2
    exit 1
  fi
done
chmod 700 -- "$SCRATCH_ROOT" || exit 1
RUN_DIR=$(umask 077; mktemp -d "$SCRATCH_ROOT/$(date +%Y%m%d)-XXXXXX") || exit 1
printf '%s\n' "$RUN_DIR"
```

## Repository evidence commands

Run JJ from the target's absolute workspace root, not from a nested directory or with `-R` in place of changing directory. For rationale, scope `jj log -r '::<verified-history-head>' -- <path>` to the intended history and read relevant full descriptions with `jj log --no-graph -r <commit-id> -T 'description ++ "\n"'`. See the [JJ CLI reference](https://docs.jj-vcs.dev/latest/cli-reference/) and [revset reference](https://docs.jj-vcs.dev/latest/revsets/).

For a permitted repository-scoped `gh` query, enter the same workspace and obtain its backend path before calling `gh`, e.g. `(cd "$workspace_root" && GIT_DIR=$(jj git root) && GIT_DIR="$GIT_DIR" gh pr view "$pr_number")`. If the root lookup fails, do not issue the query against a different repository; use an otherwise allowed PR interface or report the gap.

## Grounding by input shape

**Repo-touching inputs** (a concept with footprint in this repo, a diff, a recap): use the project's active instructions already in context and go directly to the diff, call-sites, current source, or commits. Read `CONCEPTS.md` when canonical vocabulary matters. If the topic cannot be scoped from the input and existing context, allow one targeted root or workspace probe.

**Diff mode:** resolve the change (the `diff:` ref, or the most recent substantial change when the request points at one implicitly) and gather its evidence — the diff itself, the files it touches, any plan or solution doc that motivated it. Use `jj show <verified-id>` for a single change or `jj diff --from <verified-base> --to <verified-head>` for a verified endpoint comparison. For a PR, verify its actual base and head and use the review range; if those commits are unavailable locally, use permitted exact PR evidence or report the gap. **Empty range** or missing subject: do not silently explain something else. Report that before explaining an adjacent thing. Use a substitute only when the request permits it or the user agrees; name the substitution in the result and artifact `Subject` when present. Otherwise return the unresolved scope to the caller.

**Recap mode:** Do not pre-scan, count, or characterize the window in the main conversation. Instead dispatch a generic OpenCode subagent at the extraction tier, seeded with `references/agents/work-recap-scout.md` and passed the resolved calendar window or requested since-ref, intended history scope, absolute workspace root, and `$RUN_DIR`. Pass any resolved artifact path the scout needs, not the docs configuration. It returns an evidence summary with commit IDs and `file:line` pointers, and writes `recap-evidence.md`. **Empty window:** report the absence of activity and finish without an explainer artifact. If dispatch cannot start, follow the degradation rule above. An inline scout uses the same sources and budgets, still writes `recap-evidence.md` when there is evidence, and forms no view of the window until the evidence pass is done.

**External concepts** (no footprint in this repo): skip repo grounding entirely — do not force repo context into the output. Research with whatever web tools are reachable. When none are, you may explain from model knowledge, but label that content **Unverified — from model knowledge, not checked against current sources** in the response or artifact metadata.

**Idea mode:** the idea is a fixed given. Explain its implications, mechanics, and trade-offs for the user's understanding. Never scope it (`ce-brainstorm`'s job), never generate and rank alternatives (`ce-ideate`'s job).

## Behavior and rationale

For a how question, trace the relevant trigger through its state changes, ownership boundaries, and effect. Inspect actual source and relevant tests; a filename or conversation claim does not establish behavior. Preserve the conditions and failure paths that matter to the requested use.

One pass is enough when that trace can name those boundaries without hand-waving. When one pass cannot, split the question into one slice per ownership boundary the answer depends on and dispatch a behavior-trace scout for each slice. Read `references/agents/behavior-trace-scout.md` and seed a generic subagent at the extraction tier with the question, its slice, and a distinct dossier path under `$RUN_DIR`. Dispatch the slices together. Two slices is the smallest split. More than four means the question is still unscoped: narrow it and trace again rather than adding scouts. Read each dossier from its path, and reconcile overlap or contradiction by reading the source. A gist is not the trace.

For a why question, look for the decision record: motivating docs, comments, JJ history, PR discussions, or linked issues. Follow evidence to available sources when the local record cannot answer the question, within the request's source restrictions. Access to team chat is not permission to search it when the calling workflow makes that opt-in. Expand investigation to resolve material gaps, not to satisfy a source quota.

Code shows behavior, not necessarily intent. Cite documented reasons separately from supported inferences; report contradictions and unknowns. A missing search result does not prove there was no reason. Establish whether a historical constraint still applies before presenting it as a current requirement. When the explanation informs a change, make the relevant constraints and unresolved risks usable by that next step without selecting an approach for it.
