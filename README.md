# TFPMDS · Growing together

**Tanzania Farmers' Produce Marketing and Distribution System** is a working academic marketplace for farmers, buyers, administrators, logistics officers and transporters.

React + TypeScript + Tailwind CSS · FastAPI + Pydantic + SQLAlchemy · SQLite · JWT / Argon2 · Pytest / Vitest.

Mobile money and SMS are **simulations**. No real funds are moved, no PIN is requested, and no SMS is sent to a mobile network. Seed prices are illustrative.

## Run locally on Windows

Tested with Python 3.14.5, Node.js 24.20.0 and Git 2.55. Python 3.11+ and recent Node 22/24 are recommended. From the **TFPMDS repository root**:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements-lock.txt
Push-Location frontend
npm ci --no-fund --no-audit
Pop-Location
Push-Location backend
..\.venv\Scripts\python.exe -m app.seed --demo
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8010
```

Leave that terminal running. In a second terminal, from the repository root:

```powershell
cd frontend
npm run dev
```

Open [TFPMDS](http://127.0.0.1:5173), [interactive API documentation](http://127.0.0.1:8010/docs), or [API health](http://127.0.0.1:8010/api/health). Vite proxies `/api` to **8010**, selected because 8000 was occupied. If 5173 is occupied, use Vite's reported port or stop your other development server; do not stop unrelated processes.

The explicit `--demo` seed is idempotent and preserves existing work. SQLite is initialized at `tfpmds.db` in the repository root. Optional root `.env.example` documents configuration. Without `JWT_SECRET`, development generates an ignored `.development-secrets` in the repository root file. Keep it private and stable while sessions are active. All assets work locally after installation. Do not commit `.env`, secrets, the working database, `.venv` or `node_modules`.

## Demo credentials

All synthetic accounts use **`DemoPass123!`** after seeding:

| Role | Email |
| --- | --- |
| Farmer | farmer@tfpmds.demo |
| Buyer | buyer@tfpmds.demo |
| Administrator | admin@tfpmds.demo |
| Logistics officer | logistics@tfpmds.demo |
| Transporter | transporter@tfpmds.demo |

See `docs/DEMO_GUIDE.md` for the complete 14-step journey and negative cases. An optional synthetic SQLite snapshot in `demo/` preserves the observed completed browser journey; see its README before using it.

## Verification

From the root: `.\scripts\verify.ps1` (or run the individual commands in that script). Backend tests use temporary SQLite databases. The recorded result is **28 backend and 5 frontend tests passed; zero failures**, plus a passing production build and UML validation. An upstream Starlette/httpx deprecation warning is recorded.

The complete 14-step journey was also verified through real UI interactions in the supported in-app browser with fresh registrations, a CSV download and a 390 px responsive/navigation check. Evidence: `docs/evidence/browser-journey.json` and genuine `docs/screenshots/` captures. Functional acceptance coverage is measured in `docs/REQUIREMENTS_TRACEABILITY.md`; it is not code coverage or production certification.

A typed Playwright harness is included for a normal environment. Start the seeded backend/frontend, then run:

```powershell
cd frontend
npx playwright install chromium
npm run test:e2e
```

It creates synthetic demo records. The harness was typechecked; standard Chromium launch was blocked in the restricted Codex shell. The equivalent journey passed in the supported in-app browser. Do not treat the harness source as a separate passing Playwright execution.

## Architecture and deliverables

```text
backend/app/        REST feature modules, domain states, schemas, models and mock ports
backend/tests/      isolated API, authorization, concurrency and acceptance tests
frontend/src/       responsive role screens and reusable API/session/components
frontend/e2e/       repeatable Playwright journey source
docs/uml/           editable UML, PNG exports and message/dependency catalogues
docs/evidence/      actual JUnit and browser-journey evidence
docs/screenshots/   genuine UI captures
scripts/           verification, diagram, evidence and PDF tools
```

`docs/uml/` has eight real editable draw.io XML models: one sequence, one matching communication, two state machines, one overview package and three detailed package/class diagrams. Each has a PNG export. The small bundled renderer draws the same source geometry; it is not an installed draw.io desktop exporter. After editing XML in diagrams.net, use its native exporter or update the generation scripts. See `docs/uml/README.md`.

The editable academic report is `docs/TECHNICAL_PROPOSAL.md`; its PDF is `docs/TFPMDS_Technical_Proposal.pdf`. Large landscape figure sheets preserve notation legibility. Supporting documents include architecture, API reference/OpenAPI, SQL schema, traceability, demonstration guide and the agent development log.

Rebuild documentation after rerunning verification:

```powershell
.\.venv\Scripts\python.exe -m pip install -r docs\requirements-docs.txt
.\.venv\Scripts\python.exe scripts\generate_interaction_uml.py
.\.venv\Scripts\python.exe scripts\generate_structure_uml.py
.\.venv\Scripts\python.exe scripts\build_evidence_docs.py
.\.venv\Scripts\python.exe scripts\build_proposal.py
```

## Scope limits

Local academic prototype; no official Ministry endorsement or production deployment. There are no real payment/SMS providers, GPS feed, identity-document checks, refunds, password recovery, rate limiting, production monitoring, offline sync or PostgreSQL deployment. Quantities are whole kg, area is whole acres and currency is integer TZS. Returned goods are not automatically restocked/refunded. Gross simulated sales include returns until a future refund workflow exists.

## Local history and your later push

The official remote is `https://github.com/gloria-mbilinyi/TFPMDS.git`. **Codex did not push**, add collaborators, change ownership, rewrite history or modify global author settings. The human confirmed the repository-local author `prettyglory <gloriambilinyi5@gmail.com>`.

When ready, execute these commands yourself from this repository:

```powershell
git status
git remote -v
git log --oneline --reverse
git fetch origin
git push -u origin main
```

Authenticate as **gloria-mbilinyi**. If necessary, run `git credential-manager github login --username gloria-mbilinyi --device` in your own terminal. If the remote changed and rejects the push, inspect and merge that work; do not force-push or rewrite the local milestones. Actual commit hashes and test results are in `docs/AGENT_DEVELOPMENT_LOG.md` and the closing history ledger.
