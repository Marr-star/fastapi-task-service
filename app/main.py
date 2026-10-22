"""Application factory: isolated configuration, engine and lifespan."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import Settings
from .database import build_engine
from .models import Base
from .routes import router


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    engine = build_engine(settings.database_url)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        try:
            Base.metadata.create_all(engine)
            yield
        finally:
            engine.dispose()

    app = FastAPI(
        title='Task Service', version='1.0.0', lifespan=lifespan,
        description='A small task management API with SQLite persistence. '
                    'Use **Authorize** to provide the shared team API key. '
                    'Filter tasks by status, priority or owner and paginate with limit/offset. '
                    'Owner is a display label, not an authorization boundary.',
        docs_url='/docs' if settings.docs_enabled else None,
        redoc_url='/redoc' if settings.docs_enabled else None,
        openapi_url='/openapi.json' if settings.docs_enabled else None,
        openapi_tags=[{'name': 'Tasks', 'description': 'Authenticated task operations'},
                      {'name': 'Health', 'description': 'Public liveness endpoint'}],
    )
    app.state.settings = settings
    app.state.engine = engine
    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins,
                       allow_credentials=False, allow_methods=['GET', 'POST', 'PATCH', 'DELETE'],
                       allow_headers=['Authorization', 'Content-Type'])
    app.include_router(router)

    @app.get('/health', tags=['Health'], summary='Check service liveness')
    def health():
        return {'status': 'ok'}

    return app
