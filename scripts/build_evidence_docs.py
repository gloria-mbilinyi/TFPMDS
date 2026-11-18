"""Generate acceptance, API and SQL references from actual project evidence."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.main import app
from app.db import Base
from sqlalchemy.schema import CreateIndex, CreateTable
from sqlalchemy.dialects import sqlite

DOCS=ROOT/'docs'
groups={
 'A':('backend/app/auth.py; backend/app/users.py; frontend/src/AuthPages.tsx','classes-identity-produce.drawio',[
   'test_registration_login_logout','test_registration_login_logout','test_approvals_and_profiles','test_approvals_and_profiles','test_approvals_and_profiles','test_approvals_and_profiles','test_approvals_and_profiles','test_complete_registration_to_delivery_journey']),
 'B':('backend/app/produce.py; frontend/src/ProducePages.tsx','classes-identity-produce.drawio',[
   'test_produce_management']*7+['test_produce_invalid_values']),
 'C':('backend/app/auth.py; backend/app/marketplace.py; backend/app/users.py; frontend/src/Marketplace.tsx','classes-identity-produce.drawio',[
   'test_complete_registration_to_delivery_journey','test_approvals_and_profiles','test_complete_registration_to_delivery_journey','test_buyer_profile_management','test_marketplace_search_filters','test_marketplace_search_filters','test_marketplace_search_filters']),
 'D':('backend/app/orders.py; frontend/src/OrderPages.tsx; frontend/src/ProducePages.tsx','purchase-order-state.drawio; classes-orders-payments.drawio',[
   'test_order_reservation_acceptance_and_history','test_order_rejection_cancellation_and_validation','test_complete_registration_to_delivery_journey','test_order_rejection_cancellation_and_validation','test_delivery_tracking_and_completion','test_order_reservation_acceptance_and_history','test_competing_buyers_cannot_oversell']),
 'E':('backend/app/payments.py; backend/app/integrations.py; frontend/src/OrderPages.tsx','classes-orders-payments.drawio; purchase-order-state.drawio',[
   'test_successful_payment_receipt_and_idempotency[mpesa]','test_successful_payment_receipt_and_idempotency[mpesa]',
   'test_successful_payment_receipt_and_idempotency[airtel_money]','test_successful_payment_receipt_and_idempotency[tigo_pesa]',
   'test_successful_payment_receipt_and_idempotency[mpesa]','test_successful_payment_receipt_and_idempotency[mpesa]',
   'test_successful_payment_receipt_and_idempotency[mpesa]','test_payment_failure_cancellation_and_retry[failed]','test_competing_callbacks_are_idempotent']),
 'F':('backend/app/logistics.py; backend/app/domain.py; frontend/src/LogisticsPages.tsx','shipment-state.drawio; classes-logistics-notifications.drawio',[
   'test_complete_registration_to_delivery_journey','test_complete_registration_to_delivery_journey','test_delivery_tracking_and_completion','test_delivery_tracking_and_completion','test_delivery_tracking_and_completion','test_delivery_tracking_and_completion','test_delivery_tracking_and_completion','test_delivery_tracking_and_completion']),
 'G':('backend/app/users.py; backend/app/reporting.py; backend/app/payments.py; frontend/src/AdminPages.tsx','package-overview.drawio; classes-identity-produce.drawio',[
   'test_reports_and_market_prices','test_approvals_and_profiles','test_approvals_and_profiles','test_admin_user_management','test_successful_payment_receipt_and_idempotency[mpesa]','test_reports_and_market_prices','test_reports_and_market_prices','test_reports_and_market_prices']),
 'H':('backend/app/notifications.py; backend/app/notification_api.py; frontend/src/NotificationPage.tsx','classes-logistics-notifications.drawio',[
   'test_notification_and_sms_history','test_notification_and_sms_history','test_notification_and_sms_history','test_notification_and_sms_history','test_complete_registration_to_delivery_journey','test_notification_and_sms_history']),
}


def test_results(name):
    root=ET.parse(DOCS/'evidence'/f'{name}-junit.xml').getroot();cases=list(root.iter('testcase'));passed={}
    for case in cases:
        if not any(case.find(t) is not None for t in ['failure','error','skipped']):
            passed[case.get('name')]=case.get('classname')
    return {'total':len(cases),'passed':len(passed),'failed':sum(c.find('failure') is not None or c.find('error') is not None for c in cases),
            'skipped':sum(c.find('skipped') is not None for c in cases)},passed


def build():
    backend,passed=test_results('backend');frontend,_=test_results('frontend')
    requirements=json.loads((DOCS/'requirements.json').read_text(encoding='utf-8'))
    journey=json.loads((DOCS/'evidence/browser-journey.json').read_text(encoding='utf-8'))
    assert journey['result']=='passed' and [s['step'] for s in journey['steps']]==list(range(1,15))
    rows=[]
    for req in requirements:
        module=req['id'][0];index=int(req['id'][1:])-1;files,uml,tests=groups[module];test=tests[index]
        assert test in passed,f'No passing test evidence for {req["id"]}: {test}'
        test_file='backend/'+passed[test].replace('.','/')+'.py'
        for path in [*files.split('; '),test_file]:assert (ROOT/path).exists(),path
        for path in uml.split('; '):assert (DOCS/'uml'/path).exists(),path
        rows.append(req|{'status':'passed','implementation':files.split('; '),'test_file':test_file,'test':test,
                         'uml':['sequence.drawio','communication.drawio',*uml.split('; ')]})
    summary={'generated_at':datetime.now(timezone.utc).isoformat(),'functional_total':len(rows),'functional_passed':len(rows),
             'functional_coverage_percent':round(100*len(rows)/len(requirements),1),'backend':backend,'frontend':frontend,
             'browser_journey':'14 steps passed in supported in-app browser','uml_models':8,'requirements':rows,
             'measurement':'Requirement acceptance coverage, not statement/branch coverage or a production-readiness score.'}
    (DOCS/'evidence/acceptance-results.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    lines=['# Requirements traceability and acceptance checklist','',
      f'**{len(rows)}/{len(requirements)} requirements passed (100%).** The denominator is the 61 functional bullet requirements frozen before implementation. Every named test appears as passed in the stored JUnit evidence.',
      '',summary['measurement'],'','Backend: '+str(backend)+'. Frontend: '+str(frontend)+'. Browser observations are stored in `evidence/browser-journey.json`.',
      '', 'The checklist verifies local simulated workflows. It does not certify real provider integrations, production scale, formal UML conformance, penetration testing or full browser/OS accessibility.','',
      '| ID | Requirement | Implementation | Passing test evidence | UML source |','| --- | --- | --- | --- | --- |']
    for r in rows:
        lines.append('| '+r['id']+' | '+r['requirement']+' | '+'; '.join(r['implementation'])+' | '+r['test_file']+' :: '+r['test']+' | '+'; '.join('uml/'+u for u in r['uml'][2:])+' |')
    lines+=['','Every row also maps to the comprehensive sequence and communication models. A passing integration test can support several acceptance requirements when its assertions and exercised workflow cover them. Provider rows map to exact parameterized test cases. Failure and cancellation are both tested in the two parameterized retry cases. Other invariant tests cover multi-item rollback, competing buyers, callback races, expired/revoked tokens and role mass assignment.','']
    (DOCS/'REQUIREMENTS_TRACEABILITY.md').write_text('\n'.join(lines),encoding='utf-8')
    openapi=app.openapi();(DOCS/'openapi.json').write_text(json.dumps(openapi,indent=2)+'\n',encoding='utf-8')
    api_lines=['# REST API reference','','Local API: http://127.0.0.1:8010. Interactive documentation: `/docs`. Machine-readable contract: `openapi.json`.','',
      'JSON bodies use UTF-8. Protected routes require `Authorization: Bearer <JWT>`. Login accepts JSON email/password. Order/payment initiation require `Idempotency-Key` (8-80 characters). Never send a PIN.','',
      '| Method | Route | Operation |','| --- | --- | --- |']
    for path,methods in openapi['paths'].items():
        for method,operation in methods.items():
            if method.upper() in {'GET','POST','PATCH','DELETE'}:api_lines.append(f'| {method.upper()} | {path} | {operation.get("summary","")} |')
    api_lines+=['','## Authorization and validation','',
      'Public: health, registration, login, produce search/detail and reference prices. Profile/notifications are current-user scoped. Listing writes require an approved farmer owner. Orders/payments require an approved buyer. Decisions require the responsible farmer or ordering buyer for the relevant action. Receipt/tracking access is limited to trading parties or authorized staff; transporters see assigned shipments. Admin routes require an active approved administrator. Shipment writes require approved logistics/admin staff or the assigned approved transporter; return requests require logistics authority and a reason.','',
      'Errors: 401 invalid/expired/revoked session; 403 authorization/approval failure; 404 missing/unavailable record; 409 business conflict/invalid transition; 422 invalid input. Business errors use `detail: {code, message}`. Pydantic returns its standard `detail` array. Database conflicts do not expose SQL or secrets.','',
      'Profile changes accept a full profile payload. Role, email, approval and active status cannot be changed there. Approved farmer edits trigger renewed verification. Produce deactivation preserves history.','',
      'Stock is whole kg and money is integer TZS. Orders contain 1-30 distinct lines from one farmer. Reservations/persistence roll back together. Rejection/cancellation releases stock once after a conditional transition. Cancellation is unavailable during a pending payment or after success. Failed/cancelled attempts can retry.','',
      'Internal callbacks require `X-Mock-Secret` matching the server configuration. The browser uses the owner-only `/simulate` route and never receives that secret. Identical terminal callbacks, including races, are idempotent. Conflicting outcomes return 409. Receipts/shipments are unique per paid order.','',
      'Shipment responses expose `next_states` from the validation graph. Assignment moves pending_arrangement/awaiting_transporter/assignment_failed/assigned to assigned. Delivered cannot ordinarily revert. Explicit returns use return_requested -> returned and do not imply refund/restocking.','',
      'Prices are illustrative references with a unique crop/region pair. Reports total successful simulated payments; returns remain included until refunds exist. The frontend generates CSV from the same response.','',
      '## Example order body','', '```json','{"items":[{"produce_id":1,"quantity_kg":50}],"delivery_address":"Kariakoo, Dar es Salaam"}','```','',
      '## Example payment body','', '```json','{"order_id":1,"provider":"mpesa","phone":"+255712345678"}','```','',
      'Use a valid token and unique idempotency key. Obtain current IDs from responses; example IDs are not guaranteed in every database.','']
    (DOCS/'API_REFERENCE.md').write_text('\n'.join(api_lines),encoding='utf-8')
    ddl=['-- Generated from SQLAlchemy metadata; monetary totals use BIGINT.','PRAGMA foreign_keys=ON;','']
    for table in Base.metadata.sorted_tables:
        ddl.append(str(CreateTable(table).compile(dialect=sqlite.dialect())).strip()+';\n')
        for index in sorted(table.indexes,key=lambda i:i.name):ddl.append(str(CreateIndex(index).compile(dialect=sqlite.dialect()))+';\n')
    (DOCS/'database-schema.sql').write_text('\n'.join(ddl)+'\n',encoding='utf-8')
    print(f'Acceptance: {len(rows)}/{len(requirements)} (100%); backend {backend}; frontend {frontend}; {len(openapi["paths"])} API paths.')


if __name__=='__main__':build()
