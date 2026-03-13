from fastapi import FastAPI
from typing import Literal
from .db import get_db

app = FastAPI()

# app.include_router(
#     prefix="/api/v1",
#     router=None,  # Placeholder for actual router
#     tags=["API v1"]
# )


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
