import { readFileSync, readdirSync } from "node:fs"
import { dirname, join, resolve } from "node:path"
import { fileURLToPath } from "node:url"
import { Plugin } from "@opencode/plugin"
import yaml from "js-yaml"

const skillsDir = resolve(dirname(fileURLToPath(import.meta.url)), "../../skills")

function loadSkills() {
  const skills = []
  for (const entry of readdirSync(skillsDir).sort()) {
    const path = join(skillsDir, entry, "SKILL.md")
    let content: string
    try {
      content = readFileSync(path, "utf8")
    } catch (error) {
      const code = (error as NodeJS.ErrnoException).code
      if (code === "ENOENT" || code === "ENOTDIR") continue
      throw error
    }

    const block = content.match(/^---[ \t]*\r?\n([\s\S]*?)\r?\n---[ \t]*(?:\r?\n|$)/)
    if (!block) continue
    const fields = yaml.load(block[1]) as Record<string, unknown> | undefined
    if (typeof fields?.name !== "string" || !fields.name) continue

    skills.push({
      name: fields.name,
      description: typeof fields.description === "string" ? fields.description : undefined,
      path,
      body: content.slice(block[0].length),
      commandable: ![fields.slash, fields["user-invocable"]].some(
        (value) => value === false || value === "false",
      ),
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
          path: skill.path,
          content: skill.body,
        } as Parameters<typeof editor.add>[0])
      }
    })

    await ctx.command.transform((editor) => {
      for (const skill of skills) {
        if (!skill.commandable) continue
        editor.add({
          name: skill.name,
          ...(skill.description ? { description: skill.description } : {}),
          execute: async ({ prompt, sessionID, delivery }) => {
            const attached = prompt.skills ?? []
            await ctx.session.prompt({
              ...prompt,
              sessionID,
              text: prompt.text ?? "",
              skills: attached.some((item) => item.id === skill.name)
                ? attached
                : [...attached, { id: skill.name }],
              delivery,
            })
          },
        })
      }
    })
  },
})
