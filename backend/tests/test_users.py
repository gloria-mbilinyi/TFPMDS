from app.models import Notification
from helpers import account, auth, registration


def test_approvals_and_profiles(client, db):
    admin = account(db, 'administrator')
    farmer_data = registration(); farmer_data.update(location='Kilosa', farm_size_acres=5, crop_categories='Rice, Maize')
    farmer = client.post('/api/auth/register', json=farmer_data).json()
    login = client.post('/api/auth/login', json={'email':farmer_data['email'],'password':farmer_data['password']}).json()
    headers = {'Authorization':'Bearer '+login['access_token']}
    assert client.get('/api/admin/users', headers=headers).status_code == 403
    for status in ['approved','rejected','approved']:
        result = client.post(f'/api/admin/users/{farmer["id"]}/approval', headers=auth(admin), json={'status':status,'note':'Farm details reviewed.'})
        assert result.json()['status'] == status
    profile = {key:farmer_data[key] for key in ['name','phone','region','location','farm_size_acres','crop_categories']}
    profile['farm_size_acres'] = 7
    result = client.patch('/api/users/me', headers=headers, json=profile)
    assert result.json()['farm_size_acres'] == 7 and result.json()['status'] == 'pending'
    assert db.query(Notification).filter_by(user_id=farmer['id']).count() == 5
    buyer = client.post('/api/auth/register', json=registration('buyer')).json()
    assert client.post(f'/api/admin/users/{buyer["id"]}/approval', headers=auth(admin), json={'status':'approved','note':'Business reviewed.'}).status_code == 200
    assert client.get('/api/admin/users', headers=auth(admin)).status_code == 200


def test_admin_user_management(client, db):
    admin = account(db, 'administrator'); target = account(db, 'buyer')
    assert client.patch(f'/api/admin/users/{admin.id}/active', headers=auth(admin), json={'active':False}).status_code == 409
    assert client.patch(f'/api/admin/users/{target.id}/active', headers=auth(admin), json={'active':False}).json()['active'] is False
    assert client.get('/api/auth/me', headers=auth(target)).status_code == 401
    staff = registration(); staff.pop('role'); staff['email']='driver@example.com'; staff['role']='transporter'
    assert client.post('/api/admin/staff', headers=auth(admin), json=staff).status_code == 201
    assert len(client.get('/api/users/transporters', headers=auth(admin)).json()) == 1
