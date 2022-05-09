python manage.py makemigrations
python manage.py migrate --noinput || exit 1
exec "$@"