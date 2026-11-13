import { Plugin } from "@opencode/plugin"
import { readdir, readFile } from "node:fs/promises"
import path from "node:path"
import { fileURLToPath } from "node:url"
import { load } from "js-yaml"

const skillsDir = fileURLToPath(new URL("../../skills/", import.meta.url))

async function loadSkills() {
  const skills = []
  for (const entry of await readdir(skillsDir, { withFileTypes: true })) {
    if (!entry.isDirectory()) continue
    const skillPath = path.join(skillsDir, entry.name, "SKILL.md")
    let content: string
    try {
      content = await readFile(skillPath, "utf8")
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code === "ENOENT") continue
      throw error
    }
    const block = content.match(/^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/)
    if (!block) throw new Error(`Missing skill frontmatter: ${skillPath}`)
    const fields = load(block[1]) as Record<string, unknown>
    if (!fields || typeof fields.name !== "string" || !fields.name.trim()) {
      throw new Error(`Missing skill name: ${skillPath}`)
    }
    if (skills.some((skill) => skill.name === fields.name)) {
      throw new Error(`Duplicate skill name: ${fields.name}`)
    }
    skills.push({
      name: fields.name,
      description: typeof fields.description === "string" ? fields.description : undefined,
      skillPath,
      body: content.slice(block[0].length),
      suppressed: fields.slash === false || fields.slash === "false"
        || fields["user-invocable"] === false || fields["user-invocable"] === "false",
    })
  }
  return skills
}

export default Plugin.define({
  id: "rocketclaw",
  async setup(ctx) {
    const skills = await loadSkills()
    await ctx.skill.transform((editor) => {
      for (const skill of skills) {
        editor.add({
          id: skill.name,
          name: skill.name,
          ...(skill.description ? { description: skill.description } : {}),
          path: skill.skillPath,
          content: skill.body,
        } as Parameters<typeof editor.add>[0])
      }
    })
    await ctx.command.transform((editor) => {
      for (const skill of skills) {
        if (skill.suppressed) continue
        editor.add({
          name: skill.name,
          ...(skill.description ? { description: skill.description } : {}),
          execute: async (input) => {
            const attached = input.prompt.skills ?? []
            const alreadyAttached = attached.some((item) => item.id === skill.name)
            await ctx.session.prompt({
              ...input.prompt,
              sessionID: input.sessionID,
              text: input.prompt.text || "",
              skills: alreadyAttached ? attached : [...attached, { id: skill.name }],
              delivery: input.delivery,
            })
          },
        })
      }
    })
  },
})
