web: gunicorn conf.wsgi
worker: celery --app conf worker --beat --loglevel=info