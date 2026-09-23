import path from "node:path"
import fs from "node:fs"
import { fileURLToPath } from "node:url"
import { Plugin, Skill } from "@opencode/plugin"

const pluginDir = path.dirname(fileURLToPath(import.meta.url))
const skillsDir = path.resolve(pluginDir, "../../skills")

type LoadedSkill = {
  id: Skill.ID
  name: Skill.Name
  description?: string
  skillPath: Skill.Info["path"]
  content: string
  commandable: boolean
  autoinvoke: boolean
}

function unquote(value: string): string {
  if (value.length < 2) return value
  const quote = value[0]
  if ((quote !== '"' && quote !== "'") || value[value.length - 1] !== quote) return value
  const inner = value.slice(1, -1)
  return quote === '"' ? inner.replace(/\\(["\\])/g, "$1") : inner.replace(/''/g, "'")
}

// Only leading frontmatter contributes metadata, never YAML examples in the body.
function parseFrontmatter(content: string): Record<string, string> | null {
  const block = content.match(/^---\r?\n([\s\S]*?)\r?\n---/)
  if (!block?.[1]) return null
  const fields: Record<string, string> = {}
  for (const line of block[1].split(/\r?\n/)) {
    const pair = line.match(/^([A-Za-z][\w-]*):\s*(.*)$/)
    if (pair?.[1]) fields[pair[1]] = unquote((pair[2] ?? "").trim())
  }
  return fields
}

function loadSkills(): LoadedSkill[] {
  const skills: LoadedSkill[] = []
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
    const block = content.match(/^---\r?\n([\s\S]*?)\r?\n---/)
    const fields = parseFrontmatter(content)
    if (!block || !fields?.name) continue
    skills.push({
      id: Skill.ID.make(entry),
      name: Skill.Name.make(fields.name),
      description: fields.description,
      skillPath: Skill.Info.fields.path.make(skillPath),
      content: content.slice(block[0].length).replace(/^\r?\n/, ""),
      commandable: fields["user-invocable"] !== "false" && fields.slash !== "false",
      autoinvoke: fields["disable-model-invocation"] !== "true",
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
        editor.add(Skill.Info.make({
          id: skill.id,
          name: skill.name,
          description: skill.description,
          autoinvoke: skill.autoinvoke,
          path: skill.skillPath,
          content: skill.content,
        }))
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
              skills: attached.some((item) => item.id === skill.id)
                ? attached
                : [...attached, { id: skill.id }],
              delivery,
            })
          },
        })
      }
    })
  },
})
