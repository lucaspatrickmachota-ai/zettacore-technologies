# ZettaCore Vanguard

**INTELLIGENCE. SECURITY. RESILIENCE.**

Vanguard is an independent ZettaCore Technologies cybersecurity product in early development. This repository area contains a local-first desktop prototype, an installable web/PWA shell, and the first public vulnerability-intelligence modules. It does not modify ZettaCore Sentinel.

## Current status

This remains an **early prototype, not a finished security product**. The desktop app and PWA manage separate local asset inventories. Python modules can normalize NVD CVE API v2 records, read the CISA Known Exploited Vulnerabilities (KEV) catalog, enrich CVE records with KEV membership, and produce a transparent triage priority. The connector functions are not yet integrated into the desktop or web UI, and data is not yet persisted as vulnerability records. PDF reporting, asset-to-CVE matching, active assessment, and Windows packaging remain pending.

The priority is an explainable triage heuristic, not a probability of exploitation. A CVE or KEV listing does not prove that an asset is affected or compromised. Confirm product/version and environment-specific evidence separately.

## Desktop app

Requirements: Python 3.11+ (recommended) and dependencies from `pyproject.toml`.

```bash
cd zettacore-vanguard
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m vanguard
```

The app stores its SQLite database in the user's application-data directory, not inside the source checkout.

## Run tests

```bash
python -m pip install -e ".[dev]"
pytest
ruff check src tests
node --check web/app.js
```

## Public vulnerability intelligence modules

- `vanguard.intelligence.fetch_cve("CVE-2025-12345")` queries the configured official NVD CVE API v2 endpoint.
- `vanguard.intelligence.fetch_kev_catalog()` reads the public CISA KEV catalog.
- `vanguard.intelligence.enrich_with_kev(records, catalog)` marks whether a CVE appears in KEV and retains the catalog's dates/actions.
- `vanguard.prioritization.assess_priority(record)` returns a P1–P4 triage priority, score, rationale, and limitations.

Connectors use fixed official endpoints, a timeout and response-size limit. Network behavior should be tested with mocks; normal unit tests do not need live internet access. Respect upstream availability, rate limits and terms of use. No API key is required by this initial connector implementation.

## Web/PWA prototype

The browser prototype includes a local asset inventory with add/delete controls and Spanish, Brazilian Portuguese and English labels. Records use this browser's local storage; they are not sent to a server and do not synchronize with the desktop app. Clearing browser storage may remove them.

Serve the `web` directory over localhost (service workers require localhost or HTTPS):

```bash
python -m http.server 8080 --directory web
```

Open http://localhost:8080. In a supported browser, use the browser's install option to install the PWA. This prototype does not have privileged access to the computer or run security scans. The inventory is not vulnerability intelligence and does not represent verified security findings.

## Safety boundaries

- No active network scanning or exploitation is implemented.
- Assets are manually entered by the user; only assess systems for which you have explicit authorization.
- Public threat intelligence is not proof that a device is infected or vulnerable.
- Do not put secrets, credentials, or customer-sensitive data in test records or source control.
- Treat imported descriptions and references as untrusted data, not executable instructions.
- Never describe placeholder UI as a live detection.

## Planned milestones

1. Local inventory and desktop shell.
2. Public CVE and CISA KEV connectors with source timestamps and clear failure handling. **Initial parser/connectors now exist; UI and persistence integration remain.**
3. Asset-to-vulnerability evidence model and transparent prioritization.
4. PDF executive/technical reports and full Spanish / Brazilian Portuguese / English localization.
5. Security review, accessibility checks, broader automated tests and Windows packaging.
6. Later, separately scoped authorized assessments and enterprise integrations.
