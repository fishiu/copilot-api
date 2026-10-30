/** Build a reproducible experimental overlay onto an official 2.8.2 runtime. */
import { cp, mkdir, readFile, writeFile } from "node:fs/promises"
import { resolve } from "node:path"
const [source, target] = process.argv.slice(2)
if (!source || !target || resolve(source) === resolve(target))
  throw new Error("Use distinct official runtime and private output paths")
await mkdir(target, { recursive: true })
await cp(source, target, { recursive: true })
const result = await Bun.build({
  entrypoints: [
    "src/lib/plaintext-v2.ts",
    "src/lib/plaintext-v2-alpha-forward.ts",
  ],
  target: "bun",
  format: "esm",
  outdir: `${target}/dist`,
  naming: "[name].js",
})
if (!result.success)
  throw new AggregateError(result.logs, "Plaintext V2 helper build failed")
const path = `${target}/dist/server-CI54ZhlD.js`
let text = await readFile(path, "utf8")
function replaceOnce(from: string, to: string) {
  if (text.split(from).length !== 2)
    throw new Error(`Official 2.8.2 anchor mismatch: ${from}`)
  text = text.replace(from, to)
}
text =
  'import { preparePlaintextV2, restorePlaintextV2Response, restorePlaintextV2Chunk } from "./plaintext-v2.js";\n'
  + text
replaceOnce(
  "const handleResponses = async (c) => {\n\tconst payload = await c.req.json();",
  "const handleResponses = async (c) => {\n\tlet payload = await c.req.json();",
)
replaceOnce(
  "\tconst normalizedAgentMessageCount = normalizeGuardianAgentMessages(payload);",
  '\tconst plaintextV2 = preparePlaintextV2(payload, process.env.CAPI_PLAINTEXT_V2_MODELS);\n\tif (plaintextV2.error) return c.json({error:{type:"invalid_request_error",message:plaintextV2.error}},400);\n\tpayload = plaintextV2.payload;\n\tconst normalizedAgentMessageCount = normalizeGuardianAgentMessages(payload);',
)
replaceOnce(
  '\t\t\t\tfor await (const chunk of { [Symbol.asyncIterator]: () => iterator }) {\n\t\t\t\t\tdebugJson(logger$1, "Responses stream chunk:", chunk);',
  '\t\t\t\tfor await (const originalChunk of { [Symbol.asyncIterator]: () => iterator }) {\n\t\t\t\t\tconst chunk = restorePlaintextV2Chunk(originalChunk, plaintextV2.active);\n\t\t\t\t\tdebugJson(logger$1, "Responses stream chunk:", chunk);',
)
replaceOnce(
  "\tconst result = response;\n\trecordUsage({",
  "\tconst result = restorePlaintextV2Response(response, plaintextV2.active);\n\trecordUsage({",
)
replaceOnce(
  "async function handleAlphaSearchRequest(c, resolvedProviderConfig) {",
  "async function handleAlphaSearchRequest(c, resolvedProviderConfig) {\n const localForward = await forwardLocalAlphaSearch(c.req.raw);\n if (localForward) return localForward;",
)
text =
  'import { forwardLocalAlphaSearch } from "./plaintext-v2-alpha-forward.js";\n'
  + text
await writeFile(path, text)
console.log(
  JSON.stringify({
    runtime: resolve(target),
    helperBuilt: true,
    officialOverlay: true,
    fullSourceBuild: false,
  }),
)
