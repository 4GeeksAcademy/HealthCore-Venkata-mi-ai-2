"""HealthCore API — Incident Analyzer + Supplier Directory + Inventory."""

from __future__ import annotations

import logging
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.errors import StorageError
from app.database import init_dual_stores
from app.models.health import HealthResponse
from app.routers.auth import router as auth_router
from app.routers.incidents import router as incidents_router
from app.routers.inventory import router as inventory_router
from app.routers.profiles import router as profiles_router
from app.routers.suppliers import router as suppliers_router
from app.routers.telemetry import router as telemetry_router
from app.routers.users import router as users_router
from app.telemetry.store import init_telemetry_schema

_services_dir = Path(__file__).resolve().parents[2]
if str(_services_dir) not in sys.path:
    sys.path.insert(0, str(_services_dir))
from reporting.router import router as reporting_router  # noqa: E402

logger = logging.getLogger(__name__)
timing_logger = logging.getLogger("api.timing")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_dual_stores()
    init_telemetry_schema()
    try:
        pipelines = Path(__file__).resolve().parents[3] / "data" / "pipelines"
        if str(pipelines) not in sys.path:
            sys.path.insert(0, str(pipelines))
        from monthly_clinic_supply.db import init_reporting_schema

        init_reporting_schema()
    except Exception:
        logging.getLogger(__name__).warning(
            "reporting schema init skipped",
            exc_info=True,
        )
    yield


app = FastAPI(
    title="HealthCore Digital API",
    version="1.1.0",
    lifespan=lifespan,
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
app.include_router(inventory_router)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(profiles_router)
app.include_router(telemetry_router)
app.include_router(reporting_router)


@app.middleware("http")
async def timing_middleware(request: Request, call_next):
    """Log method, path, status, and duration. Path only — no query or auth headers."""
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    timing_logger.info(
        "%s %s → %s | %.1fms",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


@app.exception_handler(StorageError)
async def storage_error_handler(_request: Request, exc: StorageError) -> JSONResponse:
    logger.error("Data store failure (%s)", type(exc).__name__)
    return JSONResponse(
        status_code=503,
        content={"detail": "Service temporarily unavailable. Please try again."},
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    _request: Request, _exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"detail": "Invalid request. Please check the submitted data."},
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=getattr(exc, "headers", None),
        )
    logger.error("Unhandled server error (%s)", type(exc).__name__)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    from app.core.config import get_settings

    return HealthResponse(
        status="ok",
        inventory_backend=get_settings().inventory_backend,
    )
