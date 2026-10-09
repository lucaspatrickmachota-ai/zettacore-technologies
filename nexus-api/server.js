const http = require("node:http");
const { chat } = require("./providers");

const PORT = Number(process.env.PORT || 3000);
const MAX_BODY = 16_384;
const WINDOW_MS = 60_000;
const MAX_REQUESTS_PER_WINDOW = 10;
const requestBuckets = new Map();
const allowedOrigins = new Set(
  (process.env.NEXUS_ALLOWED_ORIGINS || "https://zettacore-nexus.onrender.com")
    .split(",").map((s) => s.trim()).filter(Boolean)
);

function selectedProvider() {
  const provider = (process.env.NEXUS_AI_PROVIDER || "").toLowerCase();
  if (provider === "gemini" && process.env.GEMINI_API_KEY) {
    return { ready: true, provider, model: process.env.GEMINI_MODEL || "gemini-2.5-flash" };
  }
  if (provider === "groq" && process.env.GROQ_API_KEY && process.env.GROQ_MODEL) {
    return { ready: true, provider, model: process.env.GROQ_MODEL };
  }
  if (provider === "ollama" && process.env.OLLAMA_MODEL) {
    return { ready: true, provider, model: process.env.OLLAMA_MODEL };
  }
  return { ready: false, provider: null, model: null };
}

function send(res, status, data, origin = "") {
  const headers = {
    "content-type": "application/json; charset=utf-8",
    "cache-control": "no-store",
    "x-content-type-options": "nosniff",
    "x-frame-options": "DENY",
    "referrer-policy": "no-referrer",
    "content-security-policy": "default-src 'none'; frame-ancestors 'none'",
    "vary": "Origin"
  };
  if (origin && allowedOrigins.has(origin)) {
    headers["access-control-allow-origin"] = origin;
    headers["access-control-allow-methods"] = "GET, POST, OPTIONS";
    headers["access-control-allow-headers"] = "Content-Type, Accept";
    headers["access-control-max-age"] = "600";
  }
  res.writeHead(status, headers);
  res.end(JSON.stringify(data));
}

function isAllowedOrigin(req) {
  const origin = req.headers.origin;
  // Browser requests must originate from the Nexus site. Non-browser health checks may omit Origin.
  if (!origin) return true;
  return allowedOrigins.has(origin);
}

function rateLimited(req) {
  const forwarded = req.headers["x-forwarded-for"];
  const ip = (typeof forwarded === "string" ? forwarded.split(",")[0].trim() : "") ||
    req.socket.remoteAddress || "unknown";
  const now = Date.now();
  let bucket = requestBuckets.get(ip);
  if (!bucket || now - bucket.start >= WINDOW_MS) {
    bucket = { start: now, count: 0 };
    requestBuckets.set(ip, bucket);
  }
  bucket.count += 1;
  if (requestBuckets.size > 5_000) {
    for (const [key, value] of requestBuckets) {
      if (now - value.start >= WINDOW_MS) requestBuckets.delete(key);
    }
  }
  return bucket.count > MAX_REQUESTS_PER_WINDOW;
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    let size = 0;
    const chunks = [];
    req.on("data", (chunk) => {
      size += chunk.length;
      if (size > MAX_BODY) {
        const error = new Error("request_too_large");
        error.code = "request_too_large";
        reject(error);
        req.destroy();
        return;
      }
      chunks.push(chunk);
    });
    req.on("end", () => {
      try {
        resolve(JSON.parse(Buffer.concat(chunks).toString("utf8") || "{}"));
      } catch {
        const error = new Error("invalid_json");
        error.code = "invalid_json";
        reject(error);
      }
    });
    req.on("error", reject);
  });
}

const server = http.createServer(async (req, res) => {
  const origin = req.headers.origin || "";
  if (req.method === "OPTIONS") {
    if (!isAllowedOrigin(req)) return send(res, 403, { error: "origin_not_allowed" });
    res.writeHead(204, {
      "access-control-allow-origin": origin,
      "access-control-allow-methods": "GET, POST, OPTIONS",
      "access-control-allow-headers": "Content-Type, Accept",
      "access-control-max-age": "600",
      "vary": "Origin"
    });
    return res.end();
  }

  if (!isAllowedOrigin(req)) {
    return send(res, 403, { error: "origin_not_allowed" });
  }

  if (req.method === "GET" && req.url === "/health") {
    return send(res, 200, { ok: true, service: "zettacore-nexus-api", stage: "provider-ready-foundation" }, origin);
  }

  if (req.method === "GET" && req.url === "/api/status") {\n    const provider = selectedProvider();\n    const chatEnabled = process.env.NEXUS_CHAT_ENABLED === "true";
    return send(res, 200, {
      product: "ZettaCore Nexus",
      stage: provider.ready && chatEnabled ? "model-configured" : "prototype",
      aiConnected: provider.ready && chatEnabled,
      provider: provider.provider,
      model: provider.model,
      accountsEnabled: false,
      subscriptionsEnabled: false,
      note: !provider.ready
        ? "AI provider is not configured. No prompts are sent to an AI provider."
        : !chatEnabled
          ? "Provider credentials are present, but chat is disabled until explicitly enabled."
          : "Provider is configured. Prototype rate limits apply; authentication is not yet implemented."
    }, origin);
  }

  if (req.method === "POST" && req.url === "/api/chat") {
    if (rateLimited(req)) {
      res.setHeader("retry-after", "60");
      return send(res, 429, { error: "rate_limited", message: "Too many requests. Please wait a minute and try again." }, origin);
    }
    const provider = selectedProvider();\n    if (process.env.NEXUS_CHAT_ENABLED !== "true" || !provider.ready) {
      return send(res, 503, {
        error: "ai_not_configured",
        message: "The AI model is not configured yet. No user content was sent to an AI provider."
      }, origin);
    }
    let body;
    try {
      body = await readBody(req);
    } catch (error) {
      if (error.code === "request_too_large") {
        if (!res.headersSent && !res.writableEnded) return send(res, 413, { error: "request_too_large" }, origin);
        return;
      }
      if (!res.headersSent && !res.writableEnded) return send(res, 400, { error: "invalid_json" }, origin);
      return;
    }
    try {
      if (!body || !Array.isArray(body.messages)) {
        return send(res, 400, { error: "invalid_messages" }, origin);
      }
      const locale = typeof body.locale === "string" && /^[a-z]{2}$/.test(body.locale) ? body.locale : "en";\n      const result = await chat(body.messages, locale);
      return send(res, 200, result, origin);
    } catch (error) {
      if (error.code === "invalid_messages") return send(res, 400, { error: "invalid_messages" }, origin);
      if (error.code === "provider_rate_limited") return send(res, 429, { error: "provider_rate_limited", message: "The AI provider is at its current limit. Please try again later." }, origin);
      if (error.code === "provider_timeout") return send(res, 504, { error: "provider_timeout", message: "The AI provider took too long to respond." }, origin);
      console.error("Nexus provider request failed:", error.code || "provider_error");
      return send(res, 502, { error: "provider_error", message: "The AI provider could not complete this request." }, origin);
    }
  }

  return send(res, 404, { error: "not_found" }, origin);
});

server.listen(PORT, "0.0.0.0", () => {
  console.log("Nexus API listening on port " + PORT);
});
