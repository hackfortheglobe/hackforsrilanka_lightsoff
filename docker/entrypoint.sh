python manage.py makemigrations
python manage.py runscript periodic_task_renew
python manage.py migrate --noinput || exit 1
exec "$@"