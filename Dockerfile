# Use the official Python 3.13 slim image as the base
FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    build-essential \
    libpq-dev \
    netcat-openbsd \
&& rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy project files
COPY . /app/

# Make entrypoint script executable
RUN chmod +x /app/docker/entrypoint.sh

# Expose port
EXPOSE 8000

# Run entrypoint script first
ENTRYPOINT ["sh", "/app/docker/entrypoint.sh"]

# Production command used by Render
# Locally, docker-compose.yml overrides this with:
# python manage.py runserver 0.0.0.0:8000
CMD ["sh", "-c", "gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000}"]