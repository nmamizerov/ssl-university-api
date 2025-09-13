#!/bin/sh

python manage.py migrate
gunicorn -c gunicorn.conf.py backend.wsgi:application 