###########
# BUILDER #
###########

FROM python:3.11-slim AS builder

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 

# install system dependencies in one layer (расширенный набор для PostgreSQL)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        g++ \
        libc6-dev \
        libpq-dev \
        postgresql-client \
        python3-dev && \
    rm -rf /var/lib/apt/lists/*

# upgrade pip
RUN pip install --upgrade pip

# copy requirements first for better layer caching
COPY requirements.txt ./

RUN pip wheel --no-cache-dir --no-deps --wheel-dir /usr/src/app/wheels -r requirements.txt

#########
# FINAL #
#########

FROM python:3.11-slim

# create app user and directories in one layer
RUN groupadd --system app && \
    useradd --system --gid app --home /home/app --create-home --shell /usr/sbin/nologin app && \
    mkdir -p /home/app/web

# set environment variables
ENV HOME=/home/app \
    APP_HOME=/home/app/web \
    LANG=ru_RU.UTF-8 \
    LC_ALL=ru_RU.UTF-8 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR $APP_HOME

# install system dependencies and setup locales in one layer
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        netcat-traditional \
        locales \
        libpq5 \
        postgresql-client && \
    sed -i -e 's/# ru_RU.UTF-8 UTF-8/ru_RU.UTF-8 UTF-8/' /etc/locale.gen && \
    dpkg-reconfigure --frontend=noninteractive locales && \
    rm -rf /var/lib/apt/lists/*

# copy wheels and install python dependencies
COPY --from=builder /usr/src/app/wheels /wheels
COPY --from=builder /usr/src/app/requirements.txt .

RUN pip install --upgrade pip && \
    pip install --no-cache /wheels/* && \
    rm -rf /wheels

# copy and setup entrypoint
COPY --chown=app:app entrypoint.sh .
RUN chmod +x entrypoint.sh

# copy application code
COPY --chown=app:app . .

# switch to non-root user
USER app

EXPOSE 8000

# use exec form for better signal handling
ENTRYPOINT ["./entrypoint.sh"]