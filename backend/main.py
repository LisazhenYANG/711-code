from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers.ai_compat import router as ai_compat_router
from backend.routers.api import router as api_router


def create_app() -> FastAPI:
    app = FastAPI(title="Manyou Backend", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)
    app.include_router(ai_compat_router)
    return app


app = create_app()
