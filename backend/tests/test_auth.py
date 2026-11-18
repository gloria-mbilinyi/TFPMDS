from app.models import User
from app.security import passwords
from helpers import account, auth, registration


def test_registration_login_logout(client, db):
    response = client.post('/api/auth/register', json=registration())
    assert response.status_code == 201
    assert response.json()['status'] == 'pending'
    assert 'password_hash' not in response.json()
    user = db.get(User, response.json()['id'])
    assert user.password_hash.startswith('$argon2') and passwords.verify('DemoPass123!', user.password_hash)
    response = client.post('/api/auth/login', json={'email': 'farmer@example.com', 'password': 'DemoPass123!'})
    headers = {'Authorization': 'Bearer ' + response.json()['access_token']}
    assert client.get('/api/auth/me', headers=headers).status_code == 200
    assert client.post('/api/auth/logout', headers=headers).status_code == 200
    assert client.get('/api/auth/me', headers=headers).status_code == 401


def test_registration_validation(client):
    assert client.post('/api/auth/register', json=registration()).status_code == 201
    assert client.post('/api/auth/register', json=registration()).status_code == 409
    body = registration(); body['role'] = 'administrator'
    assert client.post('/api/auth/register', json=body).status_code == 422
    body['role'] = 'buyer'; body['phone'] = '123'
    assert client.post('/api/auth/register', json=body).status_code == 422
    assert client.post('/api/auth/login', json={'email':'nobody@example.com','password':'wrong'}).status_code == 401
    assert client.get('/api/auth/me', headers={'Authorization':'Bearer fake'}).status_code == 401
    assert client.get('/api/auth/me').status_code == 401


def test_inactive_user_is_blocked(client, db):
    user = account(db); headers = auth(user)
    user.active = False; db.commit()
    assert client.get('/api/auth/me', headers=headers).status_code == 401
