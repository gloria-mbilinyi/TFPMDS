from helpers import account, auth


def listing(**overrides):
    body = dict(name='Kilombero rice', crop='Rice', description='Freshly harvested', available_kg=500,
                price_tzs=2200, harvest_date='2026-11-10')
    return body | overrides


def test_produce_management(client, db):
    farmer = account(db); other = account(db); pending = account(db, status='pending')
    assert client.post('/api/produce', headers=auth(pending), json=listing()).status_code == 403
    result = client.post('/api/produce', headers=auth(farmer), json=listing())
    assert result.status_code == 201
    product = result.json(); assert product['harvest_date'] == '2026-11-10'
    assert client.patch(f'/api/produce/{product["id"]}', headers=auth(other), json=listing()).status_code == 403
    edited = client.patch(f'/api/produce/{product["id"]}', headers=auth(farmer), json=listing(available_kg=300, price_tzs=2100)).json()
    assert edited['available_kg'] == 300 and edited['price_tzs'] == 2100
    assert len(client.get('/api/produce/mine', headers=auth(farmer)).json()) == 1
    assert client.delete(f'/api/produce/{product["id"]}', headers=auth(other)).status_code == 403
    assert client.delete(f'/api/produce/{product["id"]}', headers=auth(farmer)).status_code == 200
    assert client.get('/api/produce/mine', headers=auth(farmer)).json()[0]['active'] is False


def test_produce_invalid_values(client, db):
    farmer = account(db)
    for change in [{'available_kg':-1},{'price_tzs':0},{'price_tzs':-5},{'available_kg':2.5},{'harvest_date':'bad'}]:
        assert client.post('/api/produce', headers=auth(farmer), json=listing(**change)).status_code == 422
