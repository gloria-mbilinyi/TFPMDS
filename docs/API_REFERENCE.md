# REST API reference

Local API: http://127.0.0.1:8010. Interactive documentation: `/docs`. Machine-readable contract: `openapi.json`.

JSON bodies use UTF-8. Protected routes require `Authorization: Bearer <JWT>`. Login accepts JSON email/password. Order/payment initiation require `Idempotency-Key` (8-80 characters). Never send a PIN.

| Method | Route | Operation |
| --- | --- | --- |
| GET | /api/health | Health |
| POST | /api/auth/register | Register |
| POST | /api/auth/login | Login |
| GET | /api/auth/me | Me |
| POST | /api/auth/logout | Logout |
| PATCH | /api/users/me | Update Profile |
| GET | /api/admin/users | List Users |
| POST | /api/admin/users/{user_id}/approval | Approve |
| PATCH | /api/admin/users/{user_id}/active | Set Active |
| POST | /api/admin/staff | Create Staff |
| GET | /api/users/transporters | Transporters |
| GET | /api/produce/mine | Own Produce |
| POST | /api/produce | Create |
| GET | /api/produce | Search |
| PATCH | /api/produce/{produce_id} | Edit |
| DELETE | /api/produce/{produce_id} | Deactivate |
| GET | /api/produce/{produce_id} | Detail |
| GET | /api/market-prices | Market Prices |
| POST | /api/orders | Create |
| GET | /api/orders | History |
| GET | /api/orders/{order_id} | Detail |
| POST | /api/orders/{order_id}/decision | Decide |
| POST | /api/payments | Initiate |
| GET | /api/payments | Transactions |
| POST | /api/payments/mock-callback | Callback |
| GET | /api/payments/{payment_id} | Status |
| POST | /api/payments/{payment_id}/simulate | Simulate |
| GET | /api/payments/{payment_id}/receipt | Receipt |
| GET | /api/shipments | List Shipments |
| GET | /api/shipments/{shipment_id} | Detail |
| POST | /api/shipments/{shipment_id}/assign | Assign |
| POST | /api/shipments/{shipment_id}/status | Progress |
| GET | /api/notifications | History |
| POST | /api/notifications/read-all | Read All |
| POST | /api/notifications/{notification_id}/read | Mark Read |
| GET | /api/admin/sms-log | Sms Log |
| GET | /api/reports/summary | Summary |
| POST | /api/admin/market-prices | Save Market Price |
| DELETE | /api/admin/market-prices/{price_id} | Delete Price |

## Authorization and validation

Public: health, registration, login, produce search/detail and reference prices. Profile/notifications are current-user scoped. Listing writes require an approved farmer owner. Orders/payments require an approved buyer. Decisions require the responsible farmer or ordering buyer for the relevant action. Receipt/tracking access is limited to trading parties or authorized staff; transporters see assigned shipments. Admin routes require an active approved administrator. Shipment writes require approved logistics/admin staff or the assigned approved transporter; return requests require logistics authority and a reason.

Errors: 401 invalid/expired/revoked session; 403 authorization/approval failure; 404 missing/unavailable record; 409 business conflict/invalid transition; 422 invalid input. Business errors use `detail: {code, message}`. Pydantic returns its standard `detail` array. Database conflicts do not expose SQL or secrets.

Profile changes accept a full profile payload. Role, email, approval and active status cannot be changed there. Approved farmer edits trigger renewed verification. Produce deactivation preserves history.

Stock is whole kg and money is integer TZS. Orders contain 1-30 distinct lines from one farmer. Reservations/persistence roll back together. Rejection/cancellation releases stock once after a conditional transition. Cancellation is unavailable during a pending payment or after success. Failed/cancelled attempts can retry.

Internal callbacks require `X-Mock-Secret` matching the server configuration. The browser uses the owner-only `/simulate` route and never receives that secret. Identical terminal callbacks, including races, are idempotent. Conflicting outcomes return 409. Receipts/shipments are unique per paid order.

Shipment responses expose `next_states` from the validation graph. Assignment moves pending_arrangement/awaiting_transporter/assignment_failed/assigned to assigned. Delivered cannot ordinarily revert. Explicit returns use return_requested -> returned and do not imply refund/restocking.

Prices are illustrative references with a unique crop/region pair. Reports total successful simulated payments; returns remain included until refunds exist. The frontend generates CSV from the same response.

## Example order body

```json
{"items":[{"produce_id":1,"quantity_kg":50}],"delivery_address":"Kariakoo, Dar es Salaam"}
```

## Example payment body

```json
{"order_id":1,"provider":"mpesa","phone":"+255712345678"}
```

Use a valid token and unique idempotency key. Obtain current IDs from responses; example IDs are not guaranteed in every database.
