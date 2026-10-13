from fastapi import FastAPI

from apps.api.src.routes.recommendations import router
from apps.api.src.routes.conversation import router as conversation_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Ruta EAN — Cerebro Académico",
        description=(
            "API para consultar Educación Continuada, "
            "Programas Oficiales y Unidades de Estudio."
        ),
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.include_router(router)
    app.include_router(conversation_router)

    return app


app = create_app()
