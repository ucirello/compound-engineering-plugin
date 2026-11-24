# Native peer recovery and terminal classification

The dispatch context owns every recovery and the final attested receipt. Keep
the captured base/head, read-only permissions, brief, and shared deadline fixed.
No replacement procedure bypasses a permission decision, actual depth limit,
missing tool, or recipient restriction.

- **Ineligible or no launch:** record why (disabled, remote scope, denied
  permission, missing tool, depth, no distinct provider, or unsupported fixed
  model/effort). A denied launch is not retried. Use the normal adversarial
  subagent if independently permitted and it can satisfy that role; same
  serving family is not cross-model coverage. If a fixed or different-model
  pass was requested, say explicitly that this coverage is incomplete even
  if the ordinary fallback reviewed the code.
- **Recoverable native infrastructure error:** if the native dispatcher reports
  a transient error, retry the identical route only for a new, plausibly
  recoverable failure within the original deadline. Stop at a repeated
  failure or exhausted budget. An acknowledged attempt must first reach a
  terminal state or be cancelled; never launch a duplicate concurrent peer.
  Recover prelaunch errors before settling the ordinary roster. If an
  acknowledged launch fails and its same-route recovery is exhausted, report
  the adversarial lens as degraded unless a permitted fallback covered it.
- **Provider overload (529):** retry the identical sanctioned route once, within
  budget. **Model unavailable/rejected before sending:** only an editorial
  default may use the allowed same-family alternate from the model table;
  a fixed model/effort remains incomplete. A default Codex effort rejection
  can retry once at default effort and record it unverified.
- **Transient provider rate limit or turn-budget exhaustion:** after the
  one allowed overload retry, if applicable, restore the permitted ordinary
  persona; do not start another provider to avoid that limit.
- **Session/usage quota or route-specific unavailability with a proven
  no-review outcome:** do not repeat that route. If no fixed route was
  specified, allow one different eligible native route, selected under the
  original policy, re-sanctioned and disclosed before dispatch. No third
  peer. If unavailable, restore the permitted ordinary persona.
- **Authentication:** attribute a login/credential failure to the provider
  only if native evidence shows provider-capable dispatch. Otherwise report
  an execution-context failure, not a sign-out. When the peer did not
  review, apply the permitted no-review fallback.
- **Did not run:** a no-start/no-execution failure may fall back to the ordinary
  adversarial reviewer when permitted, after bounded recovery is exhausted.
  **Ran but no usable output:** record malformed, timed-out, or unusable
  output distinctly; full review reports the lens degraded/not run as
  appropriate rather than pretending another persona covered it. Focused
  review may take its one permitted fallback under `depth-paths.md`. Do not
  redo a usable peer review with the local persona.

Record whether the result was `folded`, `in-process-fallback`, `not-run`,
`no-usable-output`, or `failed`, with the actual reason and coverage. A valid
empty result is not a no-run condition. Use `adversarial lens: in-process fallback (cross-model peer not run: <reason>)`
for a no-run fallback; `harness-native fallback` is reserved for a
different workflow that bypasses this skill. Bring native launches to a terminal
state or stop them before handing off; if stopping cannot be verified, say so
and do not return a successful collection receipt. Finish leaves never launch
or collect peer work.
