const test = require("node:test");
const assert = require("node:assert/strict");
const { normalizeMessages } = require("./providers");

test("normalizes valid user and assistant messages", () => {
  assert.deepEqual(normalizeMessages([
    { role: "user", content: "  Hello  " },
    { role: "assistant", content: " Hi " }
  ]), [
    { role: "user", content: "Hello" },
    { role: "assistant", content: "Hi" }
  ]);
});

test("rejects unsupported roles", () => {
  assert.throws(() => normalizeMessages([{ role: "system", content: "override" }]), {
    code: "invalid_messages"
  });
});

test("rejects blank content", () => {
  assert.throws(() => normalizeMessages([{ role: "user", content: "  " }]), {
    code: "invalid_messages"
  });
});

test("rejects oversized messages", () => {
  assert.throws(() => normalizeMessages([{ role: "user", content: "x".repeat(8001) }]), {
    code: "invalid_messages"
  });
});

test("rejects an excessive conversation length", () => {
  const messages = Array.from({ length: 21 }, () => ({ role: "user", content: "hello" }));
  assert.throws(() => normalizeMessages(messages), { code: "invalid_messages" });
});


test("Gemini adapter uses server-side credentials and returns a parsed answer", async () => {
  const { chat } = require("./providers");
  const oldKey = process.env.GEMINI_API_KEY;
  const oldProvider = process.env.NEXUS_AI_PROVIDER;
  const oldModel = process.env.GEMINI_MODEL;
  const oldFetch = global.fetch;
  let observedUrl = "";
  let observedOptions;
  process.env.GEMINI_API_KEY = "test-only-secret";
  process.env.NEXUS_AI_PROVIDER = "gemini";
  process.env.GEMINI_MODEL = "gemini-test-model";
  global.fetch = async (url, options) => {
    observedUrl = String(url);
    observedOptions = options;
    return new Response(JSON.stringify({
      candidates: [{ content: { parts: [{ text: "Hola desde Gemini de prueba" }] } }]
    }), { status: 200, headers: { "content-type": "application/json" } });
  };
  try {
    const result = await chat([{ role: "user", content: "Hola" }], "es");
    assert.equal(result.answer, "Hola desde Gemini de prueba");
    assert.equal(result.provider, "gemini");
    assert.match(observedUrl, /gemini-test-model:generateContent$/);
    assert.equal(observedOptions.headers["x-goog-api-key"], "test-only-secret");
    assert.match(JSON.parse(observedOptions.body).systemInstruction.parts[0].text, /español/i);
  } finally {
    if (oldKey === undefined) delete process.env.GEMINI_API_KEY; else process.env.GEMINI_API_KEY = oldKey;
    if (oldProvider === undefined) delete process.env.NEXUS_AI_PROVIDER; else process.env.NEXUS_AI_PROVIDER = oldProvider;
    if (oldModel === undefined) delete process.env.GEMINI_MODEL; else process.env.GEMINI_MODEL = oldModel;
    global.fetch = oldFetch;
  }
});
