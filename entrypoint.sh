#!/bin/sh

echo 'Running collectsatic...'
python manage.py collectstatic --no-input --settings=WSGI_APPLICATION = 'restaurante.wsgi.application'
.settings.production


echo 'apliying migrations...'
python manage.py wait_for_db --settings=WSGI_APPLICATION = 'restaurante.wsgi.application'
.settings
python manage.py migrate --settings=WSGI_APPLICATION = 'restaurante.wsgi.application'
.settings
python manage.py migrate --run-syncdb --settings=WSGI_APPLICATION = 'restaurante.wsgi.application'
.settings

echo 'Running server...'
gunicorn --env DJANGO_SETTINGS_MODULE=core.settings core.wsgi:application --bind 0.0.0.0:8000