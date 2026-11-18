"""Environment configuration. Development secrets persist locally, never in Git."""
import os
import secrets
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / '.env')
DATABASE_URL = os.getenv('DATABASE_URL', f'sqlite:///{(ROOT / "tfpmds.db").as_posix()}')
secret_file = ROOT / '.development-secrets'
if not os.getenv('JWT_SECRET'):
    if not secret_file.exists():
        secret_file.write_text(secrets.token_urlsafe(48), encoding='ascii')
    JWT_SECRET = secret_file.read_text(encoding='ascii').strip()
else:
    JWT_SECRET = os.environ['JWT_SECRET']
if len(JWT_SECRET) < 32:
    raise RuntimeError('JWT_SECRET must have at least 32 characters.')
MOCK_CALLBACK_SECRET = os.getenv('MOCK_CALLBACK_SECRET', JWT_SECRET + '-mock-only')
CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173').split(',')
