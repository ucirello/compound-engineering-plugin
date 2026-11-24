import path from "node:path"
import fs from "node:fs"
import { fileURLToPath } from "node:url"
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
function parseFrontmatter(block: string) {
  const fields: Record<string, string> = {}
  for (const line of block.split(/\r?\n/)) {
    const pair = line.match(/^([A-Za-z][\w-]*):\s*(.*)$/)
    if (pair) fields[pair[1]] = unquote(pair[2].trim())
  }
  return fields
}

// Skills and commands share the same package inventory.
function loadSkills() {
  const skills = []
  let entries
  try {
    entries = fs.readdirSync(skillsDir)
  } catch {
    return skills
  }
  for (const entry of entries) {
    const skillPath = path.join(skillsDir, entry, "SKILL.md")
    let content
    try {
      content = fs.readFileSync(skillPath, "utf8")
    } catch {
      continue
    }
    const block = content.match(/^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/)
    if (!block) continue
    const fields = parseFrontmatter(block[1])
    if (!fields.name) continue
    const body = content.slice(block[0].length)
    skills.push({
      id: Skill.ID.make(fields.name),
      name: Skill.Name.make(fields.name),
      description: fields.description,
      skillPath: Skill.Info.fields.path.make(skillPath),
      body,
      manual: fields["disable-model-invocation"] === "true",
      suppressCommand: fields["user-invocable"] === "false" || fields.slash === "false",
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
          id: skill.id,
          name: skill.name,
          ...(skill.description ? { description: skill.description } : {}),
          ...(skill.manual ? { autoinvoke: false } : {}),
          path: skill.skillPath,
          content: skill.body,
        })
      }
    })

    await ctx.command.transform((editor) => {
      for (const skill of skills) {
        if (skill.suppressCommand) continue
        editor.add({
          name: skill.name,
          ...(skill.description ? { description: skill.description } : {}),
          execute: async ({ sessionID, prompt, delivery }) => {
            const attached = prompt.skills ?? []
            await ctx.session.prompt({
              ...prompt,
              sessionID,
              text: prompt.text || "",
              skills: attached.some((item) => item.id === skill.id) ? attached : [...attached, { id: skill.id }],
              delivery,
            })
          },
        })
      }
    })
  },
})
