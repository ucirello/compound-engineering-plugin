import { existsSync, readFileSync } from "fs"
import path from "path"
import { describe, expect, test } from "bun:test"

const SKILL_DIR = path.join(
  process.cwd(),
  "skills/ce-worktree",
)
const SKILL_BODY = readFileSync(path.join(SKILL_DIR, "SKILL.md"), "utf8")

describe("ce-worktree SKILL.md", () => {
  // Issue #946: ce-worktree was re-architected from a script-based creator into
  // a portable isolation guardrail. There must be no bundled script (it was the
  // root cause of the #943/#764 path-resolution bug class) and no dependence on
  // ${CLAUDE_SKILL_DIR}, so the skill works verbatim on every target.
  test("ships no bundled script and no ${CLAUDE_SKILL_DIR} dependence", () => {
    expect(
      existsSync(path.join(SKILL_DIR, "scripts")),
        "ce-worktree must not bundle a scripts/ directory. A bundled script reintroduces the cross-platform path-resolution bug class (#943/#764).",
    ).toBe(false)
    expect(
      SKILL_BODY.includes("CLAUDE_SKILL_DIR"),
        "ce-worktree/SKILL.md must not reference ${CLAUDE_SKILL_DIR} — the guardrail uses inline commands only, so it resolves on every platform without a skill-dir variable.",
    ).toBe(false)
    expect(
      SKILL_BODY.includes("worktree-manager.sh"),
      "ce-worktree/SKILL.md must not reference the removed worktree-manager.sh script.",
    ).toBe(false)
  })

  // The guardrail must be portable to every target, so it must NOT gate itself
  // to Claude only. (Absence of the worktree-manager.sh allowed-tools pin is
  // covered by the whole-file check above.)
  test("is portable: no ce_platforms gate", () => {
    const frontmatter = SKILL_BODY.match(/^---\n([\s\S]*?)\n---/)
    expect(frontmatter, "ce-worktree/SKILL.md must have YAML frontmatter").not.toBeNull()
    expect(
      /^ce_platforms:/m.test(frontmatter![1]),
      "ce-worktree/SKILL.md must not declare `ce_platforms` — the inline-git guardrail is portable to all targets (issue #946).",
    ).toBe(false)
  })

  // The core value of the skill is the isolation-discipline judgment. Guard the
  // three load-bearing behaviors so they cannot silently regress.
  test("detects existing isolation before creating a worktree", () => {
    expect(
      SKILL_BODY.includes("jj workspace list"),
      "ce-worktree/SKILL.md must inspect JJ workspaces to detect existing isolation (Step 0).",
    ).toBe(true)
    expect(
      SKILL_BODY.includes("jj root"),
      "ce-worktree/SKILL.md must anchor workspace paths with `jj root` so subdirectory CWDs are handled correctly.",
    ).toBe(true)
    expect(
      /work in place/i.test(SKILL_BODY),
      "ce-worktree/SKILL.md must instruct the agent to work in place when already isolated, rather than nesting a workspace.",
    ).toBe(true)
  })

  test("prefers the harness's native workspace tool before the JJ fallback", () => {
    expect(
      /native (isolation primitive|workspace tool|workspace primitive)|native primitive/i.test(SKILL_BODY),
      "ce-worktree/SKILL.md must instruct the agent to prefer the harness's native workspace tool before falling back to JJ (avoids phantom state).",
    ).toBe(true)
  })

  test("documents an inline JJ fallback under .worktrees with ignore safety", () => {
    expect(
      SKILL_BODY.includes("jj workspace add"),
      "ce-worktree/SKILL.md must document the inline `jj workspace add` fallback.",
    ).toBe(true)
    expect(
      SKILL_BODY.includes(".worktrees/"),
      "ce-worktree/SKILL.md must ensure `.worktrees/` is ignored before creating a fallback workspace.",
    ).toBe(true)
  })

  // PR #948 review: the fallback's relative `.worktrees/` and ignore-file
  // paths resolve against the agent's CWD, which may be a subdirectory — so the
  // skill must anchor at the repo root first, or it creates `src/.worktrees/...`
  // and edits a subdirectory ignore file instead of the repo-root one.
  test("anchors the JJ fallback at the repo root before using relative paths", () => {
    expect(
      SKILL_BODY.includes('cd "$(jj root)"'),
      "ce-worktree/SKILL.md must `cd \"$(jj root)\"` in the JJ fallback so relative `.worktrees` and ignore paths resolve at the repo root, not a subdirectory CWD.",
    ).toBe(true)
    expect(
      /run from the repo root/i.test(SKILL_BODY),
      "ce-worktree/SKILL.md Step 2 must explicitly instruct running the fallback from the repo root.",
    ).toBe(true)
  })

  // PR #948 review: `jj git fetch --remote origin --branch <branch>` exits with no `origin`
  // remote / a local-only base. The fetch must be non-fatal so the flow
  // continues to the local-ref fallback it claims to handle.
  test("treats the base-branch fetch as best-effort / non-fatal", () => {
    expect(
      /non-fatal|best-effort/i.test(SKILL_BODY),
      "ce-worktree/SKILL.md must mark the `jj git fetch` step non-fatal so an absent `origin` remote falls through to the local base ref instead of aborting.",
    ).toBe(true)
  })

  // PR #948 review: on a sandbox/permission failure the requested isolation was
  // not created. The skill must not silently fall back to the current checkout —
  // the user chose isolation specifically to avoid touching it.
  test("on a sandbox/permission failure, asks rather than silently using the current checkout", () => {
    expect(
      /work in the current (directory|checkout|workspace) instead/i.test(SKILL_BODY),
      "ce-worktree/SKILL.md must not instruct the agent to silently work in the current workspace on a sandbox failure — that defeats the isolation contract.",
    ).toBe(false)
    // The confirmation is blocking, so it must route through the platform's
    // blocking-question tool (AGENTS.md > Cross-Platform User Interaction),
    // not a vague "ask the user" that can degrade to a non-blocking prompt.
    expect(
      SKILL_BODY.includes("AskUserQuestion") && SKILL_BODY.includes("request_user_input"),
      "ce-worktree/SKILL.md must route the sandbox-failure confirmation through the platform's blocking question tool (name AskUserQuestion / request_user_input / ask_user), per AGENTS.md > Cross-Platform User Interaction, rather than a non-blocking 'ask the user'.",
    ).toBe(true)
  })
})
