# Nexus AI provider setup (development)

Nexus now has a provider adapter module in `providers.js`. It supports Gemini, Groq, and a local Ollama server. This is integration groundwork, **not yet a public chat feature**: the public `POST /api/chat` endpoint remains disabled until user authentication, authorization, per-user rate limits, abuse protection, and privacy handling are implemented.

## Choose a provider

Set `NEXUS_AI_PROVIDER` to exactly one of `gemini`, `groq`, or `ollama`.

### Gemini API
- `NEXUS_AI_PROVIDER=gemini`
- `GEMINI_API_KEY=<server-side key>`
- Optional: `GEMINI_MODEL=gemini-2.5-flash`

Google offers a free tier with model-specific quotas, not a guaranteed unlimited production allowance. Review the current [pricing](https://ai.google.dev/gemini-api/docs/pricing) and [terms](https://ai.google.dev/gemini-api/terms) before use. Do not send confidential or personal information to unpaid services. In the European Economic Area, Google's terms say the paid-service data-use conditions apply even to unpaid quota, but check current terms for the exact account and use case.

### GroqCloud
- `NEXUS_AI_PROVIDER=groq`
- `GROQ_API_KEY=<server-side key>`
- `GROQ_MODEL=<model currently available to your account>`

The free tier has rate limits that vary by model and account. Check [current limits](https://console.groq.com/docs/rate-limits). On a limit, requests can fail with HTTP 429; free access is not a production availability guarantee.

### Local Ollama
- `NEXUS_AI_PROVIDER=ollama`
- `OLLAMA_MODEL=<model installed locally>`
- Optional: `OLLAMA_BASE_URL=http://127.0.0.1:11434`

This sends prompts to the Ollama server at the configured address and avoids per-token cloud API charges. It requires a machine with enough RAM/CPU/GPU and Ollama installed. The default loopback URL is appropriate when the API and Ollama run on the same machine; a hosted Render service cannot reach your personal computer's loopback address. Never expose Ollama directly to the public internet.

## Secret handling
- Configure keys only in server environment variables or a secrets manager, never in browser JavaScript, Git, screenshots, or public logs.
- Do not set provider credentials until you're ready to test.
- Keep the public chat endpoint disabled until authentication and rate limiting are implemented.
- No provider keys, user accounts, subscription data, or payment details are included in this repository.

## Test
Run `node --test nexus-api/providers.test.js` with a supported Node.js version. These tests validate request input handling without making network calls.
