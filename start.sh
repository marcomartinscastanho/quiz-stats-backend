#!/bin/bash
set -e

echo "Running migrations..."
python manage.py migrate
python manage.py collectstatic --noinput

echo "Checking for default superuser..."

python manage.py shell -c "
import os
from django.contrib.auth import get_user_model
User = get_user_model()
username = os.getenv('ADMIN_USERNAME')
email = os.getenv('ADMIN_EMAIL')
password = os.getenv('ADMIN_PASSWORD')

if not username or not password or not email:
    print('Admin credentials are not fully set in environment variables.')
else:
    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username, email, password)
        print('Default superuser created')
    else:
        print('Superuser already exists')
"

echo "Starting server..."
exec python manage.py runserver 0.0.0.0:8000