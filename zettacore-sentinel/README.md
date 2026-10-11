# ZettaCore Sentinel MVP 0.1

Early URL-risk prototype, not a certified security product.

## Run
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

This version analyses URL text only. It does not visit URLs or query external reputation sources. Findings are heuristics, not a probability or safety guarantee. Do not add live scanning without strict SSRF protections, DNS/IP validation, redirect checks, timeouts, rate limits, privacy controls, and authorization checks.
