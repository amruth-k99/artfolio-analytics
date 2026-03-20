FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies including newly added ones
RUN pip install --no-cache-dir -r requirements.txt httpx alembic

# Copy application source code
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY alembic.ini .

# Create directory for SQLite DB if used locally
RUN mkdir -p /app/src/db

# Expose the application port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the FastAPI server via uvicorn
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
