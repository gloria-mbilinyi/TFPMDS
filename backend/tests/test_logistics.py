from app.models import Shipment
from helpers import account, auth
from test_orders import setup_order


def paid_order(client, db):
    farmer,buyer,produce,order,body=setup_order(client,db)
    client.post(f'/api/orders/{order["id"]}/decision',headers=auth(farmer),json={'action':'accept'})
    payment=client.post('/api/payments',headers=auth(buyer)|{'Idempotency-Key':'logistics-pay01'},json={'order_id':order['id'],'provider':'mpesa','phone':buyer.phone}).json()
    result=client.post(f'/api/payments/{payment["id"]}/simulate',headers=auth(buyer),json={'outcome':'successful'})
    assert result.status_code == 200, result.text
    return farmer,buyer,order,db.query(Shipment).one()


def test_delivery_tracking_and_completion(client, db):
    farmer,buyer,order,shipment=paid_order(client,db)
    officer=account(db,'logistics'); driver=account(db,'transporter'); other=account(db,'transporter')
    assert client.post(f'/api/shipments/{shipment.id}/assign',headers=auth(buyer),json={'transporter_id':driver.id}).status_code == 403
    assert client.post(f'/api/shipments/{shipment.id}/assign',headers=auth(officer),json={'transporter_id':driver.id}).json()['status'] == 'assigned'
    assert len(client.get('/api/shipments',headers=auth(driver)).json()) == 1
    assert client.get('/api/shipments',headers=auth(other)).json() == []
    assert client.get(f'/api/shipments/{shipment.id}',headers=auth(other)).status_code == 403
    assert client.post(f'/api/shipments/{shipment.id}/status',headers=auth(other),json={'status':'ready_for_pickup','location':'Morogoro'}).status_code == 403
    for state in ['ready_for_pickup','picked_up','in_transit','delivered']:
        response=client.post(f'/api/shipments/{shipment.id}/status',headers=auth(driver),json={'status':state,'location':'Dar es Salaam','note':'Delivery progress recorded.'})
        assert response.json()['status'] == state, response.text
    for party in [farmer,buyer]:
        tracking=client.get(f'/api/shipments/{shipment.id}',headers=auth(party)).json()
        assert len(tracking['history']) == 6 and tracking['status'] == 'delivered'
    assert client.post(f'/api/orders/{order["id"]}/decision',headers=auth(buyer),json={'action':'complete'}).json()['status'] == 'completed'
    assert client.post(f'/api/shipments/{shipment.id}/status',headers=auth(driver),json={'status':'in_transit','location':'Morogoro'}).status_code == 409
    assert client.post(f'/api/shipments/{shipment.id}/status',headers=auth(driver),json={'status':'return_requested','location':'Dar','note':'Buyer requested return'}).status_code == 403
    assert client.post(f'/api/shipments/{shipment.id}/status',headers=auth(officer),json={'status':'return_requested','location':'Dar','note':'Approved exception return'}).status_code == 200
    assert client.post(f'/api/shipments/{shipment.id}/status',headers=auth(driver),json={'status':'returned','location':'Morogoro','note':'Returned to farmer'}).status_code == 200
