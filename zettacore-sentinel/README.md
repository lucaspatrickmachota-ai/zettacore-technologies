# ZettaCore Sentinel

A privacy-minded MVP for explainable URL triage. This is not a certified anti-phishing product.

## Current scope (0.2.0)
- Strict URL parsing for unsupported schemes, ambiguous backslashes, credentials, ports, internationalized labels and malformed hostnames.
- Heuristic cues for non-public IPs, local hostnames, URL shorteners, brand impersonation, simple visual typos, unusually deep subdomains, uncommon ports and social-engineering terms.
- An explanation for each finding and an internal indicator score explicitly labelled as a heuristic, not probability.
- An "unverified" result when no current rule fires; no "safe" verdict.
- Privacy-minimised response: hostname and origin only, not the submitted path, query, fragment or userinfo.
- Baseline response security headers, no-store policy and a Content-Length limit.
- No URL fetching, DNS resolution, redirect following or external reputation calls.

## Run locally
Install requirements.txt, then run: uvicorn app.main:app --reload
Open http://127.0.0.1:8000. Health endpoint: /api/health. API docs: /api/docs.
Tests: pytest -q

## Security boundaries and roadmap
- The brand/domain list is small and incomplete: a cue, not an official-domain registry.
- Heuristics can miss phishing and flag legitimate services. Never market this version as a definitive verdict.
- Do not add URL fetching casually. A future fetcher must be isolated and implement SSRF protections: validate all resolved A/AAAA addresses, block loopback/private/link-local/reserved IPs, revalidate every redirect and DNS result, enforce timeouts and response-size limits, strip credentials/cookies, apply egress controls and rate limits.
- Web audits must be restricted to domains the user owns or is authorised to assess.
- Avoid storing full URLs, since query strings may contain session tokens or personal data.
- Production still needs updated public-suffix/official-domain data, external reputation integrations with privacy review, distributed rate limiting, security monitoring that excludes submitted URLs, dependency pinning/scanning, CI, accessibility review and an independent security review.
