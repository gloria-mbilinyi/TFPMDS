# TFPMDS demonstration guide

Start and seed using the README. Open http://127.0.0.1:5173. All seeded `@tfpmds.demo` accounts use `DemoPass123!`. Use unique `@example.com` emails for fresh registrations. Never enter a real mobile money PIN.

## Full acceptance journey

| Step | Actor / screen | Action and observable result |
| --- | --- | --- |
| 1 | Public / farmer registration | Enter name, mobile number, location, acreage, crops, email and password. Account starts pending. |
| 2 | Administrator / Administration | Review the farmer profile, record a verification note and approve. Status notification is logged. |
| 3 | New farmer / My produce | Publish Rice with 600 kg, TZS 2,100/kg and a valid harvest date. Listing appears publicly. |
| 4 | Public and administrator | Register and approve a buyer business profile. |
| 5 | Buyer / Marketplace | Search the listing; choose Rice, Morogoro, price bounds and minimum quantity. |
| 6 | Buyer / Produce details | Order 50 kg to Kariakoo warehouse, Dar es Salaam. Pending order totals TZS 105,000; stock becomes 550 kg. |
| 7 | Farmer / Orders | Accept the order with a note. Buyer is notified. |
| 8 | Buyer / Orders → Simulate payment | Initiate M-Pesa, Airtel Money or Tigo-Pesa; choose Simulate success. One receipt and shipment are created. |
| 9 | Buyer / Receipt | Review reference, parties, value and simulation label. Print / Save PDF opens the browser print dialog. |
| 10 | Logistics officer / Shipments | Assign Safari Fresh Transport to the paid order. Assignment and notification are logged. |
| 11 | Transporter / Shipments | Record Ready for pickup, Picked up, In transit and Delivered with locations/notes. |
| 12 | Farmer and buyer / Tracking and Orders | Both see all six tracking events; buyer confirms receipt and completes the order. |
| 13 | Administrator / Orders, receipt, Reports | Review the completed transaction and successful simulated gross sales. |
| 14 | Administrator / SMS log | Review registration, order, payment and delivery rows. No real SMS is sent. |

The observed 18 November 2026 browser run created order #4 for TZS 105,000, receipt `TFP-6150D9B221C74F79` and shipment `TZ-D6F8BD740AB9`. These identify that run only; later references differ. The working local database retains this synthetic journey. A fresh seed starts with the original three sample orders. See `evidence/browser-journey.json` for actual observations.

## Negative and exception cases

- Pending buyers cannot order; pending farmers cannot publish. Profiles reject role mass assignment.
- Invalid quantities/prices/harvest dates are rejected. An order larger than stock rolls back.
- Rejection or pre-payment cancellation releases stock once. Repeating a terminal decision fails.
- Failed/cancelled payment simulations create no receipt/shipment; a new attempt can retry.
- Identical successful callbacks are idempotent, including concurrent replay; conflicting terminal outcomes fail.
- An unrelated farmer cannot decide an order; an unassigned transporter cannot update it.
- Delivered shipments cannot return to In transit. Logistics may explicitly request a return with a reason; an authorized transporter can record Returned. Refunds and automatic restocking are outside scope.

## Screens and evidence

All 18 required screens are present: landing; farmer registration; buyer registration; login; farmer dashboard; produce management; marketplace; produce details; buyer orders; payment simulation; receipt; logistics dashboard; transporter dashboard; tracking; administrator dashboard; market prices; reports; notifications. Profile management and SMS history are additional screens. Logistics/transporter dashboards share a role-aware shipment component with distinct data/actions.

`screenshots/` contains genuine captures of the landing, dashboard, listing management, approvals, filtered marketplace, receipt, assignment, tracking, completed order, reports, SMS history and mobile marketplace. `farmer-dashboard-full.jpg` is the complete dashboard. The earlier shorter viewport capture is retained as development evidence.

Use `scripts/verify.ps1` for API/unit/build/UML checks. The optional Playwright harness is documented in the README; its standard browser launch was blocked in the restricted shell, while the supported in-app browser journey passed.
