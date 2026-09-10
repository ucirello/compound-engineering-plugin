import fs from "fs"
import path from "path"
import { fileURLToPath } from "url"
import { Plugin, Skill } from "@opencode/plugin"

const pluginDir = path.dirname(fileURLToPath(import.meta.url))
const skillsDir = path.resolve(pluginDir, "../../skills")

function unquote(value: string): string {
  if (value.length < 2) return value
  const quote = value[0]
  if ((quote !== '"' && quote !== "'") || value[value.length - 1] !== quote) return value
  const inner = value.slice(1, -1)
  return quote === '"' ? inner.replace(/\\(["\\])/g, "$1") : inner.replace(/''/g, "'")
}

// Scoped to the leading `---` block so a `name:`/`description:` line inside a
// fenced YAML example in the skill body cannot register a bogus command.
function parseFrontmatter(content: string): { fields: Record<string, string>; body: string } | null {
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

type LoadedSkill = {
  name: string
  description?: string
  body: string
  skillPath: string
  suppressed: boolean
  autoinvoke: boolean
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
    const parsed = parseFrontmatter(content)
    if (!parsed || !parsed.fields.name) continue
    skills.push({
      name: parsed.fields.name,
      description: parsed.fields.description,
      body: parsed.body,
      skillPath,
      suppressed: parsed.fields["user-invocable"] === "false",
      autoinvoke: parsed.fields["disable-model-invocation"] !== "true",
    })
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
          slash: false,
          autoinvoke: skill.autoinvoke,
          location: skill.skillPath,
          content: skill.body,
        } as Skill.Info)
      }
    })

    await ctx.command.transform((editor) => {
      for (const skill of skills) {
        if (skill.suppressed) continue
        editor.add({
          name: skill.name,
          ...(skill.description ? { description: skill.description } : {}),
          execute: async ({ sessionID, prompt, delivery }) => {
            const attached = prompt.skills ?? []
            const alreadyAttached = attached.some((item) => item.id === skill.name)
            await ctx.session.prompt({
              ...prompt,
              sessionID,
              text: `Load and execute the \`${skill.name}\` skill.\n\n${prompt.text}`,
              skills: alreadyAttached ? attached : [...attached, { id: skill.name }],
              delivery,
            })
          },
        })
      }
    })
  },
})
