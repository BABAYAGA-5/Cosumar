#!/usr/bin/env sh
set -e

# Wait for Postgres if DB_HOST env var is provided
if [ -n "$DB_HOST" ]; then
  echo "Waiting for database at $DB_HOST:$DB_PORT..."
  : ${DB_PORT:=5432}
  until nc -z "$DB_HOST" "$DB_PORT"; do
    sleep 1
  done
fi

# Apply migrations and collect static (no static root configured here)
python manage.py migrate --noinput

# Start Gunicorn
exec gunicorn Cosumar_Digital_Recrutement.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 3 \
  --timeout 120 \
  --access-logfile '-' \
  --error-logfile '-'
