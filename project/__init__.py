from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from project.celery_utils import create_celery
from project.users.views import users_router
from project.ws import broadcast, ws_router
from project.ws.views import register_socketio_app

ORIGINS = [
    'http://localhost',
    'http://localhost:8010',
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    await broadcast.connect()
    yield
    await broadcast.disconnect()


def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)

    app.celery_app = create_celery()

    app.include_router(users_router)
    app.include_router(ws_router)

    register_socketio_app(app)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=ORIGINS,
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )

    @app.get('/')
    async def root():
        return {'message': 'Hello World'}

    return app
