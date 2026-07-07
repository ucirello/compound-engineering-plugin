import { describe, expect, test } from "bun:test"
import { spawnSync } from "node:child_process"
import {
  mkdtempSync,
  writeFileSync,
  readFileSync,
  mkdirSync,
  renameSync,
} from "node:fs"
import { tmpdir } from "node:os"
import path from "node:path"

// The cache helper is byte-duplicated per consuming skill (parity-guarded in
// repo-profile-cache-parity.test.ts). Behavior is identical, so exercise the
// canonical ce-pov copy here.
const SCRIPT = path.join(
  __dirname,
  "../skills/ce-pov/scripts/repo-profile-cache.py",
)

function run(
  cwd: string,
  ...args: string[]
): { code: number; stdout: string; stderr: string } {
  const r = spawnSync("python3", [SCRIPT, ...args], { cwd, encoding: "utf8" })
  return {
    code: r.status ?? -1,
    stdout: r.stdout ?? "",
    stderr: r.stderr ?? "",
  }
}

function jj(cwd: string, ...args: string[]): string {
  const r = spawnSync("jj", args, { cwd, encoding: "utf8" })
  if (r.status !== 0) {
    throw new Error(`jj ${args.join(" ")} failed: ${r.stderr}`)
  }
  return r.stdout ?? ""
}

/** Fresh JJ repo with a manifest + README, one described change. */
function makeRepo(): string {
  const dir = mkdtempSync(path.join(tmpdir(), "repo-profile-"))
  jj(dir, "git", "init")
  writeFileSync(
    path.join(dir, "package.json"),
    '{"name":"x","version":"1.0.0"}\n',
  )
  writeFileSync(path.join(dir, "README.md"), "# x\n")
  jj(dir, "commit", "-m", "init")
  return dir
}

/** A full, valid agnostic profile — `put` now requires every top-level key. */
const VALID_PROFILE = {
  stack: { languages: ["bun"] },
  dependencies: { top_level: [], project_license: "MIT" },
  topology: { monorepo: false, module_layout: "src/" },
  conventions: { testing: "bun test" },
  vocabulary: { concepts_present: false, terms: [] },
}

/** Write a profile JSON file and `put` it; return the cache path. */
function putProfile(dir: string, profile: object = VALID_PROFILE): string {
  const profileFile = path.join(dir, "profile.json")
  writeFileSync(profileFile, JSON.stringify(profile))
  const res = run(dir, "put", profileFile)
  expect(res.code).toBe(0)
  return res.stdout.trim()
}

function getHitProfile(stdout: string): unknown {
  const nl = stdout.indexOf("\n")
  return JSON.parse(stdout.slice(nl + 1).trim())
}

describe("repo-profile-cache helper", () => {
  test("fresh repo with no entry → MISS + a cache path under /tmp", () => {
    const dir = makeRepo()
    const res = run(dir, "get")
    expect(res.code).toBe(0)
    expect(res.stdout.startsWith("MISS\n")).toBe(true)
    const writePath = res.stdout.split("\n")[1]
    expect(writePath).toContain("/compound-engineering/repo-profile/")
    expect(writePath.endsWith(".json")).toBe(true)
  })

  test("put then get (clean tree) → HIT with the stored profile", () => {
    const dir = makeRepo()
    putProfile(dir)
    const res = run(dir, "get")
    expect(res.code).toBe(0)
    expect(res.stdout.startsWith("HIT\n")).toBe(true)
    expect(getHitProfile(res.stdout)).toEqual(VALID_PROFILE)
  })

  test("dirty NON-input file (untracked source) stays HIT", () => {
    const dir = makeRepo()
    putProfile(dir)
    mkdirSync(path.join(dir, "src"))
    writeFileSync(path.join(dir, "src", "app.js"), "console.log(1)\n")
    const res = run(dir, "get")
    expect(res.stdout.startsWith("HIT\n")).toBe(true)
  })

  test("modified manifest → MISS (cardinal-rule input guard)", () => {
    const dir = makeRepo()
    putProfile(dir)
    writeFileSync(
      path.join(dir, "package.json"),
      '{"name":"x","version":"2.0.0"}\n',
    )
    const res = run(dir, "get")
    expect(res.stdout.startsWith("MISS\n")).toBe(true)
  })

  test("new UNTRACKED manifest (??) → MISS (untracked-input guard)", () => {
    const dir = makeRepo()
    putProfile(dir)
    mkdirSync(path.join(dir, "packages", "sub"), { recursive: true })
    writeFileSync(
      path.join(dir, "packages", "sub", "package.json"),
      '{"name":"sub"}\n',
    )
    const res = run(dir, "get")
    expect(res.stdout.startsWith("MISS\n")).toBe(true)
  })

  test("new untracked root AGENTS.md (??) → MISS", () => {
    const dir = makeRepo()
    putProfile(dir)
    writeFileSync(path.join(dir, "AGENTS.md"), "# rules\n")
    const res = run(dir, "get")
    expect(res.stdout.startsWith("MISS\n")).toBe(true)
  })

  test("schema-version mismatch → MISS", () => {
    const dir = makeRepo()
    const cachePath = putProfile(dir)
    const doc = JSON.parse(readFileSync(cachePath, "utf8"))
    doc.profile_schema_version = "0"
    writeFileSync(cachePath, JSON.stringify(doc))
    const res = run(dir, "get")
    expect(res.stdout.startsWith("MISS\n")).toBe(true)
  })

  test("malformed cache file → MISS (degrades, never raises)", () => {
    const dir = makeRepo()
    const cachePath = putProfile(dir)
    writeFileSync(cachePath, "not json at all")
    const res = run(dir, "get")
    expect(res.code).toBe(0)
    expect(res.stdout.startsWith("MISS\n")).toBe(true)
  })

  test("non-JJ directory → NO-CACHE", () => {
    const dir = mkdtempSync(path.join(tmpdir(), "repo-profile-nogit-"))
    const res = run(dir, "get")
    expect(res.code).toBe(0)
    expect(res.stdout.trim()).toBe("NO-CACHE")
  })

  test("root path component is a deterministic single JJ id", () => {
    const dir = makeRepo()
    const res = run(dir, "get")
    expect(res.code).toBe(0)
    const writePath = res.stdout.split("\n")[1]
    // The root path component must be one JJ id, not a newline-joined pair.
    const rootComponent = writePath.split("/repo-profile/")[1].split("/")[0]
    expect(rootComponent).toMatch(/^[a-z0-9]+$/)
  })

  test("put rejects a non-object / empty / partial profile → not cached", () => {
    // empty, non-object, AND partial / wrapper objects missing required keys
    // (a profiler failure that still returns JSON must not be cached + served)
    const bad = ["{}", '"oops"', "[]", "42", "null", '{"stack":{}}', '{"oops":"x"}']
    for (const garbage of bad) {
      const dir = makeRepo()
      const f = path.join(dir, "bad.json")
      writeFileSync(f, garbage)
      const put = run(dir, "put", f)
      expect(put.code).toBe(0)
      expect(put.stdout.trim()).toBe("NO-CACHE") // refused to persist
      // and nothing was cached, so a subsequent get is a MISS, not a HIT
      const get = run(dir, "get")
      expect(get.stdout.startsWith("MISS\n")).toBe(true)
    }
  }, 30000)

  test("put refuses a profile derived from a dirty tree (revert-staleness guard)", () => {
    const dir = makeRepo()
    // dirty a profile input, then derive + put while dirty
    writeFileSync(path.join(dir, "package.json"), '{"name":"x","version":"DIRTY"}\n')
    const f = path.join(dir, "profile.json")
    writeFileSync(f, JSON.stringify(VALID_PROFILE))
    expect(run(dir, "put", f).stdout.trim()).toBe("NO-CACHE") // not persisted — dirty
    // revert → clean tree at the same HEAD; must still MISS, not serve the dirty profile
    writeFileSync(path.join(dir, "package.json"), '{"name":"x","version":"1.0.0"}\n')
    expect(run(dir, "get").stdout.startsWith("MISS\n")).toBe(true)
  })

  test("usage error on missing/garbage subcommand → exit 2", () => {
    const dir = makeRepo()
    expect(run(dir).code).toBe(2)
    expect(run(dir, "frobnicate").code).toBe(2)
    expect(run(dir, "put").code).toBe(2) // put with no file
  })
})

describe("repo-profile-cache helper — review-driven invalidation cases", () => {
  test("renaming a profile input AWAY → MISS (both rename endpoints count)", () => {
    const dir = makeRepo()
    putProfile(dir)
    renameSync(path.join(dir, "package.json"), path.join(dir, "pkg.json"))
    const res = run(dir, "get")
    expect(res.stdout.startsWith("MISS\n")).toBe(true)
  })

  test("renaming a NON-input file → stays HIT", () => {
    const dir = makeRepo()
    mkdirSync(path.join(dir, "src"))
    writeFileSync(path.join(dir, "src", "lib.js"), "export const x = 1\n")
    jj(dir, "commit", "-m", "add lib")
    putProfile(dir)
    renameSync(path.join(dir, "src", "lib.js"), path.join(dir, "src", "lib2.js"))
    expect(run(dir, "get").stdout.startsWith("HIT\n")).toBe(true)
  })

  test("nested (subdir) instruction file stays HIT; only root invalidates", () => {
    const dir = makeRepo()
    putProfile(dir)
    mkdirSync(path.join(dir, "sub"))
    writeFileSync(path.join(dir, "sub", "AGENTS.md"), "# nested\n")
    expect(run(dir, "get").stdout.startsWith("HIT\n")).toBe(true)
  })

  test("CI/config prefixes invalidate; non-workflow .github file does not", () => {
    // .cursor/ and .github/workflows/ are profile inputs (MISS)
    for (const p of [".cursor/rules", ".github/workflows/ci.yml"]) {
      const dir = makeRepo()
      putProfile(dir)
      mkdirSync(path.join(dir, path.dirname(p)), { recursive: true })
      writeFileSync(path.join(dir, p), "x\n")
      expect(run(dir, "get").stdout.startsWith("MISS\n")).toBe(true)
    }
    // a .github file NOT under workflows/ is not an input (HIT)
    const dir = makeRepo()
    putProfile(dir)
    mkdirSync(path.join(dir, ".github"))
    writeFileSync(path.join(dir, ".github", "ISSUE_TEMPLATE.md"), "x\n")
    expect(run(dir, "get").stdout.startsWith("HIT\n")).toBe(true)
  }, 30000)

  test("non-JS ecosystem + monorepo + IaC + deploy inputs invalidate", () => {
    for (const p of [
      "App.csproj", // .NET project-file suffix
      "Package.swift", // Swift/iOS
      "go.work", // Go workspace
      "nx.json", // monorepo orchestrator
      "infra.tf", // Terraform (.tf suffix)
      "terraform/main.tf", // Terraform dir prefix
      "k8s/deployment.yaml", // Kubernetes dir prefix
      "Pulumi.yaml", // Pulumi IaC
      ".nvmrc", // runtime version selector
      ".tool-versions", // asdf/mise version selector
      ".cursorrules", // legacy root Cursor rules
      "vercel.json", // deploy descriptor
      ".gitlab-ci.yml", // non-GitHub CI
    ]) {
      const dir = makeRepo()
      putProfile(dir)
      const fp = path.join(dir, p)
      mkdirSync(path.dirname(fp), { recursive: true })
      writeFileSync(fp, "x\n")
      expect(run(dir, "get").stdout.startsWith("MISS\n")).toBe(true)
    }
  }, 30000)

  test("revert of a dirtied input restores the HIT (recompute determinism)", () => {
    const dir = makeRepo()
    const orig = '{"name":"x","version":"1.0.0"}\n'
    putProfile(dir)
    writeFileSync(path.join(dir, "package.json"), '{"name":"x","version":"9"}\n')
    expect(run(dir, "get").stdout.startsWith("MISS\n")).toBe(true)
    writeFileSync(path.join(dir, "package.json"), orig) // revert → clean again
    expect(run(dir, "get").stdout.startsWith("HIT\n")).toBe(true)
  })

  test("cached doc with a non-object profile → MISS (get-side shape guard)", () => {
    const dir = makeRepo()
    const cachePath = putProfile(dir)
    const doc = JSON.parse(readFileSync(cachePath, "utf8"))
    doc.profile = null // externally corrupted / poisoned
    writeFileSync(cachePath, JSON.stringify(doc))
    expect(run(dir, "get").stdout.startsWith("MISS\n")).toBe(true)
  })
})
