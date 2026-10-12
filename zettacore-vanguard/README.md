# ZettaCore Vanguard

**INTELLIGENCE. SECURITY. RESILIENCE.**

Vanguard is an independent ZettaCore Technologies cybersecurity product in early development. This repository area starts with a local-first desktop prototype and an installable web/PWA shell. It does not modify ZettaCore Sentinel.

## Current status

This is a **starter scaffold**, not a finished security product. The dashboard currently manages a local asset inventory; vulnerability intelligence connectors, risk analysis, PDF reporting and active assessment are not implemented yet.

## Desktop app

Requirements: Python 3.11+ (recommended) and dependencies from `pyproject.toml`.

```bash
cd zettacore-vanguard
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m vanguard
```

The app stores its SQLite database in the user's application-data directory, not inside the source checkout.

## Run tests

```bash
python -m pip install -e ".[dev]"
pytest
```

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
- Public threat intelligence is not proof that a device is infected.
- Do not put secrets, credentials, or customer-sensitive data in test records or source control.
- Never describe placeholder UI as a live detection.

## Planned milestones

1. Local inventory and desktop shell.
2. Public CVE intelligence import with source timestamps and rate-limit handling.
3. Evidence-backed findings and transparent prioritization.
4. PDF reports and full Spanish / Brazilian Portuguese / English localization.
5. Automated tests, security review and Windows packaging.
6. Later, separately scoped authorized assessments and enterprise integrations.
