import fs from "node:fs"
import path from "node:path"
import { fileURLToPath } from "node:url"
import { Plugin, Skill } from "@opencode/plugin"

const pluginDir = path.dirname(fileURLToPath(import.meta.url))
const skillsDir = path.resolve(pluginDir, "../../skills")

type BundledSkill = {
  name: string
  description?: string
  skillPath: string
  body: string
  suppressed: boolean
  autoinvoke?: boolean
}

function unquote(value: string): string {
  if (value.length < 2) return value
  const quote = value[0]
  if ((quote !== '"' && quote !== "'") || value[value.length - 1] !== quote) return value
  const inner = value.slice(1, -1)
  return quote === '"' ? inner.replace(/\\(["\\])/g, "$1") : inner.replace(/''/g, "'")
}

function parseFrontmatter(content: string): Record<string, string> | null {
  const block = content.match(/^---\r?\n([\s\S]*?)\r?\n---/)
  const yaml = block?.[1]
  if (yaml === undefined) return null
  const fields: Record<string, string> = {}
  for (const line of yaml.split(/\r?\n/)) {
    const pair = line.match(/^([A-Za-z][\w-]*):\s*(.*)$/)
    const key = pair?.[1]
    const raw = pair?.[2]
    if (!key || raw === undefined) continue
    fields[key] = unquote(raw.trim())
  }
  return fields
}

function skillBody(content: string): string {
  const match = content.match(/^---\r?\n[\s\S]*?\r?\n---(?:\r?\n([\s\S]*))?$/)
  return match && match[1] !== undefined ? match[1] : content
}

function loadSkills(): BundledSkill[] {
  let entries: string[]
  try {
    entries = fs.readdirSync(skillsDir)
  } catch {
    return []
  }

  const skills: BundledSkill[] = []
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
      body: skillBody(content),
      suppressed: fields["user-invocable"] === "false",
    }
    if (fields.description) skill.description = fields.description
    if (fields["disable-model-invocation"] === "true") skill.autoinvoke = false
    skills.push(skill)
  }
  return skills
}

export default Plugin.define({
  id: "rocketclaw",
  async setup(ctx) {
    const skills = loadSkills()

    await ctx.permission.hook("evaluate", (event) => {
      if (event.effect !== "ask") return
      event.effect = "deny"
      event.message = "Permission denied. Do not retry this. Try another approach."
    })

    await ctx.skill.transform((editor) => {
      for (const skill of skills) {
        // Runtime Skill.Info requires `path`; published docs currently show `location`.
        editor.add(
          Skill.Info.make({
            id: Skill.ID.make(skill.name),
            name: Skill.Name.make(skill.name),
            ...(skill.description ? { description: skill.description } : {}),
            ...(skill.autoinvoke === false ? { autoinvoke: false } : {}),
            path: Skill.Info.fields.path.make(skill.skillPath),
            content: skill.body,
          }),
        )
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
              skills: alreadyAttached ? attached : [...attached, { id: Skill.ID.make(skill.name) }],
              delivery: input.delivery,
            })
          },
        })
      }
    })
  },
})
