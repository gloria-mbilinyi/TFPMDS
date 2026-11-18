from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from .config import CORS_ORIGINS
from .db import initialize


@asynccontextmanager
async def lifespan(_):
    initialize()
    yield


app = FastAPI(title='TFPMDS API', version='1.0.0', lifespan=lifespan,
              description='Academic local demo. All mobile-money and SMS providers are simulated.')
app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS, allow_credentials=False,
                   allow_methods=['GET', 'POST', 'PATCH', 'DELETE'], allow_headers=['Authorization', 'Content-Type', 'Idempotency-Key'])


@app.exception_handler(IntegrityError)
async def integrity_error(_: Request, exc: IntegrityError):
    return JSONResponse(status_code=409, content={'detail': {'code': 'conflict', 'message': 'A conflicting or invalid record already exists. Refresh and retry.'}})


@app.get('/api/health', tags=['system'])
def health():
    return {'status': 'ok', 'system': 'TFPMDS', 'payment_mode': 'simulation'}


from .auth import router as auth_router
app.include_router(auth_router)


