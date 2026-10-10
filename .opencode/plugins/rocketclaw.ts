import path from "node:path"
import fs from "node:fs"
import { fileURLToPath } from "node:url"
import { Plugin } from "@opencode/plugin"

const pluginDir = path.dirname(fileURLToPath(import.meta.url))
const skillsDir = path.resolve(pluginDir, "../../skills")

function unquote(value: string) {
  if (value.length < 2) return value
  const quote = value[0]
  if ((quote !== '"' && quote !== "'") || value[value.length - 1] !== quote) return value
  const inner = value.slice(1, -1)
  return quote === '"' ? inner.replace(/\\(["\\])/g, "$1") : inner.replace(/''/g, "'")
}

// Only leading frontmatter contributes metadata, never fenced YAML in the body.
function parseFrontmatter(content: string) {
  const block = content.match(/^---\r?\n([\s\S]*?)\r?\n---/)
  if (!block) return null
  const fields: Record<string, string> = {}
  for (const line of block[1].split(/\r?\n/)) {
    const pair = line.match(/^([A-Za-z][\w-]*):\s*(.*)$/)
    if (pair) fields[pair[1]] = unquote(pair[2].trim())
  }
  return { fields, body: content.slice(block[0].length).replace(/^\r?\n/, "") }
}

function loadSkills() {
  const skills = []
  for (const entry of fs.readdirSync(skillsDir)) {
    const skillPath = path.join(skillsDir, entry, "SKILL.md")
    if (!fs.existsSync(skillPath)) continue
    const parsed = parseFrontmatter(fs.readFileSync(skillPath, "utf8"))
    if (!parsed?.fields.name) continue
    skills.push({
      name: parsed.fields.name,
      description: parsed.fields.description,
      skillPath,
      body: parsed.body,
      suppressed: parsed.fields["user-invocable"] === "false" || parsed.fields.slash === "false",
    })
  }
  return skills
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
        })
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
