web: gunicorn core.wsgi
worker: celery -A core worker -l info
beat: celery -A core beat -l info
release: python manage.py migrate