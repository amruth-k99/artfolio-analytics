# Artfolio Analytics

![Python](https://img.shields.io/badge/Python-3.13+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white)
![Pydantic](https://img.shields.io/badge/Pydantic-V2-E92063?style=for-the-badge&logo=pydantic&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-003B57?style=for-the-badge&logo=postgresql&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

An open-source, self-hostable analytics backend for [Artfolio](https://www.artfolio.tech) — track page views, visitor trends, referral sources, device breakdowns, and geographic locations for any portfolio URL.

> **System Design Reference:** [Artfolio Analytics on Whimsical](https://whimsical.com/amruth26/artfolio-analytics-system-design-2eZGHwX3Ju32bhnfTZbXv7)

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [1. Clone & Install](#1-clone--install)
  - [2. Configure Environment Variables](#2-configure-environment-variables)
  - [3. Set Up the Database](#3-set-up-the-database)
  - [4. Run Database Migrations](#4-run-database-migrations)
  - [5. Start the Development Server](#5-start-the-development-server)
- [Using Your Own Database](#using-your-own-database)
  - [Option A — SQLite (local dev)](#option-a--sqlite-local-dev)
  - [Option B — PostgreSQL (recommended for production)](#option-b--postgresql-recommended-for-production)
- [Database Migrations (Alembic)](#database-migrations-alembic)
- [Running Tests](#running-tests)
- [Docker Deployment](#docker-deployment)
- [API Reference](#api-reference)
- [Environment Variable Reference](#environment-variable-reference)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

**Artfolio Analytics** is a lightweight, privacy-conscious analytics backend built with FastAPI. It uses a **star-schema** data model with a central `f_events` fact table linked to dimension tables for dates, devices, visitors, pages, referral sources, and locations. Dimension lookups are cached in-memory at startup for fast ingestion.

The platform is designed to be forked and self-hosted — just point it at your own database and you have a production-ready analytics API.

## Features

- **Event Ingestion** — Single and batch event ingestion endpoints with automatic dimension resolution
- **Star-Schema Data Model** — Fact table (`f_events`) with six dimension tables for flexible querying
- **IP-to-Location Resolution** — Automatically resolves visitor IP addresses to geographic locations (IP is not stored)
- **In-Memory Dimension Caching** — LRU caches with configurable sizes and TTLs for zero-latency dimension lookups
- **Dimension Registry** — Global singleton that caches all event type and referral IDs at startup
- **Database Seeding** — Idempotent seed function that creates default event types and referral sources on every startup
- **Keep-Alive Scheduler** — Self-ping background task to prevent free-tier hosting from sleeping
- **Alembic Migrations** — Version-controlled schema changes with autogenerate support
- **CORS Support** — Configurable allowed origins for frontend integration
- **Rate Limiting** — Built-in request throttling via SlowAPI
- **CI/CD** — GitHub Actions workflow for automated testing on push/PR

## Tech Stack

| Layer           | Technology                                          |
| --------------- | --------------------------------------------------- |
| **Framework**   | FastAPI 0.135 + Uvicorn                             |
| **ORM**         | SQLAlchemy 2.0 (mapped columns, DeclarativeBase)    |
| **Validation**  | Pydantic V2 + pydantic-settings                     |
| **Migrations**  | Alembic 1.18                                        |
| **Database**    | SQLite (dev) / PostgreSQL (prod via `psycopg2`)     |
| **HTTP Client** | HTTPX (async, for IP geolocation + self-ping)       |
| **Rate Limit**  | SlowAPI                                             |
| **Testing**     | Pytest + pytest-asyncio                             |
| **CI/CD**       | GitHub Actions                                      |
| **Container**   | Docker (Python 3.13-slim)                           |

## Project Structure

```
artfolio-analytics/
├── src/
│   ├── main.py              # FastAPI app, lifespan events, CORS, routers
│   ├── config.py             # Pydantic BaseSettings — loads .env / .env.prod
│   ├── scheduler.py          # Self-ping keep-alive for free-tier hosts
│   ├── auth/                 # Authentication decorators (extensible)
│   ├── cache/                # LRU cache manager with hit/miss/eviction stats
│   │   ├── lru.py
│   │   └── manager.py
│   ├── db/
│   │   ├── __init__.py       # init_db(), get_db() dependency
│   │   ├── base.py           # SQLAlchemy engine, SessionLocal, Base
│   │   ├── constants.py      # App-wide enum constants (event types, device types, etc.)
│   │   ├── registry.py       # DimensionRegistry singleton — cached lookups
│   │   ├── seed.py           # Idempotent DB seeding (event types, default referral)
│   │   └── migrations/       # Alembic migration scripts
│   │       ├── env.py
│   │       └── versions/
│   ├── dates/                # d_dates dimension
│   ├── devices/              # d_device_types dimension
│   ├── events/               # f_events fact table + ingestion logic
│   │   ├── model.py          # Events, EventTypes ORM models
│   │   ├── schema.py         # Pydantic schemas (ingestion payload, batch payload)
│   │   ├── service.py        # Ingestion pipeline (dimension upsert + fact insert)
│   │   └── router.py         # /v1/events endpoints
│   ├── locations/            # d_locations dimension + IP geolocation
│   ├── pages/                # d_pages dimension
│   ├── referrals/            # d_referral_sources dimension
│   └── visitors/             # d_visitors dimension
├── scripts/
│   ├── mock_events.json      # Sample event data for testing /v1/events/automate
│   └── mock_events.jsonc     # Annotated version with comments
├── tests/
│   ├── conftest.py           # Pytest fixtures (test DB session, FastAPI TestClient)
│   ├── test_api_endpoints.py
│   └── test_cache.py
├── sqlite/                   # Local SQLite database directory (gitignored)
├── .env                      # Development environment variables
├── .env.prod                 # Production environment variables (gitignored)
├── .github/workflows/test.yml
├── alembic.ini               # Alembic configuration
├── Dockerfile
├── pytest.ini
└── requirements.txt
```

---

## Getting Started

### Prerequisites

- **Python 3.13+**
- **pip** (or a virtual environment manager like `venv`)
- **PostgreSQL** _(only if deploying for production — SQLite works out of the box for local dev)_

### 1. Clone & Install

```bash
git clone https://github.com/amruth-k99/artfolio-analytics.git
cd artfolio-analytics

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # macOS/Linux
# .venv\Scripts\activate    # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy the example `.env` and update values for your setup:

```bash
cp .env .env.local   # optional — .env is already configured for local dev
```

Edit `.env` with your own values:

```env
DATABASE_URL=sqlite:///./sqlite/dev.db
SECRET_KEY=your-secret-key-here
DEBUG=True
DEPLOYMENT_EMAIL=you@example.com
SELF_BASE_URL=http://localhost:8000
```

> **Note:** The app reads `.env` when `DEBUG=True` and `.env.prod` when `DEBUG=False`. See [Environment Variable Reference](#environment-variable-reference) for details.

### 3. Set Up the Database

**For local development (SQLite):** No setup needed — the SQLite file is created automatically.

**For PostgreSQL:** Create a database and update `DATABASE_URL`:

```bash
# Create a PostgreSQL database
createdb artfolio_analytics

# Update .env
DATABASE_URL=postgresql://your_user:your_password@localhost:5432/artfolio_analytics
```

### 4. Run Database Migrations

Alembic manages the database schema. Run migrations to create all tables:

```bash
# Apply all migrations to bring the DB up to date
alembic upgrade head
```

If you're starting fresh on a new database and want to generate the initial migration from the current models:

```bash
# Auto-generate a new migration from model changes
alembic revision --autogenerate -m "initial_migration"

# Apply it
alembic upgrade head
```

> Tables are created via Alembic migrations, not `Base.metadata.create_all()`. Default dimension data (event types, referral sources) is seeded automatically on every server startup.

### 5. Start the Development Server

```bash
uvicorn src.main:app --reload
```

The API is now running at **http://localhost:8000**. Visit:

- **http://localhost:8000** — Welcome message
- **http://localhost:8000/docs** — Interactive Swagger UI
- **http://localhost:8000/redoc** — ReDoc API documentation
- **http://localhost:8000/health** — Health check endpoint

---

## Using Your Own Database

### Option A — SQLite (local dev)

SQLite is the default for development. No external service required.

```env
DATABASE_URL=sqlite:///./sqlite/dev.db
```

> **Limitation:** SQLite does not support `pool_size`/`max_overflow` arguments. The app handles this gracefully but for production workloads, use PostgreSQL.

### Option B — PostgreSQL (recommended for production)

1. **Provision a PostgreSQL database** — use any provider (Render, Supabase, Neon, Railway, AWS RDS, or self-hosted).

2. **Get your connection string** in this format:

   ```
   postgresql://<user>:<password>@<host>:<port>/<database_name>
   ```

3. **Update your `.env.prod`** (or `.env` for local Postgres dev):

   ```env
   DATABASE_URL=postgresql://admin:mypassword@localhost:5432/artfolio_analytics
   SECRET_KEY=a-strong-random-secret-key
   DEBUG=False
   DEPLOYMENT_EMAIL=you@example.com
   SELF_BASE_URL=https://your-production-url.com
   ```

4. **Run migrations:**

   ```bash
   # Make sure DEBUG=False is set so Alembic picks up the prod env
   export DEBUG=False
   alembic upgrade head
   ```

5. **Start the server:**

   ```bash
   export DEBUG=False
   uvicorn src.main:app --host 0.0.0.0 --port 8000
   ```

---

## Database Migrations (Alembic)

All schema changes are managed via Alembic. Migrations live in `src/db/migrations/versions/`.

| Command                                                  | Description                                  |
| -------------------------------------------------------- | -------------------------------------------- |
| `alembic upgrade head`                                   | Apply all pending migrations                 |
| `alembic downgrade -1`                                   | Rollback the last migration                  |
| `alembic revision --autogenerate -m "description"`       | Auto-generate a migration from model changes |
| `alembic history`                                        | Show migration history                       |
| `alembic current`                                        | Show the current migration revision          |

> Alembic reads the `DATABASE_URL` from your environment (via `src/config.py` → `CONFIG.database_url`), not from `alembic.ini`. The `sqlalchemy.url` in `alembic.ini` is overridden at runtime.

---

## Running Tests

Tests use an in-memory SQLite database configured in `tests/conftest.py`.

```bash
# Run the full test suite
PYTHONPATH=. pytest

# Run with verbose output
PYTHONPATH=. pytest -v

# Run a specific test file
PYTHONPATH=. pytest tests/test_cache.py
```

---

## Docker Deployment

Build and run the application using Docker:

```bash
# Build the image
docker build -t artfolio-analytics .

# Run with environment variables
docker run -d \
  -p 8000:8000 \
  -e DATABASE_URL="postgresql://user:pass@host:5432/dbname" \
  -e SECRET_KEY="your-secret-key" \
  -e DEBUG="False" \
  -e DEPLOYMENT_EMAIL="you@example.com" \
  -e SELF_BASE_URL="https://your-domain.com" \
  artfolio-analytics
```

The container exposes port **8000** and runs Uvicorn directly.

---

## API Reference

### Core Endpoints

| Method | Endpoint                       | Description                                     |
| ------ | ------------------------------ | ----------------------------------------------- |
| `GET`  | `/`                            | Welcome message                                 |
| `GET`  | `/health`                      | Health check — returns `{"status": "Healthy"}`   |
| `GET`  | `/cache/stats`                 | View hit/miss/eviction stats for all caches     |

### Events (`/v1/events`)

| Method | Endpoint               | Description                                                |
| ------ | ---------------------- | ---------------------------------------------------------- |
| `GET`  | `/v1/events/`          | List all events                                            |
| `POST` | `/v1/events/`          | Ingest a single event                                      |
| `POST` | `/v1/events/batch`     | Batch ingest events (frontend analytics pipeline)          |
| `POST` | `/v1/events/automate`  | Ingest mock events from `scripts/mock_events.json`         |

### Locations (`/v1/locations`)

| Method | Endpoint                         | Description                          |
| ------ | -------------------------------- | ------------------------------------ |
| `POST` | `/v1/locations/`                 | Create a new location record         |
| `POST` | `/v1/locations/search`           | Search/filter locations              |
| `GET`  | `/v1/locations/ip/{ip_address}`  | Resolve an IP address to a location  |

> Full interactive documentation is available at `/docs` (Swagger UI) or `/redoc` when the server is running.

---

## Environment Variable Reference

| Variable           | Required | Default                 | Description                                                                                          |
| ------------------ | -------- | ----------------------- | ---------------------------------------------------------------------------------------------------- |
| `DATABASE_URL`     | ✅        | —                       | SQLAlchemy connection string. Use `sqlite:///./sqlite/dev.db` for local dev or a PostgreSQL URI for prod. |
| `SECRET_KEY`       | ✅        | —                       | Secret key for signing/encryption. Use a strong random string in production.                          |
| `DEBUG`            | ❌        | `True`                  | `True` loads `.env`, `False` loads `.env.prod`. Controls environment file selection.                  |
| `DEPLOYMENT_EMAIL` | ✅        | —                       | Contact email used for deployment notifications.                                                     |
| `SELF_BASE_URL`    | ❌        | `http://localhost:8000` | The public URL of this service. Used by the keep-alive self-ping scheduler.                          |
| `CORS_ORIGINS`     | ❌        | `["*"]`                 | List of allowed CORS origins. Restrict in production.                                                |

---

## Contributing

Contributions are welcome! Please open issues or submit pull requests for improvements and bug fixes.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes (`git commit -am 'Add my feature'`)
4. Push to the branch (`git push origin feature/my-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the **MIT License**.

---

## Powered by Artfolio.tech

This is our first open-source project and we are open to collaborations. If you find any issues with the architecture or have suggestions, feel free to raise a PR or reach out:

- 📧 **amruth@artfolio.tech**
- 📧 **support@artfolio.tech**
