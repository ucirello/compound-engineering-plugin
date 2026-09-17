import { Plugin } from "@opencode/plugin"
import fs from "fs"
import path from "path"
import { fileURLToPath } from "url"

const pluginDir = path.dirname(fileURLToPath(import.meta.url))
const skillsDir = path.resolve(pluginDir, "../../skills")

function unquote(value: string) {
  if (value.length < 2) return value
  const quote = value[0]
  if ((quote !== '"' && quote !== "'") || value[value.length - 1] !== quote) return value
  const inner = value.slice(1, -1)
  return quote === '"' ? inner.replace(/\\(["\\])/g, "$1") : inner.replace(/''/g, "'")
}

// Scoped to the leading `---` block so a `name:`/`description:` line inside a
// fenced YAML example in the skill body cannot register a bogus command.
function parseFrontmatter(content: string) {
  const block = content.match(/^---\r?\n([\s\S]*?)\r?\n---/)
  if (!block) return null
  const fields: Record<string, string> = {}
  for (const line of block[1].split(/\r?\n/)) {
    const pair = line.match(/^([A-Za-z][\w-]*):\s*(.*)$/)
    if (pair) fields[pair[1]] = unquote(pair[2].trim())
  }
  return fields
}

type BundledSkill = {
  name: string
  description?: string
  skillPath: string
  body: string
  suppressed: boolean
}

function loadSkills() {
  const skills: BundledSkill[] = []
  let entries: string[]
  try {
    entries = fs.readdirSync(skillsDir)
  } catch {
    return skills
  }
  for (const entry of entries) {
    const skillPath = path.join(skillsDir, entry, "SKILL.md")
    let content: string
    try {
      content = fs.readFileSync(skillPath, "utf8")
    } catch {
      continue
    }
    const fields = parseFrontmatter(content)
    if (!fields || !fields.name) continue
    const skill: BundledSkill = {
      name: fields.name,
      skillPath,
      body: content,
      suppressed: fields["user-invocable"] === "false",
    }
    if (fields.description) skill.description = fields.description
    skills.push(skill)
  }
  return skills
}

const skills = loadSkills()

export default Plugin.define({
  id: "rocketclaw",
  async setup(ctx) {
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
