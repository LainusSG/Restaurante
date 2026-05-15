#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

pip install mediapipe --upgrade

python manage.py collectstatic --no-input

python manage.py migrate

python manage.py migrate --run-syncdb 

python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username="admin").exists():
    User.objects.create_superuser("admin", "admin@example.com", "admin123")
    print("✅ Superusuario creado: admin / admin123")
else:
    print("ℹ️ Superusuario ya existe, no se crea otro.")
END