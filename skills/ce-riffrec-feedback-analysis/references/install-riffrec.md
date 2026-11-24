# Setup: Add Riffrec to a project

Use this path when the user has no recording yet and wants to start capturing product feedback with [Riffrec](https://github.com/kieranklaassen/riffrec).

Riffrec is a browser-based capture tool that records the screen, microphone audio, console output, network requests, and DOM events into a single `riffrec-*.zip` bundle. The bundle is what this skill consumes downstream.

## What to tell the user

1. Riffrec lives at <https://github.com/kieranklaassen/riffrec>. Refer them to the README for the current install command — it is the source of truth and may change.
2. The general shape of integration:
   - Add the Riffrec capture script or package to the project's web app.
   - Wire a "Record feedback" affordance somewhere accessible during real use (a bug report button, a dev-only floating recorder, or a keyboard shortcut).
   - Confirm a sample session ends with a downloadable `riffrec-*.zip`.
3. Once a zip exists, the user runs this skill again with the zip path. The skill will pick the **quick bug report** or **extensive analysis** path automatically based on length and content.

Riffrec capture does not require OpenCode. To use RocketClaw's deep delegation in OpenCode V2 for downstream analysis, merge `"experimental": { "subagent_depth": 3 }` into `~/.config/opencode/opencode.json`. Use `opencode debug paths` or `opencode debug paths config` to locate the actual user config and edit its existing `opencode.json` or `opencode.jsonc` rather than creating a competing file. Preserve unrelated settings, other `experimental` fields, and any existing integer depth above `3`. Do not let a higher-precedence config lower it below `3`. Installing the plugin or relying on its package-local config alone does not enable deep delegation in consuming projects.

## Recommended capture habits

Surface these to the user during setup so the recordings they share later are easy to analyze:

- Speak the issue out loud while reproducing it. The transcript is the single highest-signal artifact.
- Click the affected UI even when it does nothing — failed clicks are the strongest signal in event extraction.
- Keep recordings focused. Many short clips beat one long one when issues are unrelated.
- Note when a step is intentional vs. accidental ("oops, that wasn't what I meant"). The analyzer cannot infer intent.

## After install

When the user returns with their first zip, route to `references/quick-bug-report.md` or `references/extensive-analysis.md` per the SKILL.md routing rules. Do not run the analyzer in the setup path — there is nothing to analyze yet.
