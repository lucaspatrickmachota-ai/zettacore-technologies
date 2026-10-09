# ZettaCore Nexus API foundation

Minimal Node.js HTTP service for the Nexus prototype. Uses Node built-ins only.

## Endpoints
- `GET /health` — health check.
- `GET /api/status` — current feature flags.
- `POST /api/chat` — deliberately returns 503 until a model provider, authentication, rate limiting and data-handling policy are configured.

## Security notes
- Never place model-provider keys in browser JavaScript.
- This foundation does not yet implement accounts, database persistence, subscription verification, admin analytics or real AI.
- Do not collect real customer data or accept payments until authentication, authorization, validation, abuse controls, privacy disclosures and monitoring have been implemented and tested.
- Configure provider secrets only as server-side environment variables when the integration is ready.
