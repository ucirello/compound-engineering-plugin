import path from "path"
import fs from "fs"
import { fileURLToPath } from "url"
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

function skillBody(content: string) {
  const block = content.match(/^---\r?\n[\s\S]*?\r?\n---(?:\r?\n|$)/)
  if (!block) return content
  return content.slice(block[0].length)
}

type LoadedSkill = {
  name: string
  description?: string
  suppressed: boolean
  skillPath: string
  body: string
}

function loadSkills(): LoadedSkill[] {
  const loaded: LoadedSkill[] = []
  let entries
  try {
    entries = fs.readdirSync(skillsDir)
  } catch {
    return loaded
  }
  for (const entry of entries) {
    const skillPath = path.join(skillsDir, entry, "SKILL.md")
    let content
    try {
      content = fs.readFileSync(skillPath, "utf8")
    } catch {
      continue
    }
    const fields = parseFrontmatter(content)
    if (!fields || !fields.name) continue
    const skill: LoadedSkill = {
      name: fields.name,
      suppressed: fields["user-invocable"] === "false",
      skillPath,
      body: skillBody(content),
    }
    if (fields.description) skill.description = fields.description
    loaded.push(skill)
  }
  return loaded
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
          location: skill.skillPath,
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
