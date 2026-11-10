import { Plugin } from "@opencode/plugin"
import path from "node:path"
import fs from "node:fs"
import { fileURLToPath } from "node:url"
import { load } from "js-yaml"

const pluginDir = path.dirname(fileURLToPath(import.meta.url))
const skillsDir = path.resolve(pluginDir, "../../skills")

function loadSkills() {
  return fs.readdirSync(skillsDir).sort().flatMap((entry) => {
    const skillPath = path.join(skillsDir, entry, "SKILL.md")
    if (!fs.existsSync(skillPath)) return []
    const content = fs.readFileSync(skillPath, "utf8")
    // Read only leading frontmatter, never YAML examples in the skill body.
    const block = content.match(/^---\r?\n([\s\S]*?)\r?\n---/)
    if (!block) return []
    const fields = load(block[1]) as Record<string, unknown> | undefined
    if (!fields || typeof fields.name !== "string" || !fields.name) return []
    return [{
      name: fields.name,
      description: typeof fields.description === "string" ? fields.description : undefined,
      skillPath,
      body: content.slice(block[0].length).replace(/^\r?\n/, ""),
      suppressed: fields["user-invocable"] === false || fields.slash === false,
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
