# Nexus subscriptions — architecture and launch gates

**Status: design only. No billing is active and no payment credentials are configured.**

## Product model to validate
- Free: low usage quota, basic chat once the real model is connected.
- Plus: proposed €7.99/month for a higher quota and synced memory when available.
- Pro: proposed €19.99/month for higher usage and advanced features when available.

These are hypotheses, not published prices. Before setting prices, measure provider cost per conversation, hosting/database costs, payment processing, taxes, support and abuse. Do not promise unlimited usage.

## Recommended flow
1. A user signs in and the backend identifies the account.
2. The backend creates a checkout session using a server-side Stripe secret.
3. Stripe hosts the payment form; the app never handles or stores card numbers.
4. A signed Stripe webhook updates subscription status in the database.
5. Each protected API request checks the server-side entitlement and quota.
6. The user manages cancellation and invoices through a verified customer portal.

## Required controls before enabling checkout
- Authentication and server-side account IDs.
- Database schema for users, subscription IDs, status, plan, period dates and event IDs.
- Webhook signature verification against the raw request body.
- Idempotency: duplicate webhook deliveries must not double-apply changes.
- Never trust a plan, amount, subscription status or user ID sent by the browser.
- Rate limits, usage quotas, provider spend limits and abuse monitoring.
- A tested cancellation flow and handling of failed payments/refunds.
- Privacy notice, terms, support contact and data export/deletion process.
- Legal/tax review for the responsible entity, VAT and consumer cancellation rights.
- Stripe test mode and test cards before any live credentials are enabled.

## Suggested server-side environment variables
- STRIPE_SECRET_KEY (test mode first)
- STRIPE_WEBHOOK_SECRET
- STRIPE_PRICE_PLUS_MONTHLY (Stripe Price ID, not an amount from the browser)
- STRIPE_PRICE_PRO_MONTHLY (Stripe Price ID, not an amount from the browser)
- APP_BASE_URL
- DATABASE_URL (only after selecting and securing a database)

Never put these values in frontend JavaScript, commit them to Git, or include them in logs. Do not configure production keys until all gates are passed.

## Admin analytics
Track aggregate counts such as registrations, active subscriptions, cancellations, provider usage, errors and revenue from verified payment events. Restrict the admin dashboard to an explicitly authorized admin role, protect it with MFA where available, and avoid storing full prompts or sensitive content merely for analytics.

## Important limitation
The current API does not yet have authentication or a database. Therefore, a real checkout or subscription entitlement endpoint must not be exposed yet. A billing integration is not complete until webhook verification, database state, authorization, tests and cancellation handling all work together.
