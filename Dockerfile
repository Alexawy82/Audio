FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt && \
    # Install gunicorn for production deployment
    pip install --no-cache-dir gunicorn

# Copy the application code
COPY . .

# Create necessary directories with proper permissions
RUN mkdir -p /app/data/uploads /app/data/output /app/data/temp /app/data/cache /app/data/logs && \
    chmod -R 755 /app/data

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=5000
ENV HOST=0.0.0.0
ENV DEBUG=false
ENV DATA_DIR=/app/data
ENV UPLOAD_DIR=/app/data/uploads
ENV OUTPUT_FOLDER=/app/data/output
ENV TEMP_FOLDER=/app/data/temp
ENV CACHE_DIR=/app/data/cache

# Expose the port the app runs on
EXPOSE 5000

# Use gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "src.app:app"] 