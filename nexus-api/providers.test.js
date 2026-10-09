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
