import pytest

from app.config import MOCK_CALLBACK_SECRET
from app.models import Payment, PaymentReceipt, Shipment
from helpers import account, auth
from test_orders import setup_order


def paid_order(client, db, provider='mpesa', outcome='successful'):
    farmer,buyer,produce,order,body = setup_order(client,db)
    assert client.post('/api/payments', headers=auth(buyer)|{'Idempotency-Key':'pay-before-approval'}, json={'order_id':order['id'],'provider':provider,'phone':buyer.phone}).status_code == 409
    client.post(f'/api/orders/{order["id"]}/decision', headers=auth(farmer), json={'action':'accept'})
    data={'order_id':order['id'],'provider':provider,'phone':buyer.phone}
    response=client.post('/api/payments', headers=auth(buyer)|{'Idempotency-Key':'payment-demo-0001'}, json=data)
    assert response.status_code == 201, response.text
    payment=response.json()
    result=client.post(f'/api/payments/{payment["id"]}/simulate',headers=auth(buyer),json={'outcome':outcome})
    assert result.status_code == 200, result.text
    return farmer,buyer,order,payment,data


@pytest.mark.parametrize('provider',['mpesa','airtel_money','tigo_pesa'])
def test_successful_payment_receipt_and_idempotency(client, db, provider):
    farmer,buyer,order,payment,data=paid_order(client,db,provider)
    assert db.query(PaymentReceipt).count() == 1 and db.query(Shipment).count() == 1
    duplicate=client.post('/api/payments',headers=auth(buyer)|{'Idempotency-Key':'payment-demo-0001'},json=data)
    assert duplicate.json()['id'] == payment['id'] and db.query(Payment).count() == 1
    body={'reference':payment['reference'],'outcome':'successful'}
    assert client.post('/api/payments/mock-callback',json=body).status_code == 401
    for _ in range(2):
        assert client.post('/api/payments/mock-callback',headers={'X-Mock-Secret':MOCK_CALLBACK_SECRET},json=body).status_code == 200
    assert db.query(PaymentReceipt).count() == 1 and db.query(Shipment).count() == 1
    receipt=client.get(f'/api/payments/{payment["id"]}/receipt',headers=auth(buyer)).json()
    assert receipt['amount_tzs'] == order['total_tzs'] and receipt['mode'].startswith('SIMULATION')
    assert client.get(f'/api/payments/{payment["id"]}',headers=auth(farmer)).json()['status'] == 'successful'
    assert len(client.get('/api/payments',headers=auth(buyer)).json()) == 1
    other=account(db,'buyer')
    assert client.get(f'/api/payments/{payment["id"]}/receipt',headers=auth(other)).status_code == 403
    assert client.post(f'/api/payments/{payment["id"]}/simulate',headers=auth(other),json={'outcome':'successful'}).status_code == 403
    assert client.post(f'/api/payments/{payment["id"]}/simulate',headers=auth(buyer),json={'outcome':'failed'}).status_code == 409


@pytest.mark.parametrize('outcome',['failed','cancelled'])
def test_payment_failure_cancellation_and_retry(client, db, outcome):
    farmer,buyer,order,payment,data=paid_order(client,db,outcome=outcome)
    assert db.query(Shipment).count() == 0 and db.query(PaymentReceipt).count() == 0
    assert client.get(f'/api/payments/{payment["id"]}/receipt',headers=auth(buyer)).status_code == 404
    retry=client.post('/api/payments',headers=auth(buyer)|{'Idempotency-Key':'payment-retry-0001'},json=data)
    assert retry.status_code == 201
    assert client.post(f'/api/payments/{retry.json()["id"]}/simulate',headers=auth(buyer),json={'outcome':'successful'}).status_code == 200
    assert db.query(Shipment).count() == 1
