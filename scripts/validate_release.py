"""Read-only API verification of the portable synthetic database and final assets."""
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker
from app.db import get_db, make_engine
from app.main import app

snapshot=ROOT/'demo/tfpmds-demo.sqlite'
before=hashlib.sha256(snapshot.read_bytes()).hexdigest()
with sqlite3.connect(f'file:{snapshot.as_posix()}?mode=ro',uri=True) as connection:
    assert connection.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    assert connection.execute('PRAGMA foreign_key_check').fetchall()==[]
    assert connection.execute('SELECT COUNT(*) FROM revoked_tokens').fetchone()[0]==0
    assert connection.execute("SELECT status FROM purchase_orders WHERE id=4").fetchone()[0]=='completed'
factory=sessionmaker(bind=make_engine('sqlite:///'+snapshot.as_posix()),expire_on_commit=False)
def database():
    with factory() as session:yield session
app.dependency_overrides[get_db]=database
try:
    with TestClient(app) as client:
        login=client.post('/api/auth/login',json={'email':'admin@tfpmds.demo','password':'DemoPass123!'})
        assert login.status_code==200
        headers={'Authorization':'Bearer '+login.json()['access_token']}
        report=client.get('/api/reports/summary',headers=headers).json()
        assert report['users']==13 and report['orders']==4 and report['gross_sales_tzs']==380000
        assert report['completed_orders']==1 and report['successful_payments']==2
        receipt=client.get('/api/payments/2/receipt',headers=headers).json()
        assert receipt['order_id']==4 and receipt['amount_tzs']==105000
        assert receipt['number']=='TFP-6150D9B221C74F79'
        assert len(client.get('/api/admin/sms-log',headers=headers).json())==44
        tracking=client.get('/api/shipments/2',headers=headers).json()
        assert tracking['status']=='delivered' and len(tracking['history'])==6
finally:
    app.dependency_overrides.clear();factory.kw['bind'].dispose()
assert hashlib.sha256(snapshot.read_bytes()).hexdigest()==before,'Read-only verification changed the snapshot.'
for path in ['frontend/dist/index.html','docs/TFPMDS_Technical_Proposal.pdf','docs/TECHNICAL_PROPOSAL.md','docs/REQUIREMENTS_TRACEABILITY.md','docs/openapi.json']:
    assert (ROOT/path).is_file(),path
def git(*parts):return subprocess.check_output(['git','-C',str(ROOT),*parts],text=True).strip()
assert git('remote','get-url','origin')=='https://github.com/gloria-mbilinyi/TFPMDS.git'
assert git('config','--local','--get','user.name') in {'prettyglory','gloria-mbilinyi'}
assert git('config','--local','--get','user.email')=='gloriambilinyi5@gmail.com'
assert set(git('log','--format=%an <%ae>').splitlines()) <= {'prettyglory <gloriambilinyi5@gmail.com>','gloria-mbilinyi <gloriambilinyi5@gmail.com>'}
result={'result':'passed','snapshot_sha256':before,'snapshot_api_checks':['admin login','13 users','4 orders','380000 simulated gross TZS','completed order','receipt','44 SMS records','6 tracking events'],
        'official_remote_preserved':True,'repository_local_author_confirmed':True,'pushes_by_agent':0}
(ROOT/'docs/evidence/release-verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result))
