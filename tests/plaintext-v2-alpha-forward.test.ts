import { afterEach, expect, test } from "bun:test"
import { mkdtemp, writeFile, rm } from "node:fs/promises"
import { tmpdir } from "node:os"
import { join } from "node:path"
import { forwardLocalAlphaSearch } from "../src/lib/plaintext-v2-alpha-forward"
async function errorOf(promise: Promise<unknown>): Promise<unknown> {
  try {
    await promise
    return null
  } catch (error) {
    return error
  }
}
let folder: string | undefined
afterEach(async () => {
  if (folder) await rm(folder, { recursive: true })
  folder = undefined
})
const request = () =>
  new Request("http://localhost:60444/alpha/search?q=abc", {
    method: "POST",
    headers: {
      authorization: "Bearer incoming",
      "x-api-key": "incoming",
      "content-type": "application/json",
    },
    body: '{"model":"gpt-6.1-sol"}',
  })
test("off and partial configuration", async () => {
  expect(await forwardLocalAlphaSearch(request(), "", "")).toBe(null)
  expect(
    await errorOf(
      forwardLocalAlphaSearch(request(), "http://127.0.0.1:4142", ""),
    ),
  ).toMatchObject({ message: expect.stringContaining("Incomplete") as unknown })
})
test("reject remote credential forwarding", async () => {
  expect(
    await errorOf(
      forwardLocalAlphaSearch(request(), "https://example.com", "/unused"),
    ),
  ).toMatchObject({ message: expect.stringContaining("loopback") as unknown })
})
test("forward original body and replace credentials", async () => {
  folder = await mkdtemp(join(tmpdir(), "alpha-forward-"))
  const key = "synthetic-local-gateway-key-1234567890"
  await writeFile(
    join(folder, "config.json"),
    JSON.stringify({ auth: { apiKeys: [key] } }),
  )
  let captured:
    | {
        url: string
        authorization: string | null
        apiKey: string | null
        body: string
      }
    | undefined
  const fetcher = ((input: string | URL | Request, init?: RequestInit) => {
    const h = new Headers(init?.headers)
    captured = {
      url:
        input instanceof Request ? input.url
        : typeof input === "string" ? input
        : input.href,
      authorization: h.get("authorization"),
      apiKey: h.get("x-api-key"),
      body: new TextDecoder().decode(init?.body as ArrayBuffer),
    }
    return Promise.resolve(Response.json({ native: true }))
  }) as typeof fetch
  const result = await forwardLocalAlphaSearch(
    request(),
    "http://127.0.0.1:4142",
    folder,
    fetcher,
  )
  expect(result?.status).toBe(200)
  expect(captured).toEqual({
    url: "http://127.0.0.1:4142/v1/alpha/search?q=abc",
    authorization: "Bearer " + key,
    apiKey: null,
    body: '{"model":"gpt-6.1-sol"}',
  })
  await writeFile(join(folder, "config.json"), "{}")
  expect(
    await errorOf(
      forwardLocalAlphaSearch(
        request(),
        "http://127.0.0.1:4142",
        folder,
        fetcher,
      ),
    ),
  ).toMatchObject({
    message: expect.stringContaining("key is missing") as unknown,
  })
})
