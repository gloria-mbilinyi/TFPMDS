import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app import models
from app.db import Base


def test_health(client):
    assert client.get('/api/health').json()['status'] == 'ok'
    assert len(Base.metadata.tables) == 11


def test_database_constraints(db):
    assert db.scalar(text('PRAGMA foreign_keys')) == 1
    with pytest.raises(IntegrityError):
        db.add(models.Produce(farmer_id=999, name='Rice', crop='Rice', available_kg=-1,
                              price_tzs=0, harvest_date=__import__('datetime').date.today()))
        db.flush()
    db.rollback()
