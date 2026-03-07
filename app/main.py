"""
Digital Farming Management (DFM) — FastAPI Backend
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine
from app.models import *  # noqa: F401, F403  — registers all ORM models with Base
from app.database import Base

from app.routers import (
    auth,
    customers,
    drivers,
    equipment,
    market,
    notifications,
    orders,
    users,
    vehicles,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables on startup if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="Digital Farming Management API",
    description=(
        "REST API for the DFM platform — equipment rental, orders, "
        "market values, fleet management, and push notifications."
    ),
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(equipment.router)
app.include_router(orders.router)
app.include_router(vehicles.router)
app.include_router(customers.router)
app.include_router(drivers.router)
app.include_router(market.router)
app.include_router(notifications.router)


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "service": "DFM API", "version": "2.0.0"}


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy"}
