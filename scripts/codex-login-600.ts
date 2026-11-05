/** Instance-specific auth entry; never starts a gateway or copies OAuth tokens. */
import { loginCodex } from "../src/lib/oauth/codex"
import { persistCodexCredentials } from "../src/lib/token"
import { prompt } from "../src/lib/interactive-prompt"
const callbackTimeoutMs = 600_000
if (!process.env.COPILOT_API_HOME)
  throw new Error("Set COPILOT_API_HOME to the original instance home")
if (process.argv.includes("--check")) {
  console.log(
    JSON.stringify({
      callbackTimeoutMs,
      apiHome: process.env.COPILOT_API_HOME,
      startsGateway: false,
    }),
  )
} else {
  const credentials = await loginCodex({
    callbackTimeoutMs,
    onAuth: ({ url }) => console.log(url),
    onPrompt: (message) =>
      prompt(message, { type: "text" }).then((value) => value ?? ""),
  })
  await persistCodexCredentials(credentials, {
    activateAccount: true,
    enableProvider: true,
  })
  console.log("Codex credentials saved to the original instance home")
}
