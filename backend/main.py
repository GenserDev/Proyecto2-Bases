from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from routers import (
    clientes, cuentas, tarjetas, transacciones,
    comercios, dispositivos, ubicaciones, relaciones,
    consultas, carga_csv, deteccion, grafo, dashboard,
)
from database import close_driver

app = FastAPI(
    title="Sistema de Detección de Fraude Bancario",
    description="API para gestionar un grafo de fraude bancario en Neo4j — CC3089 Base de Datos 2",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(clientes.router)
app.include_router(cuentas.router)
app.include_router(tarjetas.router)
app.include_router(transacciones.router)
app.include_router(comercios.router)
app.include_router(dispositivos.router)
app.include_router(ubicaciones.router)
app.include_router(relaciones.router)
app.include_router(consultas.router)
app.include_router(carga_csv.router)
app.include_router(deteccion.router)
app.include_router(grafo.router)
app.include_router(dashboard.router)

frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_path):
    # Montar subdirectorios del frontend directamente en la raíz
    for subdir in ("css", "js", "partials"):
        subpath = os.path.join(frontend_path, subdir)
        if os.path.exists(subpath):
            app.mount(f"/{subdir}", StaticFiles(directory=subpath), name=subdir)

    @app.get("/", include_in_schema=False)
    def serve_frontend():
        return FileResponse(os.path.join(frontend_path, "index.html"))


@app.on_event("shutdown")
def shutdown():
    close_driver()


@app.get("/health", tags=["Sistema"])
def health():
    return {"status": "ok", "mensaje": "Sistema de Detección de Fraude activo"}
