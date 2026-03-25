# ============================================
# INDMoney Weekly Pulse — Dockerfile
# ============================================
# Multi-stage not needed; single slim image is sufficient
# for a simple Python pipeline.

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies first (Docker layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory for runtime outputs
RUN mkdir -p /app/data

# Default port for Streamlit
ENV PORT=8501
EXPOSE ${PORT}

# Run the pipeline
CMD ["python", "main.py"]
