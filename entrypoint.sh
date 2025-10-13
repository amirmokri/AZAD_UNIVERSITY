#!/bin/bash

# Exit on error
set -e

echo "Starting University Hub application..."

# Wait for database to be ready using Python
echo "Waiting for database..."
python << END
import os
import time
import socket

db_host = os.environ.get('DB_HOST', 'localhost')
db_port = int(os.environ.get('DB_PORT', '3306'))

max_retries = 30
retry_count = 0

while retry_count < max_retries:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((db_host, db_port))
        sock.close()
        
        if result == 0:
            print(f"Database is ready at {db_host}:{db_port}")
            break
    except socket.gaierror:
        pass
    
    retry_count += 1
    if retry_count < max_retries:
        time.sleep(1)
    else:
        print(f"Could not connect to database at {db_host}:{db_port} after {max_retries} attempts")
        exit(1)
END

echo "Database connection verified!"

# Run migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Create superuser if it doesn't exist (optional, for first deployment)
echo "Checking for superuser..."
python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    print("No admin user found")
END

# Start Gunicorn
echo "Starting Gunicorn server..."
exec gunicorn --bind 0.0.0.0:8000 \
    --workers 4 \
    --threads 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    university_hub.wsgi:application

