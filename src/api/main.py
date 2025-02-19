from api.v1 import v1_router

from fastapi import FastAPI

app = FastAPI(
    title="Main API for Mathis LAMBERT",
    description="This is the main API for Mathis LAMBERT's projects.",
    version="0.1.0",
    openapi_url="/api/v1/openapi.json",  # Chemin personnalisé pour le fichier OpenAPI
    docs_url="/docs",  # Chemin personnalisé pour la documentation Swagger UI
    redoc_url="/redoc"  # Chemin personnalisé pour la documentation ReDoc
)

# Inclure les routes pour chaque version
app.include_router(v1_router, prefix="/v1", tags=["v1"])


@app.get("/")
def read_root():
    return {"message": "Welcome to my FastAPI application! 🚀 You can check the documentation at /docs."}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, reload_dirs=["/src/api"])
