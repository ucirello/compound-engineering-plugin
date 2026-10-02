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

// Load every bundled skill once for both skill and command registrations.
function loadSkills() {
  const skills = []
  let entries
  try {
    entries = fs.readdirSync(skillsDir)
  } catch {
    return skills
  }
  for (const entry of entries) {
    let content
    try {
      content = fs.readFileSync(path.join(skillsDir, entry, "SKILL.md"), "utf8")
    } catch {
      continue
    }
    const block = content.match(/^---\r?\n([\s\S]*?)\r?\n---/)
    const fields = parseFrontmatter(content)
    if (!block || !fields || !fields.name) continue
    const body = content.slice(block[0].length).replace(/^\r?\n/, "")
    skills.push({
      id: fields.name,
      name: fields.name,
      description: fields.description,
      skillPath: path.join(skillsDir, entry, "SKILL.md"),
      content: body,
      // Honor both supported frontmatter spellings for command suppression.
      commandable: fields["user-invocable"] !== "false" && fields.slash !== "false",
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
          path: skill.skillPath,
          content: skill.content,
          ...(skill.description ? { description: skill.description } : {}),
        })
      }
    })

    await ctx.command.transform((editor) => {
      for (const skill of skills) {
        if (!skill.commandable) continue
        editor.add({
          name: skill.name,
          ...(skill.description ? { description: skill.description } : {}),
          execute: async ({ sessionID, prompt, delivery }) => {
            const attached = prompt.skills ?? []
            const alreadyAttached = attached.some((item) => item.id === skill.id)
            await ctx.session.prompt({
              ...prompt,
              sessionID,
              text: prompt.text || "",
              skills: alreadyAttached ? attached : [...attached, { id: skill.id }],
              delivery,
            })
          },
        })
      }
    })
  },
})
