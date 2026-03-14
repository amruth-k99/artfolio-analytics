# imports MUST be in this order to avoid circular dependencies
from contextlib import asynccontextmanager
from fastapi import FastAPI
from typing import Literal
from src.db.base import SessionLocal
from src.db.seed import seed_defaults
from src.db.registry import registry
from src.locations.router import router as locations_router
from src.events.router import router as events_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle for the app."""
    # --- Startup ---
    db = SessionLocal()
    try:
        seed_defaults(db)
        registry.load(db)
    finally:
        db.close()

    yield  # App runs here

    # --- Shutdown ---
    # cleanup if needed in the future


app = FastAPI(lifespan=lifespan)

app.include_router(events_router)
app.include_router(locations_router)


@app.get("/",
         description="Welcome message for the Artfolio Analytics API",
         name="Root Endpoint"
         )
async def root():
    return {"message": "Welcome to Artfolio Analytics!"}


@app.get("/health",
         description="Check the health status of the application",
         name="Health Check"
         )
async def health_check() -> dict[Literal["status"], Literal["Healthy", "Unhealthy"]]:
    return {"status": "Healthy"}
