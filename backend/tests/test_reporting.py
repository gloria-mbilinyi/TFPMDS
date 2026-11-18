from helpers import account, auth
from test_logistics import paid_order


def test_reports_and_market_prices(client, db):
    farmer,buyer,order,shipment=paid_order(client,db)
    admin=account(db,'administrator')
    report=client.get('/api/reports/summary',headers=auth(admin)).json()
    assert report['gross_sales_tzs'] == 220000 and report['successful_payments'] == 1
    assert report['orders'] == 1 and report['sales_by_produce'][0]['quantity_kg'] == 100
    assert report['sales_by_region'] == [{'region':'Morogoro','sales_tzs':220000}]
    assert client.get('/api/reports/summary',headers=auth(buyer)).status_code == 403
    data={'crop':'Rice','region':'Morogoro','price_tzs':2000,'observed_on':'2026-11-18'}
    assert client.post('/api/admin/market-prices',headers=auth(buyer),json=data).status_code == 403
    price=client.post('/api/admin/market-prices',headers=auth(admin),json=data).json()
    data['price_tzs']=2300
    assert client.post('/api/admin/market-prices',headers=auth(admin),json=data).json()['id'] == price['id']
    assert client.get('/api/market-prices').json()[0]['price_tzs'] == 2300
    data['price_tzs']=0
    assert client.post('/api/admin/market-prices',headers=auth(admin),json=data).status_code == 422
    assert client.delete(f'/api/admin/market-prices/{price["id"]}',headers=auth(admin)).status_code == 200
