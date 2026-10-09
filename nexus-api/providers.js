const DEFAULT_TIMEOUT_MS = 30_000;
const MAX_OUTPUT_TOKENS = 512;

function requiredEnv(name) {
  const value = process.env[name];
  if (!value || !value.trim()) {
    const error = new Error("Provider is not configured");
    error.code = "provider_not_configured";
    throw error;
  }
  return value.trim();
}

async function fetchWithTimeout(url, options, timeoutMs = DEFAULT_TIMEOUT_MS) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, { ...options, signal: controller.signal });
  } catch (error) {
    if (error.name === "AbortError") {
      const timeout = new Error("AI provider timed out");
      timeout.code = "provider_timeout";
      throw timeout;
    }
    throw error;
  } finally {
    clearTimeout(timer);
  }
}

async function readJson(response) {
  const text = await response.text();
  let data;
  try {
    data = JSON.parse(text);
  } catch {
    throw new Error("AI provider returned an invalid response");
  }
  if (!response.ok) {
    const error = new Error("AI provider request failed");
    error.code = response.status === 429 ? "provider_rate_limited" : "provider_request_failed";
    error.status = response.status;
    throw error;
  }
  return data;
}

function normalizeMessages(messages) {
  if (!Array.isArray(messages) || messages.length === 0 || messages.length > 20) {
    const error = new Error("Invalid messages");
    error.code = "invalid_messages";
    throw error;
  }
  return messages.map((item) => {
    if (!item || !["user", "assistant"].includes(item.role) ||
        typeof item.content !== "string" || !item.content.trim() || item.content.length > 8_000) {
      const error = new Error("Invalid message");
      error.code = "invalid_messages";
      throw error;
    }
    return { role: item.role, content: item.content.trim() };
  });
}

async function geminiChat(messages, locale) {
  const key = requiredEnv("GEMINI_API_KEY");
  const model = process.env.GEMINI_MODEL || "gemini-2.5-flash";
  const contents = normalizeMessages(messages).map((m) => ({
    role: m.role === "assistant" ? "model" : "user",
    parts: [{ text: m.content }]
  }));
  const url = "https://generativelanguage.googleapis.com/v1beta/models/" +
    encodeURIComponent(model) + ":generateContent";
  const response = await fetchWithTimeout(url, {
    method: "POST",
    headers: { "content-type": "application/json", "x-goog-api-key": key },
    body: JSON.stringify({
      systemInstruction: { parts: [{ text: languageInstruction(locale) }] },\n      contents,\n      generationConfig: { maxOutputTokens: MAX_OUTPUT_TOKENS, temperature: 0.4 }
    })
  });
  const data = await readJson(response);
  const answer = data.candidates?.[0]?.content?.parts?.map((p) => p.text || "").join("").trim();
  if (!answer) throw new Error("AI provider returned no answer");
  return { answer, provider: "gemini", model };
}

async function groqChat(messages, locale) {
  const key = requiredEnv("GROQ_API_KEY");
  const model = requiredEnv("GROQ_MODEL");
  const response = await fetchWithTimeout("https://api.groq.com/openai/v1/chat/completions", {
    method: "POST",
    headers: { authorization: "Bearer " + key, "content-type": "application/json" },
    body: JSON.stringify({
      model,
      messages: [{ role: "system", content: languageInstruction(locale) }, ...normalizeMessages(messages).map((m) => ({ role: m.role, content: m.content }))],
      max_tokens: MAX_OUTPUT_TOKENS,
      temperature: 0.4
    })
  });
  const data = await readJson(response);
  const answer = data.choices?.[0]?.message?.content?.trim();
  if (!answer) throw new Error("AI provider returned no answer");
  return { answer, provider: "groq", model };
}

async function ollamaChat(messages, locale) {
  const baseUrl = (process.env.OLLAMA_BASE_URL || "http://127.0.0.1:11434").replace(/\/$/, "");
  const model = requiredEnv("OLLAMA_MODEL");
  const response = await fetchWithTimeout(baseUrl + "/api/chat", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      model,
      messages: [{ role: "system", content: languageInstruction(locale) }, ...normalizeMessages(messages).map((m) => ({ role: m.role, content: m.content }))],
      stream: false,
      options: { num_predict: MAX_OUTPUT_TOKENS, temperature: 0.4 }
    })
  });
  const data = await readJson(response);
  const answer = data.message?.content?.trim();
  if (!answer) throw new Error("AI provider returned no answer");
  return { answer, provider: "ollama", model };
}

function languageInstruction(locale) {
  const languages = {
    es: "Responde en español salvo que el usuario pida otro idioma.",
    en: "Respond in English unless the user asks for another language.",
    pt: "Responda em português, salvo se o usuário pedir outro idioma.",
    fr: "Répondez en français, sauf si l’utilisateur demande une autre langue.",
    de: "Antworte auf Deutsch, sofern der Nutzer keine andere Sprache verlangt.",
    it: "Rispondi in italiano, salvo richiesta di un'altra lingua.",
    ja: "ユーザーが別の言語を希望しない限り、日本語で回答してください。",
    zh: "除非用户要求其他语言，否则请用简体中文回答。",
    ar: "أجب باللغة العربية ما لم يطلب المستخدم لغة أخرى.",
    hi: "जब तक उपयोगकर्ता कोई दूसरी भाषा न मांगे, हिंदी में उत्तर दें。"
  };
  return "You are ZettaCore Nexus, a helpful AI assistant. " +
    (languages[locale] || languages.en) +
    " Be honest about uncertainty. Never claim a tool action was completed unless it actually was.";
}

async function chat(messages, locale) {
  const provider = (process.env.NEXUS_AI_PROVIDER || "").toLowerCase();
  if (provider === "gemini") return geminiChat(messages, locale);
  if (provider === "groq") return groqChat(messages, locale);
  if (provider === "ollama") return ollamaChat(messages, locale);
  const error = new Error("No AI provider selected");
  error.code = "provider_not_configured";
  throw error;
}

module.exports = { chat, normalizeMessages };
