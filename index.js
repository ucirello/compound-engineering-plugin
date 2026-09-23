// Root entrypoint so OpenCode resolves the plugin whether it is installed as a
// package (git/npm) or referenced as a local directory. The implementation
// lives in .opencode/plugins/rocketclaw.ts, which also makes it
// auto-discoverable when this repository itself is opened as a project.
export { default } from "./.opencode/plugins/rocketclaw.ts"
