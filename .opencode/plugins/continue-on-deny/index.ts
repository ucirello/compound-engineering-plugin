export default {
  id: "continue-on-deny",
  async setup(ctx) {
    await ctx.permission.hook("evaluate", (event) => {
      if (event.effect !== "ask") return
      event.effect = "deny"
      event.message = "Permission denied. Do not retry this. Try another approach."
    })
  },
}
