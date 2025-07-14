release: python setup_static.py && python migrate.py
web: gunicorn proyecto.wsgi --bind 0.0.0.0:$PORT