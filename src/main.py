# imports MUST be in this order to avoid circular dependencies
from contextlib import asynccontextmanager
from fastapi import FastAPI
from typing import Literal
from fastapi.middleware.cors import CORSMiddleware
from src.config import CONFIG
from src.db.base import SessionLocal
from src.db.seed import seed_defaults
from src.db.registry import registry
from src.cache import cache_manager
from src.scheduler import start_self_ping
from src.locations.router import router as locations_router
from src.events.router import router as events_router


def _register_caches() -> None:
    """
    Register all dimension caches with tuned sizes and TTLs.
    Called once at startup before any events are ingested.
    """
    cache_manager.register("ip_location",  max_size=2048, ttl_seconds=3600)
    cache_manager.register("dates",        max_size=512)
    cache_manager.register("device_types", max_size=256)
    cache_manager.register("pages",        max_size=1024)
    cache_manager.register("referrals",    max_size=512)
    cache_manager.register("visitors",     max_size=1024)

    print(
        f"\n=== Caches registered: {cache_manager.cache_names} ===\n"
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown lifecycle for the app.
    This is where we can do any necessary setup or teardown for the application, 
    such as connecting to the database, seeding default data, loading registries, etc.
    For more resources: https://fastapi.tiangolo.com/advanced/events/
    """
    # --- Startup ---
    from src.db import init_db
    init_db()  # create tables (imports Events model inside to avoid circular import)

    db = SessionLocal()
    try:
        seed_defaults(db)
        registry.load(db)
    finally:
        db.close()

    _register_caches()

    # Start the keep-alive self-ping scheduler
    ping_task = await start_self_ping()

    yield  # App runs here

    # --- Shutdown ---
    ping_task.cancel()
    cache_manager.clear_all()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CONFIG.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(events_router, prefix="/analytics")
app.include_router(locations_router, prefix="/analytics")


@app.get("/analytics",
         description="Welcome message for the Artfolio Analytics API",
         name="Root Endpoint"
         )
async def root():
    return {"message": "Welcome to Artfolio Analytics!"}


@app.get("/analytics/health",
         description="Check the health status of the application",
         name="Health Check"
         )
async def health_check() -> dict[Literal["status"], Literal["Healthy", "Unhealthy"]]:
    return {"status": "Healthy"}


@app.get("/analytics/cache/stats",
         description="View hit/miss/eviction stats for all dimension caches",
         name="Cache Stats",
         tags=["Diagnostics"]
         )
async def cache_stats() -> dict:
    return cache_manager.stats()
