#!/bin/sh

# Exit immediately if a command fails
set -e

POSTGRES_HOST=${POSTGRES_HOST:-db}
POSTGRES_PORT=${POSTGRES_PORT:-5432}

echo "Waiting for PostgreSQL at ${POSTGRES_HOST}:${POSTGRES_PORT}..."

while ! nc -z "$POSTGRES_HOST" "$POSTGRES_PORT"; do
  sleep 1
done

echo "PostgreSQL started"

# Run migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Create superuser if requested
if [ "${DJANGO_CREATE_SUPERUSER:-false}" = "true" ]; then
  echo "Checking superuser..."

  python manage.py shell <<'PY'
import os

from django.contrib.auth import get_user_model

User = get_user_model()

email = os.getenv("DJANGO_SUPERUSER_EMAIL")
password = os.getenv("DJANGO_SUPERUSER_PASSWORD")

if email and password:
    existing_user = User.objects.filter(
        email__iexact=email,
    ).first()

    if existing_user:
        print("Superuser already exists")
    else:
        User.objects.create_superuser(
            email=email,
            password=password,
        )
        print("Superuser created")
else:
    print("Superuser credentials not configured")
PY
fi

# Execute container command
exec "$@"