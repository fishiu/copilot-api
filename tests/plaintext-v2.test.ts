import { describe, expect, test } from "bun:test"
import {
  preparePlaintextV2,
  restorePlaintextV2Response,
  restorePlaintextV2Chunk,
  PLAINTEXT_V2_ALIAS as alias,
} from "../src/lib/plaintext-v2"
const ns = () => ({
  type: "namespace",
  name: "collaboration",
  tools: [
    ...["spawn_agent", "send_message", "followup_task", "wait_agent"].map(
      (name) => ({
        type: "function",
        name,
        parameters: {
          properties: { message: { type: "string", encrypted: true } },
        },
      }),
    ),
  ],
})
const payload = () => ({
  model: "gpt-6-astra",
  tools: [ns()],
  input: [
    {
      type: "message",
      role: "user",
      content: "collaboration must stay in user text",
    },
  ],
})
const call = (name = "spawn_agent", message = "Read the file") => ({
  type: "function_call",
  namespace: alias,
  name,
  arguments: JSON.stringify({ message }),
  call_id: "abc",
})
describe("opt-in plaintext V2", () => {
  test("disabled and unlisted models preserve identity", () => {
    const p = payload()
    expect(preparePlaintextV2(p).payload).toBe(p)
    expect(preparePlaintextV2(p, "other").active).toBe(false)
    expect(preparePlaintextV2(null, "x").active).toBe(false)
  })
  test("rewrite only message schemas and preserve input", () => {
    const p = payload()
    const r = preparePlaintextV2(p, "gpt-6-astra")
    expect(r.active).toBe(true)
    expect(r.payload.tools[0].name).toBe(alias)
    expect(
      r.payload.tools[0].tools[0].parameters.properties.message,
    ).not.toHaveProperty("encrypted")
    expect(
      r.payload.tools[0].tools[3].parameters.properties.message.encrypted,
    ).toBe(true)
    expect(p.tools[0].name).toBe("collaboration")
    expect(r.payload.input).toEqual(p.input)
  })
  test("developer, discovered tools, history and tool choice", () => {
    const p = {
      model: "x",
      input: [
        { type: "additional_tools", tools: [ns()] },
        { type: "tool_search_output", tools: [ns()] },
        {
          type: "function_call",
          namespace: "collaboration",
          name: "send_message",
          arguments: '{"message":"a"}',
        },
        {
          type: "function_call",
          namespace: "collaboration",
          name: "wait_agent",
          arguments: "{}",
        },
      ],
      tool_choice: { namespace: "collaboration" },
    }
    const r = preparePlaintextV2(p, "x")
    expect(r.active).toBe(true)
    expect(r.payload.input[2].namespace).toBe(alias)
    expect(r.payload.tool_choice.namespace).toBe(alias)
  })
  test("no tools leaves ordinary request unchanged", () => {
    const p = { model: "x", input: "hello" }
    expect(preparePlaintextV2(p, "x").payload).toBe(p)
  })
  test("reject alias conflicts", () => {
    const p = payload()
    p.tools.push({ ...ns(), name: alias })
    expect(preparePlaintextV2(p, "gpt-6-astra").error).toContain("collision")
  })
  test("reject encrypted agent message before upstream", () => {
    const p = {
      model: "x",
      input: [
        {
          type: "agent_message",
          content: [{ type: "encrypted_content", encrypted_content: "old" }],
        },
      ],
    }
    expect(preparePlaintextV2(p, "x").error).toContain("not decrypted")
  })
  test("reject old cipher and invalid args", () => {
    for (const args of ['{"message":"gAAAA' + "a".repeat(60) + '"}', "bad"]) {
      expect(
        preparePlaintextV2(
          {
            model: "x",
            tools: [ns()],
            input: [{ ...call(), namespace: "collaboration", arguments: args }],
          },
          "x",
        ).error,
      ).toBeTruthy()
    }
  })
  test("restore message calls and mark plaintext", () => {
    for (const name of ["spawn_agent", "send_message", "followup_task"]) {
      const c = call(name)
      const r = restorePlaintextV2Response(
        { type: "response.completed", response: { output: [c] } },
        true,
      )
      expect(r.response.output[0]).toEqual({
        ...c,
        namespace: "collaboration",
        encrypted_function_args: [],
      })
      expect(c.namespace).toBe(alias)
    }
  })
  test("restore wait names without plaintext marker", () => {
    const r = restorePlaintextV2Response(call("wait_agent"), true)
    expect(r.namespace).toBe("collaboration")
    expect(r).not.toHaveProperty("encrypted_function_args")
  })
  test("added call, pass-through and nested results", () => {
    expect(
      restorePlaintextV2Response({ ...call(), arguments: "" }, true).namespace,
    ).toBe("collaboration")
    const output = { type: "function_call_output", output: [call()] }
    expect(restorePlaintextV2Response(output, true)).toEqual(output)
    expect(restorePlaintextV2Response(null, true)).toBe(null)
    const c = call()
    expect(restorePlaintextV2Response(c, false)).toBe(c)
  })
  test("reject malformed or opaque new messages", () => {
    for (const message of ["", "gAAAA" + "b".repeat(60)])
      expect(() =>
        restorePlaintextV2Response(call("send_message", message), true),
      ).toThrow()
    expect(() =>
      restorePlaintextV2Response({ ...call(), arguments: "bad" }, true),
    ).toThrow()
  })
  test("SSE rewrite preserves ids and unrelated usage", () => {
    const c = {
      id: "event1",
      event: "response.output_item.done",
      data: JSON.stringify({ type: "response.output_item.done", item: call() }),
    }
    const r = restorePlaintextV2Chunk(c, true)
    expect(r.id).toBe("event1")
    const event: unknown = JSON.parse(r.data)
    expect(event).toMatchObject({ item: { namespace: "collaboration" } })
    expect(restorePlaintextV2Chunk(c, false)).toBe(c)
    for (const data of ["[DONE]", "", ":heartbeat"]) {
      const v = { data }
      expect(restorePlaintextV2Chunk(v, true)).toBe(v)
    }
  })
})
