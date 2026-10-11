# ZettaCore Sentinel

Privacy-minded MVP for explainable URL triage. It is not a certified anti-phishing product and never gives a "safe" verdict.

## Current scope (0.3.0)
- Strict URL parsing for unsupported schemes, ambiguous backslashes, credentials, ports, internationalized labels and malformed hostnames.
- Heuristics for local/private IPs, local hostnames, known shorteners, brand/domain impersonation, simple lookalike labels, unusually deep subdomains, uncommon ports and social-engineering terms.
- Each finding includes severity, rationale and observed evidence. The numeric indicator is explicitly not a probability.
- "Unverified" status when no configured heuristic fires.
- Privacy-minimised response: returns hostname and origin, not the submitted path, query, fragment or userinfo.
- Baseline response headers, no-store policy, Content-Length guard and strict Content Security Policy. Static CSS/JS are served as local files.
- Optional URLhaus URL lookup, only when the visitor explicitly opts in AND the server has URLHAUS_AUTH_KEY and URLHAUS_LICENSE_APPROVED=true. URLs containing userinfo are never sent to the provider. Results never echo the full URL.

## Run locally
From this folder:
1. Install dependencies with pip install -r requirements.txt.
2. Run uvicorn app.main:app --reload.
3. Open http://127.0.0.1:8000. Health: /api/health. API docs: /api/docs.
4. Run tests with pytest -q.

## External intelligence and license gate
URLhaus is an indicator source focused on malware distribution. Querying it shares the full URL (path and query included) with URLhaus, which is why consent is explicit and disabled by default. To enable it, configure URLHAUS_AUTH_KEY as a secret and set URLHAUS_LICENSE_APPROVED=true only after confirming the applicable API terms/plan permit the intended use. URLhaus states that commercial or for-profit use may require its enhanced commercial API: https://urlhaus.abuse.ch/api/ and https://urlhaus-api.abuse.ch/.

Do not use Google Safe Browsing's free API for a commercial product; its usage guidance says it is for non-commercial use and directs commercial use to Web Risk: https://developers.google.com/safe-browsing/reference/Appropriate.Usage. OpenPhish similarly restricts commercial use without prior written consent: https://www.openphish.com/terms.html.

## Security boundaries and roadmap
- The brand/domain list is small and incomplete: a cue, not an official-domain registry or public-suffix implementation.
- Heuristics and third-party feeds can be stale, miss threats or flag legitimate sites. A match is an indicator, not proof; no match does not mean safe.
- No target URL is fetched, resolved or redirected in this version. Any future web scanner needs strict SSRF protections: validate all A/AAAA answers at connection time, block loopback/private/link-local/reserved ranges, revalidate every redirect and DNS result, enforce timeouts and response-size limits, strip credentials/cookies, use egress controls and rate limits.
- Audits must be restricted to domains the user owns or is authorised to assess.
- Production still needs an updated public-suffix/official-domain source, stronger distributed rate limiting, structured security monitoring that excludes submitted URLs, pinned dependencies and vulnerability scanning, CI confirmation, accessibility review and independent security review.
