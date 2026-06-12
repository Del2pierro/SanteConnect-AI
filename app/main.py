"""
Point d'entrée principal de l'application FastAPI
"""

from contextlib import asynccontextmanager
import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.database import init_db
from app.config import settings
from app.routes import chat
from app.services.llm_service import llm_service

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Cycle de vie de l'application."""
    init_db()
    llm_service.initialize()
    logger.info(f"Démarrage de {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Mode debug: {settings.DEBUG}")
    yield
    logger.info(f"Arrêt de {settings.APP_NAME}")


# Création de l'application FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Assistant médical alimenté par l'IA pour fournir des conseils de santé",
    lifespan=lifespan,
)

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusion des routes
app.include_router(chat.router)

# Serveur statique pour le frontend
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_path):
    index_path = os.path.join(frontend_path, "index.html")

    @app.get("/")
    async def serve_frontend_index():
        """Sert l'interface depuis la racine."""
        return FileResponse(index_path)

    app.mount(
        "/static",
        StaticFiles(directory=frontend_path, html=True),
        name="static",
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
