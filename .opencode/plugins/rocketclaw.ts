import { Plugin } from "@opencode/plugin"
import fs from "node:fs"
import path from "node:path"
import { fileURLToPath } from "node:url"
import { load } from "js-yaml"

const skillsDir = fileURLToPath(new URL("../../skills/", import.meta.url))

function loadSkills() {
  return fs.readdirSync(skillsDir, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .sort((a, b) => a.name.localeCompare(b.name))
    .flatMap((entry) => {
      const skillPath = path.join(skillsDir, entry.name, "SKILL.md")
      if (!fs.existsSync(skillPath)) return []
      const content = fs.readFileSync(skillPath, "utf8")
      const block = content.match(/^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/)
      if (!block) throw new Error(`Missing skill frontmatter: ${skillPath}`)
      const fields = load(block[1]) as Record<string, unknown>
      if (!fields || typeof fields.name !== "string" || !fields.name.trim()) {
        throw new Error(`Missing skill name: ${skillPath}`)
      }
      return [{
        name: fields.name,
        description: typeof fields.description === "string" ? fields.description : undefined,
        skillPath,
        body: content.slice(block[0].length),
        suppressed: fields["user-invocable"] === false || fields["user-invocable"] === "false"
          || fields.slash === false || fields.slash === "false",
      }]
    })
}

export default Plugin.define({
  id: "rocketclaw",
  async setup(ctx) {
    const skills = loadSkills()
    const names = new Set<string>()
    for (const skill of skills) {
      if (names.has(skill.name)) throw new Error(`Duplicate skill name: ${skill.name}`)
      names.add(skill.name)
    }

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
