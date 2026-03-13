from fastapi import FastAPI
from typing import Literal
from src.events.router import router as events_router

app = FastAPI()

app.include_router(events_router)


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
