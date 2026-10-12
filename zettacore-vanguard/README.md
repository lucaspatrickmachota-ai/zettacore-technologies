# ZettaCore Vanguard

**INTELLIGENCE. SECURITY. RESILIENCE.**

Vanguard is an independent ZettaCore Technologies cybersecurity product in active early development. It contains a local-first PySide6 desktop app, an installable web/PWA shell, public vulnerability-intelligence connectors, local persistence and an initial PDF reporting module. It does not modify ZettaCore Sentinel.

## Current working capabilities

- Manage an authorized asset inventory locally in SQLite.
- Look up a specific CVE through the NIST NVD CVE API v2.
- Enrich the result using the CISA Known Exploited Vulnerabilities (KEV) catalog.
- Store normalized CVE metadata and a history of lookup attempts in the local database.
- View saved records with an explainable P1–P4 review priority.
- Export a PDF report in English, Spanish or Brazilian Portuguese.
- Use the separate web/PWA prototype in Spanish, Brazilian Portuguese and English; its browser inventory is local to that browser and does not sync with the desktop app.

**Important limitations:** this is an MVP, not a complete security product. The desktop UI currently performs single-CVE lookups, not a full catalog synchronization. It does not yet match assets to affected products/versions, confirm asset findings, run active scans, detect malware or perform remediation. A CVE or KEV listing is not proof that an asset is vulnerable or compromised. The P1–P4 score is a review heuristic, not a probability of exploitation. The desktop interface is currently English-only.

## Requirements and install

Python 3.11+ is recommended. The desktop UI uses PySide6; PDF export uses ReportLab.

```bash
cd zettacore-vanguard
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
python -m pip install -e ".[dev,reports]"
python -m vanguard
```

The app stores its SQLite database in the user's application-data directory, not inside the source checkout. The web/PWA stores its inventory separately in the current browser's local storage.

## Run tests and quality checks

```bash
python -m pip install -e ".[dev,reports]"
pytest -q
ruff check src tests
node --check web/app.js
```

The CI workflow runs these checks on relevant changes. The test suite uses mocked source responses for network-related behavior; a passing test run does not imply that upstream APIs are currently reachable.

## Public vulnerability intelligence

- The intelligence module's fetch_cve function queries NIST NVD.
- The fetch_kev_catalog function reads the public CISA KEV catalog.
- The enrich_with_kev function attaches KEV status and relevant dates/actions.
- The prioritization module returns a transparent P1–P4 triage assessment with rationale and limitations.
- VulnerabilityStore persists records and sync history.
- The reporting module exports PDF reports.

Connectors use fixed official endpoints, a timeout and response-size limit. Respect upstream availability, rate limits and terms of use. A failed source lookup is reported; no vulnerability records are fabricated. Imported descriptions are treated as untrusted text.

## Web/PWA prototype

Serve the web directory over localhost (service workers require localhost or HTTPS):

```bash
python -m http.server 8080 --directory web
```

Open http://localhost:8080. In a supported browser, use the browser's install option to install the PWA. The browser prototype does not have privileged access to the computer or run security scans. Clearing browser storage may remove its records.

## Safety boundaries

- No active network scanning, exploitation or remediation is implemented.
- Only assess systems for which you have explicit authorization.
- Public threat intelligence is not proof that a device is infected or vulnerable.
- Do not put secrets, credentials, or customer-sensitive data in test records or source control.
- Never describe placeholder UI as a live detection.

## Roadmap to a distributable product

1. Stabilize the current desktop CVE lookup, local persistence and PDF export.
2. Match assets to products and versions using explicit evidence; distinguish confirmed, probable, possible and unverified.
3. Add stronger multilingual desktop UI, accessibility, error handling and offline views of saved records.
4. Add broader tests, dependency/security review and a repeatable Windows packaging workflow.
5. Build and test a Windows installer on a clean Windows environment, including install, upgrade, persistence and uninstall.
6. Only later, consider separately scoped authorized assessments and enterprise integrations.

Each milestone should ship with executable code, tests and honest documentation. The approved Vanguard emblem must be integrated when its original asset is available; do not replace it with a temporary design.
