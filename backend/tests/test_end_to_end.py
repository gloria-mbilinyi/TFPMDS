"""The full 14-step academic acceptance journey, using fresh registrations."""
from helpers import account, auth, registration
from test_produce import listing


def test_complete_registration_to_delivery_journey(client,db):
    admin=account(db,'administrator'); officer=account(db,'logistics'); driver=account(db,'transporter')
    def register_and_login(role):
        body=registration(role)
        result=client.post('/api/auth/register',json=body)
        assert result.status_code==201 and result.json()['status']=='pending'
        login=client.post('/api/auth/login',json={'email':body['email'],'password':body['password']})
        assert login.status_code==200
        return result.json(),{'Authorization':'Bearer '+login.json()['access_token']}
    farmer,farmer_auth=register_and_login('farmer')
    assert client.post('/api/produce',headers=farmer_auth,json=listing()).status_code==403
    assert client.post(f'/api/admin/users/{farmer["id"]}/approval',headers=auth(admin),json={'status':'approved','note':'Farm profile reviewed for academic demonstration.'}).status_code==200
    produce=client.post('/api/produce',headers=farmer_auth,json=listing()).json()
    buyer,buyer_auth=register_and_login('buyer')
    assert client.post(f'/api/admin/users/{buyer["id"]}/approval',headers=auth(admin),json={'status':'approved','note':'Buyer profile reviewed.'}).status_code==200
    search=client.get('/api/produce?q=rice&region=Morogoro&min_quantity=50').json()
    assert search[0]['id']==produce['id']
    order=client.post('/api/orders',headers=buyer_auth|{'Idempotency-Key':'acceptance-order01'},json={'items':[{'produce_id':produce['id'],'quantity_kg':50}],'delivery_address':'Kariakoo, Dar es Salaam'}).json()
    assert client.post(f'/api/orders/{order["id"]}/decision',headers=farmer_auth,json={'action':'accept'}).json()['status']=='accepted'
    payment=client.post('/api/payments',headers=buyer_auth|{'Idempotency-Key':'acceptance-pay0001'},json={'order_id':order['id'],'provider':'airtel_money','phone':buyer['phone']}).json()
    assert client.post(f'/api/payments/{payment["id"]}/simulate',headers=buyer_auth,json={'outcome':'successful'}).status_code==200
    assert client.get(f'/api/payments/{payment["id"]}/receipt',headers=buyer_auth).json()['amount_tzs']==110000
    shipment=client.get('/api/shipments',headers=auth(officer)).json()[0]
    assert client.post(f'/api/shipments/{shipment["id"]}/assign',headers=auth(officer),json={'transporter_id':driver.id}).status_code==200
    for state in ['ready_for_pickup','picked_up','in_transit','delivered']:
        assert client.post(f'/api/shipments/{shipment["id"]}/status',headers=auth(driver),json={'status':state,'location':'Dar es Salaam','note':'Acceptance journey milestone.'}).status_code==200
    for party in [farmer_auth,buyer_auth]:
        track=client.get(f'/api/shipments/{shipment["id"]}',headers=party).json()
        assert track['status']=='delivered' and len(track['history'])==6
        notices=client.get('/api/notifications',headers=party).json()
        assert {n['kind'] for n in notices}>={'registration','order','payment','delivery'}
        assert all(n['sms_status']=='simulated' for n in notices)
    assert client.post(f'/api/orders/{order["id"]}/decision',headers=buyer_auth,json={'action':'complete'}).json()['status']=='completed'
    report=client.get('/api/reports/summary',headers=auth(admin)).json()
    assert report['gross_sales_tzs']==110000 and report['completed_orders']==1
    log=client.get('/api/admin/sms-log',headers=auth(admin)).json()
    assert len(log)>=20 and all(row['sms_reference'].startswith('SMS-SIM-') for row in log)
