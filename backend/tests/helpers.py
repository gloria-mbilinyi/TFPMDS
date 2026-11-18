from app.models import User
from app.security import issue_token, passwords


def account(db, role='farmer', status='approved', name=None):
    count = db.query(User).count() + 1
    user = User(name=name or f'Demo {role} {count}', email=f'{role}{count}@example.com',
                password_hash=passwords.hash('DemoPass123!'), role=role, status=status,
                phone='+255712345678', region='Morogoro')
    db.add(user)
    db.commit()
    return user


def auth(user):
    return {'Authorization': 'Bearer ' + issue_token(user)}


def registration(role='farmer', **overrides):
    return dict(name='Asha Mbilinyi', email=f'{role}@example.com', password='DemoPass123!',
                role=role, phone='+255712345678', region='Morogoro', **overrides)
