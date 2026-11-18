"""Export only a synthetic demonstration database, using the current schema."""
import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from sqlalchemy import select, text
from app.db import Base, engine, make_engine
from app.models import User


def export():
    target=(ROOT/'demo/tfpmds-demo.sqlite').resolve()
    assert target.parent==ROOT/'demo'
    target.parent.mkdir(exist_ok=True)
    with engine.connect() as source:
        emails=source.scalars(select(User.email)).all()
        if not emails or not all(email.endswith(('@tfpmds.demo','@example.com')) for email in emails):
            raise RuntimeError('Refusing export: this database contains non-demonstration accounts or is empty.')
        if target.exists():
            raise RuntimeError('A snapshot already exists; preserve it or choose a new release destination explicitly.')
        snapshot=make_engine('sqlite:///'+target.as_posix())
        Base.metadata.create_all(snapshot)
        counts={}
        with snapshot.begin() as destination:
            for table in Base.metadata.sorted_tables:
                # Session revocations are ephemeral and not needed in a portable demonstration.
                if table.name=='revoked_tokens':continue
                rows=[dict(row) for row in source.execute(select(table)).mappings()]
                if rows:destination.execute(table.insert(),rows)
                counts[table.name]=len(rows)
        with snapshot.connect() as connection:
            assert connection.scalar(text('PRAGMA integrity_check'))=='ok'
            assert connection.execute(text('PRAGMA foreign_key_check')).all()==[]
        snapshot.dispose()
    metadata={'purpose':'Optional synthetic local demo snapshot, including the observed browser journey.',
              'source':'Working local academic demo; passwords are hashes of the documented public demo password.',
              'contains_real_money_or_sms':False,'contains_jwt_secret':False,'counts':counts}
    (target.parent/'snapshot-info.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(counts))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--demo',action='store_true');args=parser.parse_args()
    if not args.demo:parser.error('Pass --demo to explicitly export public demonstration records.')
    export()
