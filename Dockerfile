FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    zip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY inputs.py .
COPY .env.example .env

# Create config directory
RUN mkdir -p config

# Expose Flask port
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=inputs.py
ENV FLASK_ENV=production
ENV FLASK_DEBUG=false

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Run the application
CMD ["python", "inputs.py"]
