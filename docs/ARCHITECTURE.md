# Requirements and architecture

## Boundaries

The React interface calls versioned REST endpoints under `/api`. FastAPI routers validate Pydantic inputs and authorize the actor. Application services coordinate domain transitions, inventory updates and provider interfaces within a SQLAlchemy transaction. Persistence models have foreign keys, uniqueness and check constraints. SQLite is the development database; portable types and conditional updates support a future PostgreSQL migration, which requires migrations and integration testing before production.

Dependency direction: interface -> application services -> domain/persistence and provider protocols. Provider adapters implement payment and SMS interfaces. Reporting reads persistence. Persistence never imports API routers. Notification delivery is a durable simulated log in the same transaction as business changes; no external calls occur during commits. A production outbox worker is future work.

## Actors and trust

Public registration permits only `farmer` and `buyer`. Both begin `pending`, may log in and edit their profiles, and require administrator approval before trading. Staff accounts are seeded locally; administrators may create staff through an admin endpoint. Bearer JWTs expire, have unique identifiers and are revoked on logout. Roles and active/approval status are loaded from the database on every request. Passwords use Argon2. API secrets come from environment configuration; no real provider credentials exist.

## Invariants

Quantities are integer kilograms and currency is integer TZS, avoiding floating-point stock and currency arithmetic. A purchase order contains one or more items from exactly one farmer. Each reservation uses `UPDATE produce SET available_kg = available_kg - q WHERE available_kg >= q AND active = true`; the transaction rolls back if any item fails. Rejection/cancellation releases reservations once. Idempotency keys prevent duplicate order submissions and payment initiation. Conditional status updates serialize competing transitions. Paid orders cannot be cancelled through the ordinary cancellation path; refunds are outside scope.

Only approved owners modify produce. Only the responsible farmer approves an order. Only accepted/awaiting-payment or payment-failed orders initiate a simulated payment. A successful terminal payment callback atomically creates one receipt and one shipment. Callbacks require an internal mock-provider secret and are idempotent. Mock outcomes are buyer initiated only through an explicitly labelled simulation route.

Shipment transitions form an explicit state graph; ordinary delivered shipments cannot move backwards. A logistics officer may explicitly start the documented return exception workflow. Buyer completion follows confirmed delivery. Both trading parties can inspect tracking history; a transporter sees assigned work only.

## Implementation plan and verification

1. Setup and evidence tooling.
2. Requirements and architecture (this document and the acceptance catalogue).
3. Database foundation with constraints and isolated test database.
4. JWT authentication, logout revocation and role guards.
5. Profile management, account verification and administration.
6. Produce CRUD and stock validation.
7. Public marketplace filters, detail and market prices.
8. Atomic multi-item orders, acceptance, rejection, cancellation and history.
9. Simulated provider adapters, payment callbacks, duplicate prevention and receipts.
10. Logistics assignment, shipment state graph and tracking history.
11. In-app and simulated SMS notification history.
12. Administration, transaction monitoring and reporting.
13. Realistic illustrative Tanzania seed data and integrated React screens.
14. Genuine draw.io XML sequence, communication, two state machines and package/class diagrams, with PNG exports.
15. Backend, frontend and end-to-end regression tests, including authorization and race-sensitive invariants.
16. Academic proposal in Markdown and PDF, with traceability and measured acceptance.
17. Repeatable demonstration, captured UI evidence and local-only handoff.

Tests use temporary SQLite databases. UI tests cover interactions and integration journeys against a running backend. Checks are recorded in the agent log. Requirement coverage is counted only after implementation and tests exist; the denominator is frozen by `docs/requirements.json` before development.

## Deliberate limits

Single deployment, local demo; no real payments, PINs, SMS, identity verification service, live market-price feed, GPS, refunds, offline sync or production operations. Seed prices are illustrative, not market advice. Farmer approval is an administrator decision supported by profile information; document upload and government identity checks are future improvements. No claim of deployment or production readiness is made.

## Technical references

- FastAPI authentication: https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
- SQLAlchemy sessions: https://docs.sqlalchemy.org/en/20/orm/session_basics.html
- SQLite transaction considerations: https://docs.sqlalchemy.org/en/20/dialects/sqlite.html
