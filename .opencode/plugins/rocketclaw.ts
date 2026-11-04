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
      const source = fs.readFileSync(skillPath, "utf8")
      const block = source.match(/^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/)
      if (!block) throw new Error(`Missing skill frontmatter: ${skillPath}`)
      const fields = load(block[1]) as Record<string, unknown>
      if (!fields || typeof fields.name !== "string" || !fields.name.trim()) {
        throw new Error(`Missing skill name: ${skillPath}`)
      }
      return [{
        id: fields.name,
        name: fields.name,
        description: typeof fields.description === "string" ? fields.description : undefined,
        skillPath,
        content: source.slice(block[0].length),
        commandable: fields["user-invocable"] !== false && fields["user-invocable"] !== "false"
          && fields.slash !== false && fields.slash !== "false",
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
          id: skill.id,
          name: skill.name,
          description: skill.description,
          path: skill.skillPath,
          content: skill.content,
        })
      }
    })
    await ctx.command.transform((editor) => {
      for (const skill of skills) {
        if (!skill.commandable) continue
        editor.add({
          name: skill.name,
          description: skill.description,
          execute: async ({ sessionID, prompt, delivery }) => {
            const attached = prompt.skills ?? []
            await ctx.session.prompt({
              ...prompt,
              sessionID,
              text: prompt.text || "",
              skills: attached.some((item) => item.id === skill.name)
                ? attached : [...attached, { id: skill.name }],
              delivery,
            })
          },
        })
      }
    })
  },
})
