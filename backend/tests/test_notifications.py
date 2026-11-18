from app.models import Notification
from helpers import account, auth
from test_logistics import paid_order


def test_notification_and_sms_history(client, db):
    farmer,buyer,order,shipment=paid_order(client,db)
    records=client.get('/api/notifications',headers=auth(buyer)).json()
    assert {r['kind'] for r in records} >= {'order','payment'}
    assert all(r['sms_status']=='simulated' and r['sms_reference'].startswith('SMS-SIM-') for r in records)
    assert client.post(f'/api/notifications/{records[0]["id"]}/read',headers=auth(farmer)).status_code == 403
    assert client.post(f'/api/notifications/{records[0]["id"]}/read',headers=auth(buyer)).status_code == 200
    assert len(client.get('/api/notifications?unread_only=true',headers=auth(buyer)).json()) == len(records)-1
    assert client.post('/api/notifications/read-all',headers=auth(buyer)).status_code == 200
    assert client.get('/api/notifications?unread_only=true',headers=auth(buyer)).json() == []
    admin=account(db,'administrator')
    assert len(client.get('/api/admin/sms-log',headers=auth(admin)).json()) == db.query(Notification).count()
    assert client.get('/api/admin/sms-log',headers=auth(buyer)).status_code == 403
