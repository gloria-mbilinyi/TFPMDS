from app.models import Notification, Produce, PurchaseOrder
from helpers import account, auth
from test_produce import listing


def setup_order(client, db, quantity=100, key='order-demo-0001'):
    farmer = account(db); buyer = account(db, 'buyer')
    produce = client.post('/api/produce', headers=auth(farmer), json=listing()).json()
    body = {'items':[{'produce_id':produce['id'],'quantity_kg':quantity}], 'delivery_address':'Kariakoo, Dar es Salaam'}
    response = client.post('/api/orders', headers=auth(buyer) | {'Idempotency-Key':key}, json=body)
    assert response.status_code == 201, response.text
    return farmer, buyer, produce, response.json(), body


def test_order_reservation_acceptance_and_history(client, db):
    farmer,buyer,produce,order,body = setup_order(client,db)
    assert order['status'] == 'pending_farmer_approval' and order['total_tzs'] == 220000
    assert db.get(Produce, produce['id']).available_kg == 400
    duplicate = client.post('/api/orders', headers=auth(buyer) | {'Idempotency-Key':'order-demo-0001'}, json=body)
    assert duplicate.json()['id'] == order['id'] and db.query(PurchaseOrder).count() == 1
    assert db.get(Produce, produce['id']).available_kg == 400
    other = account(db)
    assert client.post(f'/api/orders/{order["id"]}/decision', headers=auth(other), json={'action':'accept'}).status_code == 403
    assert client.get(f'/api/orders/{order["id"]}', headers=auth(other)).status_code == 403
    assert client.post(f'/api/orders/{order["id"]}/decision', headers=auth(farmer), json={'action':'accept'}).json()['status'] == 'accepted'
    assert len(client.get('/api/orders', headers=auth(buyer)).json()) == 1
    assert db.query(Notification).filter_by(user_id=farmer.id,kind='order').count() == 2


def test_order_rejection_cancellation_and_validation(client, db):
    farmer,buyer,produce,order,body = setup_order(client,db)
    assert client.post(f'/api/orders/{order["id"]}/decision', headers=auth(farmer), json={'action':'reject'}).json()['status'] == 'rejected'
    assert db.get(Produce,produce['id']).available_kg == 500
    assert client.post(f'/api/orders/{order["id"]}/decision', headers=auth(farmer), json={'action':'reject'}).status_code == 409
    body['items'][0]['quantity_kg'] = 501
    assert client.post('/api/orders', headers=auth(buyer)|{'Idempotency-Key':'order-stock-fail'}, json=body).status_code == 409
    assert db.query(PurchaseOrder).count() == 1
    body['items'][0]['quantity_kg']=20
    new = client.post('/api/orders', headers=auth(buyer)|{'Idempotency-Key':'order-cancel-001'}, json=body).json()
    assert client.post(f'/api/orders/{new["id"]}/decision', headers=auth(buyer), json={'action':'cancel'}).status_code == 200
    assert db.get(Produce,produce['id']).available_kg == 500
    pending = account(db, 'buyer', 'pending')
    assert client.post('/api/orders', headers=auth(pending)|{'Idempotency-Key':'order-pending01'}, json=body).status_code == 403
    body['items'][0]['quantity_kg']=0
    assert client.post('/api/orders', headers=auth(buyer)|{'Idempotency-Key':'order-zero-0001'}, json=body).status_code == 422
