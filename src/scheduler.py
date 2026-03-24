"""
Self-ping scheduler to prevent free-tier hosting (e.g. Render) from
putting the service to sleep due to inactivity.

The scheduler fires an HTTP GET to the server's own /health endpoint
every SELF_PING_INTERVAL_SECONDS (default 240 s = 4 min).
"""

import asyncio
import httpx
from src.config import CONFIG

SELF_PING_INTERVAL_SECONDS = 4 * 60  # 4 minutes


async def _ping_self() -> None:
    """Send a single GET to /health and log the result."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{CONFIG.self_base_url}/health")
            print(f"[self-ping] GET /health -> {resp.status_code}")
    except Exception as exc:
        print(f"[self-ping] failed: {exc}")


async def start_self_ping() -> asyncio.Task:
    """
    Launch a background task that pings /health every 4 minutes.
    Returns the asyncio.Task so it can be cancelled on shutdown.
    """

    async def _loop() -> None:
        while True:
            await asyncio.sleep(SELF_PING_INTERVAL_SECONDS)
            await _ping_self()

    task = asyncio.create_task(_loop())
    print(
        f"[self-ping] scheduler started – pinging {CONFIG.self_base_url}/health "
        f"every {SELF_PING_INTERVAL_SECONDS}s"
    )
    return task
