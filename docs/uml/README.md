# Editable UML source and image exports

Open any `.drawio` file with the free diagrams.net desktop app or **File → Open from → Device** at https://app.diagrams.net/. Every object, relationship, message and fragment is an editable mxGraph cell. These are real, uncompressed draw.io XML documents, not images embedded inside XML.

The eight canonical models are:

1. `sequence.drawio`: one comprehensive interaction with 15 lifelines, 84 messages, activations, calls/returns, asynchronous logical notifications and alt/opt/loop fragments across the four required processes.
2. `communication.drawio`: one corresponding communication diagram. Four process views reuse the same object identities. Links carry the same message numbers, including nested callback number `3.6.1`; the adjacent message register retains each conditional interaction.
3. `purchase-order-state.drawio`: persistent order states, a transient validation state, rejection/cancellation/payment failure, and explicit delivery-return exceptions.
4. `shipment-state.drawio`: the exact status graph from `backend/app/domain.py`, plus assignment/reassignment transitions. The transition register includes event, guard and action specifications.
5. `package-overview.drawio`: conceptual responsibility packages, concrete module mapping and acyclic dependencies.
6. `classes-identity-produce.drawio`: user roles, profiles, produce, market prices and authentication/produce service operations.
7. `classes-orders-payments.drawio`: order composition, inventory snapshots, payment attempts, receipt uniqueness and the provider protocol.
8. `classes-logistics-notifications.drawio`: shipments, assigned transporters, tracking composition, notification history and the SMS port/mock.

The PNG beside each source is generated from the exact same geometry by `scripts/uml_canvas.py`; it is a raster export, not a screenshot. The small renderer supports the shapes used by these authors and is not a general draw.io renderer. Open the XML in diagrams.net to edit it or use diagrams.net's native exporter after manual edits. `previews/` contains readable process panels derived from the two comprehensive diagrams for insertion in the PDF. They do not constitute extra UML models.

Regenerate from the repository root:

```powershell
.\.venv\Scripts\python.exe scripts\generate_interaction_uml.py
.\.venv\Scripts\python.exe scripts\generate_structure_uml.py
.\.venv\Scripts\python.exe scripts\validate_uml.py
```

Role classes such as Farmer and Transporter are explicitly labelled conceptual views of User, implemented by `User.role` rather than separate ORM subclasses/tables. The class diagrams show service operations on service classes; domain entities contain mapped attributes. Composition is limited to the actual ORM-owned OrderItem and TrackingEvent collections. PaymentReceipt is an associated record, not a cascading composition. Shipment assignment is an association; deleting or deactivating a transporter never owns/deletes a shipment.

Asynchronous arrows express logical notification events. The local mock records them synchronously in the request transaction; no production message queue or external SMS service is running. Mock payment completion can enter through the authenticated callback or the buyer-owned simulation endpoint; terminal identical replays are idempotent. No diagram asserts a real mobile-money integration.
