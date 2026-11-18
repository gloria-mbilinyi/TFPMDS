from helpers import account, auth
from test_produce import listing


def test_marketplace_search_filters(client, db):
    farmer = account(db)
    produce = client.post('/api/produce', headers=auth(farmer), json=listing()).json()
    assert len(client.get('/api/produce?q=kilombero&crop=Rice&region=Morogoro&min_price=2000&max_price=2300&min_quantity=400').json()) == 1
    for query in ['region=Mbeya','max_price=100','min_quantity=501','crop=Maize',f'farmer_id={farmer.id+1}']:
        assert client.get('/api/produce?'+query).json() == []
    detail = client.get(f'/api/produce/{produce["id"]}').json()
    assert detail['farmer_name'] == farmer.name and detail['available_kg'] == 500
    assert 'password_hash' not in str(detail) and 'email' not in detail
    assert len(client.get(f'/api/produce?farmer_id={farmer.id}').json()) == 1
    assert client.get('/api/produce?min_quantity=-1').status_code == 422
    farmer.status='pending'; db.commit()
    assert client.get('/api/produce').json() == []
    assert client.get(f'/api/produce/{produce["id"]}').status_code == 404
