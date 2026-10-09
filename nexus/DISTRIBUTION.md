# ZettaCore Nexus — distribution plan

## Phase 1: installable web app (PWA)
The current Render-hosted prototype is being prepared as a Progressive Web App (PWA). Users can open the website worldwide and, on supported browsers, install it from the browser menu or the app's install prompt. This does not require a store listing or a developer account fee.

Current limitations:
- The prototype demo stores its notes and chat in that browser's local storage.
- No real AI model, accounts, cloud sync, subscription, or payment processing is active.
- PWA installation and offline caching are convenience features, not a native app store release.
- Browser installation support varies, especially on iOS. Use the browser's Add to Home Screen action where necessary.

## Phase 2: secure online product
Before opening real chat to the public:
1. Add user authentication and secure sessions.
2. Add a database for accounts, preferences and explicitly opted-in memories.
3. Add per-user quotas, abuse protection and request throttling.
4. Add data export/deletion, retention rules, privacy notices and a support contact.
5. Add subscription verification on the server. Never trust a price, plan or entitlement sent by the browser.
6. Add admin-only analytics with access control and privacy-conscious event logging.
7. Test model-provider errors, cost limits, prompt injection and access boundaries.

## Phase 3: global distribution
- **Web/PWA:** easiest first release; users worldwide can access it through a link.
- **Google Play:** Android listing after packaging/testing. Google Play generally requires a one-time developer registration fee; verify current terms before publishing.
- **Apple App Store:** iPhone/iPad listing after native packaging/testing. Apple Developer Program membership generally has an annual fee; verify current terms and regional requirements.
- **Desktop:** package the web app or build a desktop shell once updates, signing and security are designed.
- **Local edition:** optional version that connects to a locally installed model (for example, Ollama). This requires a compatible computer and should not expose its local model port publicly.

## Subscription design
Keep the user interface, provider calls, entitlements and billing separate. A payment provider such as Stripe can be evaluated later, but subscription state must be verified by server-side webhooks. Never store card numbers or secret payment credentials ourselves. Before selling, confirm legal entity details, tax/VAT handling, consumer cancellation/refund rules, privacy obligations and provider availability.

## Free versus paid
A sensible starting plan could offer limited free usage and paid tiers for higher quotas, longer context, synced memory or advanced tools. The actual limits and prices must be based on measured model costs and abuse testing. Do not promise unlimited AI usage while using a provider with quotas or per-token costs.
