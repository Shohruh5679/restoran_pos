web: cd restoran_pos && python manage.py migrate --noinput && python manage.py seed_default_data --reset-passwords && gunicorn restoran.wsgi --bind 0.0.0.0:$PORT --log-file -
