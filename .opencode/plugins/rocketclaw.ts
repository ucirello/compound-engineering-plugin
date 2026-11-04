import path from "node:path"
import fs from "node:fs"
import { fileURLToPath } from "node:url"
import { Plugin } from "@opencode/plugin"
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
      const fields = load(block[1]) as Record<string, unknown> | undefined
      if (!fields || typeof fields.name !== "string" || !fields.name.trim()) {
        throw new Error(`Missing skill name: ${skillPath}`)
      }
      return [{
        name: fields.name,
        description: typeof fields.description === "string" ? fields.description : undefined,
        skillPath,
        body: content.slice(block[0].length),
        suppressed: fields.slash === false || fields["user-invocable"] === false,
      }]
    })
}

export default Plugin.define({
  id: "rocketclaw",
  async setup(ctx) {
    const skills = loadSkills()
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
