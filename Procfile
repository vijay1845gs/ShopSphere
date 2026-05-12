web: gunicorn config.wsgi:application --workers 2 --bind 0.0.0.0:$PORT
release: python manage.py migrate --settings=config.settings.production
worker: celery -A config.celery worker --loglevel=info
beat: celery -A config.celery beat --loglevel=info
