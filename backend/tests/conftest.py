import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.db import Base, get_db, make_engine
from app.main import app


@pytest.fixture
def db(tmp_path):
    engine = make_engine(f'sqlite:///{(tmp_path / "test.db").as_posix()}')
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine, expire_on_commit=False)() as session:
        yield session
    engine.dispose()


@pytest.fixture
def client(db):
    def override_db():
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
