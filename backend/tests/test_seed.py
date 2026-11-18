from app.models import Produce, PurchaseOrder, User
from app.seed import seed, seed_transactions


def test_seed_is_idempotent(client, db):
    seed(db); seed_transactions(db)
    assert db.query(User).count()==11 and db.query(Produce).count()==8 and db.query(PurchaseOrder).count()==3
    seed(db); seed_transactions(db)
    assert db.query(User).count()==11 and db.query(Produce).count()==8 and db.query(PurchaseOrder).count()==3
    login=client.post('/api/auth/login',json={'email':'farmer@tfpmds.demo','password':'DemoPass123!'})
    assert login.status_code==200, login.text
