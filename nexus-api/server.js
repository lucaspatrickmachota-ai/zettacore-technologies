const http = require("node:http");

const PORT = Number(process.env.PORT || 3000);
const MAX_BODY = 16_384;

function send(res, status, data) {
  res.writeHead(status, {
    "content-type": "application/json; charset=utf-8",
    "cache-control": "no-store",
    "x-content-type-options": "nosniff",
    "x-frame-options": "DENY",
    "referrer-policy": "no-referrer",
    "content-security-policy": "default-src 'none'; frame-ancestors 'none'",
  });
  res.end(JSON.stringify(data));
}

const server = http.createServer((req, res) => {
  if (req.method === "GET" && req.url === "/health") {
    return send(res, 200, { ok: true, service: "zettacore-nexus-api", stage: "foundation" });
  }

  if (req.method === "GET" && req.url === "/api/status") {
    return send(res, 200, {
      product: "ZettaCore Nexus",
      stage: "prototype",
      aiConnected: false,
      accountsEnabled: false,
      subscriptionsEnabled: false,
      note: "AI and billing are intentionally disabled until secure configuration is completed."
    });
  }

  if (req.method === "POST" && req.url === "/api/chat") {
    let size = 0;
    req.on("data", chunk => {
      size += chunk.length;
      if (size > MAX_BODY) {
        send(res, 413, { error: "request_too_large" });
        req.destroy();
      }
    });
    req.on("end", () => {
      if (res.writableEnded) return;
      return send(res, 503, {
        error: "ai_not_configured",
        message: "The AI model is not connected yet. No user content was sent to an AI provider."
      });
    });
    return;
  }

  return send(res, 404, { error: "not_found" });
});

server.listen(PORT, "0.0.0.0", () => {
  console.log("Nexus API foundation listening on port " + PORT);
});
