FROM python:3.12-slim

# Install system dependencies for WeasyPrint (Cairo/Pango/GObject)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libjpeg-dev \
    libopenjp2-7-dev \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency requirements
COPY backend/requirements.txt .

RUN chmod +x start_worker.sh

# Install python requirements
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY backend/app /app/app

# Expose standard port (Railway dynamically overrides this via PORT env)
EXPOSE 8000

# Default launch command for the web api service
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
