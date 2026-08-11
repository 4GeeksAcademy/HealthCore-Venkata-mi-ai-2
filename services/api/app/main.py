"""HealthCore API — Incident Analyzer + Supplier Directory."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.incidents import router as incidents_router
from app.routers.suppliers import router as suppliers_router

app = FastAPI(
    title="HealthCore Digital API",
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(incidents_router)
app.include_router(suppliers_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
