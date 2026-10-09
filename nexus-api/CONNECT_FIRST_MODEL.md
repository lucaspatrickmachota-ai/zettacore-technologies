# Connect the first real model to Nexus

**Current state:** provider adapters exist, but no provider secret has been configured. The public chat route remains disabled by default. The website's language selector changes the interface language; it does not translate model replies automatically.

## Recommended first experiment: Gemini API
1. Create an API key in Google AI Studio using the account you control.
2. Review current pricing, free-tier limits, and data-use terms: https://ai.google.dev/gemini-api/docs/pricing
3. In the Render dashboard for `zettacore-nexus-api`, open Environment and add:
   - `NEXUS_AI_PROVIDER=gemini`
   - `GEMINI_API_KEY` = your secret key
   - `GEMINI_MODEL=gemini-2.5-flash` (or a model currently available to your key)
   - `NEXUS_CHAT_ENABLED=false`
   - `NEXUS_ALLOWED_ORIGINS=https://zettacore-nexus.onrender.com`
4. Redeploy and check `/api/status`. It should report the provider is present but `aiConnected=false` while the explicit flag is false.
5. Do not set `NEXUS_CHAT_ENABLED=true` for a public launch yet. The current request limit is in-memory and per instance, and there is no user authentication, persistent quota accounting, abuse monitoring, or database. Before public activation, implement those controls and test with a controlled private beta.

## Alternative: Groq
Use `NEXUS_AI_PROVIDER=groq`, `GROQ_API_KEY` and `GROQ_MODEL`. Check model availability and current rate limits: https://console.groq.com/docs/rate-limits. Do not switch to a paid tier without reviewing billing.

## Local Ollama
Ollama is suitable when Nexus API runs on the same machine as Ollama. A cloud-hosted Render service cannot use `127.0.0.1` to reach your personal computer. Never expose an unauthenticated Ollama port publicly.

## Multilingual behaviour
The current website selector changes the interface among Spanish, English, Portuguese, French, German, Italian, Japanese, Chinese, Arabic and Hindi. The model itself may respond in a different language depending on its instructions. A production release should add a server-side system instruction for the selected locale and validate language behaviour. The selected locale is not yet sent to the API.

## Important
Never paste an API key into the chat, a public issue, frontend JavaScript, or a committed file. Set it only in Render's secret environment settings. Free-tier limits and terms can change, and model input may be handled under the provider's terms. Do not send confidential user data to a provider before privacy terms and consent are ready.
