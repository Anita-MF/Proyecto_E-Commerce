from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from backend.app.core.config import settings
from backend.app.routers import inventario

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description=settings.description,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(inventario.router)

FRONTEND_PATH = Path(__file__).parent.parent.parent / "frontend"

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def dashboard():
    try:
        ruta = Path("frontend/index.html")
        html = ruta.read_text(encoding="utf-8")
        return HTMLResponse(content=html)
    except Exception as e:
        return HTMLResponse(content=f"<h1>Error: {e}</h1>")

@app.get("/health", summary="Health check")
def health():
    return {"status": "ok", "version": settings.version}