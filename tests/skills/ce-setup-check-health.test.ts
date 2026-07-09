import { copyFile, mkdir, mkdtemp, rm, writeFile } from "fs/promises"
import os from "os"
import path from "path"
import { describe, expect, test } from "bun:test"

const repoRoot = path.join(import.meta.dir, "..", "..")
const checkHealthScript = path.join(repoRoot, "skills", "ce-setup", "scripts", "check-health")
const configTemplate = path.join(repoRoot, "skills", "ce-setup", "references", "config-template.yaml")
const testPath = process.env.PATH ?? "/usr/bin:/bin"

type RunResult = {
  exitCode: number
  stdout: string
  stderr: string
}

async function runCheckHealth(cwd: string, pathValue: string): Promise<RunResult> {
  const proc = Bun.spawn(["bash", checkHealthScript], {
    cwd,
    env: {
      ...process.env,
      HOME: cwd,
      PATH: pathValue,
    },
    stderr: "pipe",
    stdout: "pipe",
  })

  const [exitCode, stdout, stderr] = await Promise.all([
    proc.exited,
    new Response(proc.stdout).text(),
    new Response(proc.stderr).text(),
  ])

  return { exitCode, stdout, stderr }
}

async function initJjRepo(root: string): Promise<void> {
  await Bun.$`jj git init --colocate`.cwd(root).quiet()
}

describe("ce-setup check-health", () => {
  test("reports missing optional tools without treating them as setup failures", async () => {
    const root = await mkdtemp(path.join(os.tmpdir(), "ce-setup-health-"))

    try {
      const result = await runCheckHealth(root, testPath)

      expect(result.exitCode).toBe(0)
      expect(result.stdout).toContain("Optional capabilities")
      expect(result.stdout).toContain("Missing optional tools do not block setup")
    } finally {
      await rm(root, { recursive: true, force: true })
    }
  })

  test("reports a healthy repo config when local config is ignored by JJ and example is current", async () => {
    const root = await mkdtemp(path.join(os.tmpdir(), "ce-setup-health-"))

    try {
      await initJjRepo(root)
      await mkdir(path.join(root, ".compound-engineering"), { recursive: true })
      await copyFile(configTemplate, path.join(root, ".compound-engineering", "config.local.example.yaml"))
      await copyFile(configTemplate, path.join(root, ".compound-engineering", "config.local.yaml"))
      await writeFile(path.join(root, ".gitignore"), ".compound-engineering/*.local.yaml\n")

      const result = await runCheckHealth(root, testPath)

      expect(result.exitCode).toBe(0)
      expect(result.stdout).toContain("Project config")
      expect(result.stdout).toContain("Local config is ignored by jj")
      expect(result.stdout).toContain("Project config healthy")
    } finally {
      await rm(root, { recursive: true, force: true })
    }
  })

  test("reports unignored local config as a project issue", async () => {
    const root = await mkdtemp(path.join(os.tmpdir(), "ce-setup-health-"))

    try {
      await initJjRepo(root)
      await mkdir(path.join(root, ".compound-engineering"), { recursive: true })
      await copyFile(configTemplate, path.join(root, ".compound-engineering", "config.local.example.yaml"))
      await copyFile(configTemplate, path.join(root, ".compound-engineering", "config.local.yaml"))

      const result = await runCheckHealth(root, testPath)

      expect(result.exitCode).toBe(0)
      expect(result.stdout).toContain("Local config is not safely ignored")
      expect(result.stdout).toContain("1 project issue(s) found")
    } finally {
      await rm(root, { recursive: true, force: true })
    }
  })
})
