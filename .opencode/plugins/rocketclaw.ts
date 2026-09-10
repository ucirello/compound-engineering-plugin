import fs from "fs"
import path from "path"
import { fileURLToPath } from "url"
import { Plugin, Skill } from "@opencode/plugin"

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
  return {
    fields,
    body: content.slice(block[0].length).replace(/^\r?\n/, ""),
  }
}

function loadSkills() {
  const skills: Array<{
    id: string
    name: string
    description?: string
    userInvocable: boolean
    autoinvoke: boolean
    location: string
    content: string
  }> = []
  let entries
  try {
    entries = fs.readdirSync(skillsDir)
  } catch {
    return skills
  }
  for (const entry of entries) {
    const location = path.join(skillsDir, entry, "SKILL.md")
    let content
    try {
      content = fs.readFileSync(location, "utf8")
    } catch {
      continue
    }
    const parsed = parseFrontmatter(content)
    if (!parsed || !parsed.fields.name) continue
    const fields = parsed.fields
    skills.push({
      id: fields.name,
      name: fields.name,
      description: fields.description,
      userInvocable: fields["user-invocable"] !== "false",
      autoinvoke: fields["disable-model-invocation"] !== "true",
      location,
      content: parsed.body,
    })
  }
  return skills
}

export default Plugin.define({
  id: "rocketclaw",
  async setup(ctx) {
    const skills = loadSkills()
    await ctx.storage.set("loaded", true)
    await ctx.storage.set("skillCount", skills.length)

    await ctx.skill.transform((editor) => {
      for (const skill of skills) {
        const record: Skill.Info = {
          id: skill.id as Skill.Info["id"],
          name: skill.name as Skill.Info["name"],
          description: skill.description,
          slash: skill.userInvocable,
          autoinvoke: skill.autoinvoke,
          location: skill.location as Skill.Info["location"],
          content: skill.content,
        }
        editor.add(record)
      }
    })

    const listed = await ctx.command.list()
    const commands = Array.isArray(listed) ? listed : []
    const existing = new Set(commands.map((command) => command.name))

    await ctx.command.transform((editor) => {
      for (const skill of skills) {
        if (!skill.userInvocable) continue
        if (existing.has(skill.name)) continue
        const name = skill.name
        const description = skill.description
        editor.add({
          name,
          description,
          execute: async ({ sessionID, prompt, delivery }) => {
            await ctx.session.prompt({
              ...prompt,
              sessionID,
              text: `Load and execute the \`${name}\` skill.\n\n${prompt.text}`,
              delivery,
            })
          },
        })
      }
    })
  },
})
