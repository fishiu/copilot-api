/** Optional local search forwarding; keeps OAuth refresh ownership in one gateway. */
import { readFile } from "node:fs/promises"
import { join } from "node:path"

export async function forwardLocalAlphaSearch(
  request: Request,
  base = process.env.CAPI_ALPHA_SEARCH_FORWARD_BASE,
  apiHome = process.env.CAPI_ALPHA_SEARCH_FORWARD_API_HOME,
  fetcher: typeof fetch = fetch,
): Promise<Response | null> {
  if (!base && !apiHome) return null
  if (!base || !apiHome)
    throw new Error("Incomplete local alpha-search forwarding configuration")
  const target = new URL("/v1/alpha/search", base)
  if (
    target.protocol !== "http:"
    || !["127.0.0.1", "localhost", "[::1]"].includes(target.hostname)
  )
    throw new Error(
      "Alpha-search credential forwarding is restricted to loopback HTTP",
    )
  target.search = new URL(request.url).search
  const config: unknown = JSON.parse(
    await readFile(join(apiHome, "config.json"), "utf8"),
  )
  const auth = (config as { auth?: { apiKeys?: unknown[] } }).auth
  const key = auth?.apiKeys?.[0]
  if (typeof key !== "string" || key.length < 32)
    throw new Error("Local alpha-search gateway key is missing")
  const headers = new Headers(request.headers)
  for (const name of [
    "host",
    "content-length",
    "connection",
    "authorization",
    "x-api-key",
  ])
    headers.delete(name)
  headers.set("authorization", "Bearer " + key)
  return await fetcher(target, {
    method: "POST",
    headers,
    body: await request.arrayBuffer(),
    signal: request.signal,
  })
}
