FROM python:3.7-slim-bullseye

WORKDIR /app

EXPOSE 8000

RUN apt update \
 && apt install -y build-essential python3-dev python2.7-dev libldap2-dev libsasl2-dev tox lcov valgrind

RUN LC_ALL=C DEBIAN_FRONTEND=noninteractive apt install -y slapd ldap-utils

RUN pip install -U pip -U setuptools supervisor

COPY requirements.txt /app/

RUN pip install -r requirements.txt

ENTRYPOINT python manage.py migrate \
        && python manage.py runserver 0.0.0.0:8000
