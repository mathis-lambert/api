import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.databases import MongoDBConnector, QdrantConnector
from api.v1 import v1_router

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Code de démarrage
    app.mongodb_client = MongoDBConnector()
    app.qdrant_client = QdrantConnector()
    yield
    # Code d'arrêt
    app.mongodb_client.get_client().close()
    await app.qdrant_client.get_client().close()


app = FastAPI(
    title="Main API for Mathis LAMBERT",
    description="This is the main API for Mathis LAMBERT's projects.",
    version="0.1.0",
    openapi_url="/api/v1/openapi.json",  # Chemin personnalisé pour le fichier OpenAPI
    docs_url="/swagger",  # Chemin personnalisé pour la documentation Swagger UI
    redoc_url="/api-docs",  # Chemin personnalisé pour la documentation ReDoc
    lifespan=lifespan,
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Vérifiez si le mode maintenance est activé via une variable d'environnement
MAINTENANCE_MODE = os.getenv("MAINTENANCE_MODE", "false").lower() == "true"


@app.middleware("http")
async def check_maintenance(request, call_next):
    if MAINTENANCE_MODE:
        return JSONResponse(
            status_code=503, content={"detail": "Service en maintenance"}
        )
    response = await call_next(request)
    return response


# Inclure les routes pour chaque version
app.include_router(v1_router, prefix="/v1", tags=["v1"])


@app.get("/")
def read_root():
    return {
        "message": "Welcome to my FastAPI application! 🚀 You can check the redoc documentation at /api-docs and the "
        "swagger documentation at /swagger."
    }


# Gestion des erreurs
@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    return JSONResponse(status_code=500, content={"message": "Internal server error"})


@app.exception_handler(404)
async def not_found_exception_handler(request, exc):
    return JSONResponse(status_code=404, content={"message": "Not found"})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app", host="0.0.0.0", port=8000, reload=True, reload_dirs=["/src/api"]
    )
