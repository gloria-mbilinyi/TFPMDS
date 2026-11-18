from concurrent.futures import ThreadPoolExecutor

import jwt
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.config import JWT_SECRET, MOCK_CALLBACK_SECRET
from app.db import get_db
from app.main import app
from app.models import PaymentReceipt, Produce, PurchaseOrder, Shipment
from helpers import account, auth
from test_produce import listing
from test_orders import setup_order


def separate_request_sessions(db):
    factory=sessionmaker(bind=db.get_bind(),expire_on_commit=False)
    def dependency():
        with factory() as session:
            try:
                yield session
                session.commit()
            except Exception:
                session.rollback()
                raise
    app.dependency_overrides[get_db]=dependency


def test_competing_buyers_cannot_oversell(client,db):
    farmer=account(db); buyers=[account(db,'buyer'),account(db,'buyer')]
    produce=client.post('/api/produce',headers=auth(farmer),json=listing()).json()
    body={'items':[{'produce_id':produce['id'],'quantity_kg':400}], 'delivery_address':'Dar es Salaam warehouse'}
    separate_request_sessions(db)
    def submit(index):
        with TestClient(app) as isolated:
            return isolated.post('/api/orders',headers=auth(buyers[index])|{'Idempotency-Key':f'concurrent-order-{index}'},json=body).status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes=list(pool.map(submit,[0,1]))
    assert sorted(outcomes)==[201,409]
    db.expire_all()
    assert db.get(Produce,produce['id']).available_kg==100
    assert db.query(PurchaseOrder).count()==1


def test_competing_callbacks_are_idempotent(client,db):
    farmer,buyer,produce,order,body=setup_order(client,db)
    client.post(f'/api/orders/{order["id"]}/decision',headers=auth(farmer),json={'action':'accept'})
    payment=client.post('/api/payments',headers=auth(buyer)|{'Idempotency-Key':'racing-payment-01'},json={'order_id':order['id'],'provider':'mpesa','phone':buyer.phone}).json()
    separate_request_sessions(db)
    def callback(_):
        with TestClient(app) as isolated:
            return isolated.post('/api/payments/mock-callback',headers={'X-Mock-Secret':MOCK_CALLBACK_SECRET},json={'reference':payment['reference'],'outcome':'successful'}).status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert list(pool.map(callback,[0,1]))==[200,200]
    db.expire_all()
    assert db.query(PaymentReceipt).count()==1 and db.query(Shipment).count()==1


def test_multi_item_rollback_and_changed_idempotency(client,db):
    farmer,buyer,produce,order,body=setup_order(client,db)
    second=client.post('/api/produce',headers=auth(farmer),json=listing(name='Second rice',available_kg=5)).json()
    body['items']=[{'produce_id':produce['id'],'quantity_kg':10},{'produce_id':second['id'],'quantity_kg':6}]
    assert client.post('/api/orders',headers=auth(buyer)|{'Idempotency-Key':'rollback-order-01'},json=body).status_code==409
    assert db.get(Produce,produce['id']).available_kg==400
    assert db.get(Produce,second['id']).available_kg==5
    assert db.query(PurchaseOrder).count()==1
    body['items']=[{'produce_id':produce['id'],'quantity_kg':1}]
    assert client.post('/api/orders',headers=auth(buyer)|{'Idempotency-Key':'order-demo-0001'},json=body).status_code==409
    body['items']=[{'produce_id':produce['id'],'quantity_kg':1}]*2
    assert client.post('/api/orders',headers=auth(buyer)|{'Idempotency-Key':'duplicate-line01'},json=body).status_code==422


def test_expired_tokens_and_mass_assignment(client,db):
    farmer=account(db)
    expired=jwt.encode({'sub':str(farmer.id),'jti':'expired','iat':1,'exp':2,'iss':'tfpmds','aud':'tfpmds-ui'},JWT_SECRET,algorithm='HS256')
    assert client.get('/api/auth/me',headers={'Authorization':'Bearer '+expired}).status_code==401
    body={'name':farmer.name,'phone':farmer.phone,'region':farmer.region,'role':'administrator'}
    assert client.patch('/api/users/me',headers=auth(farmer),json=body).status_code==422
