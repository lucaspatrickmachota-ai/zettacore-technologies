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


## Provider adapters
See [provider setup](PROVIDER_SETUP.md) for Gemini, Groq and local Ollama configuration. Adapters are implemented in `providers.js`; they are not yet exposed through the public chat route. This is intentional until authentication, quotas and abuse controls are in place.

## Distribution
See [Nexus distribution plan](../nexus/DISTRIBUTION.md) for the PWA-first approach, app-store options and subscription safeguards.

## Local checks
Run `node --check nexus-api/server.js`, `node --check nexus-api/providers.js`, and `node --test nexus-api/providers.test.js` before deploying changes.
