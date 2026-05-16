web: python restoran_pos/manage.py migrate --noinput && python restoran_pos/manage.py seed_default_data --reset-passwords && gunicorn --chdir restoran_pos restoran.wsgi --log-file -
