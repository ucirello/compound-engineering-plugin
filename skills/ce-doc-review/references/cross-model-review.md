# Native cross-model document review

Run this additive, read-only pass only for activated adversarial, product-lens,
and security-lens reviewers. Include one full-document `whole-doc` sweep in the
same wave; it has no local twin. Use native OpenCode subagents, never another
harness CLI or a dispatch bridge. Follow `dispatch.md` permission and depth rules.

Resolve the absolute workspace root with JJ, or use the document's local working
directory outside a repository. Read ordinary settings from
`.rocketclaw/config.local.yaml`, then `config.yaml`, first valid value winning;
retain `config.example.yaml` model/tier choices as documented defaults, not a
third active layer. `cross_model_review_mode: off` disables this pass unless the
user explicitly requests it. A live prohibition wins. Respect `CROSS_MODEL_PEERS`
when set; unset is unfiltered, not a new authorization requirement.

Discover available models using `opencode.models`; resolve conversation choices
before `cross_model_peer`, `cross_model_model`, and `cross_model_effort`, then
documented defaults. Preserve configured choices and tiers. Compatibility target
names (codex, claude, grok, composer, cursor, antigravity, opencode) identify
preferences only: map to a discovered provider/model, not another harness.
Never silently replace an explicit model or recipient. Where host policy requires
a user model request, configuration alone does not authorize a model override.
Use an inherited reviewer only as non-independent evidence and disclose the
unmet configured route; a required cross-model pass remains incomplete.

Before content is sent, disclose the requested model, effort, native route and
all receiving providers, and that full document content is sent. Non-interactive
runs retain the same egress policy and an audit receipt rather than chat announce.
Unknown serving identity cannot establish independence. Distinct same-model
reviewers are not cross-model independence.

Give each fresh subagent the selected persona, template and schema in full, the
document content, type and origin, and a round-one framing without peer findings
or the accumulated decision primer. Whole-doc uses `personas/whole-doc-reviewer.md`
and the full document. Restrict tools to read-only access to the supplied evidence
using actual native capabilities. If isolation cannot be enforced, report that
limitation; do not claim empty-workspace or tool-less isolation.

Collect a schema-valid `<reviewer-name>-<provider>.json` result plus a receipt:
requested target/model/effort, actual native route, recipient, observed serving
model and identity evidence, status/reason, and `independence_verified`. Store any
artifacts in the absolute target root's `.tmp/rocketclaw/doc-review/` (local
`.tmp/` outside JJ), never global temporary directories. Mark independence true
only for attested different serving families. Requested identity is not proof.
Only verified independence may promote agreement in synthesis.

Bound parallelism by native capacity. Wait for active completions before retrying
capacity errors, with at most one retry per queued reviewer. Retry a transient
overload once on the identical route within the original deadline. Never retry
denial, model rejection, quota or missing tools, and never evade depth limits.
An infrastructure failure may receive one same-route recovery if permissions,
read scope and deadline remain unchanged. Preserve completed receipts, collect
all started reviewers and use only supported lifecycle cleanup.

Report each eligible lens as completed, skipped, failed or timed out with observed
reason, including lost whole-doc coverage. Distinguish disabled policy, missing
tool, depth, capacity, permission denial, model rejection and provider failure;
do not infer account authentication from unverified reviewer prose. Optional
pass failure is non-blocking but remains named in Coverage; an explicitly
required unavailable pass is incomplete. Keep in-process findings, never invent
corroboration. Apply synthesis's ordinary suppression rules to peer findings.
