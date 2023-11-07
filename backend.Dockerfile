# syntax = docker/dockerfile:experimental
FROM python:3.11-bullseye AS pk2_base
LABEL maintainer="Adrian S. <lims@omics.dev>"

ENV \
    DEBIAN_FRONTEND=noninteractive \
    LANG=en_US.UTF-8 \
    LANGUAGE=en_US:en \
    LC_ALL=en_US.UTF-8 \
    LC_TIME=en_DK.UTF-8 \
    TZ="Europe/Berlin"

RUN apt-get update --fix-missing \
    && apt-get -y upgrade \
    && apt-get install -y software-properties-common \
    && apt-get install -y --no-install-recommends \
    jq \
    less \
    locales \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN localedef -i en_US -f UTF-8 en_US.UTF-8

WORKDIR /usr/src/app
COPY ./backend .
EXPOSE 8000
RUN --mount=type=cache,target=/root/.cache pip install -r requirements/base.txt
CMD ["gunicorn", "wui.wsgi:application", "--name=parkour2", "--timeout=600", "--workers=4", "--bind=0.0.0.0:8000"]

# ----------------------
FROM pk2_base AS pk2_prod
ENV DJANGO_SETTINGS_MODULE=wui.settings.prod
RUN --mount=type=cache,target=/root/.cache pip install -r requirements/prod.txt

# ----------------------
FROM pk2_base AS pk2_dev
RUN echo "from functools import partial\nimport rich\nhelp = partial(rich.inspect, help=True, methods=True)" \
    > /root/.pythonrc
ENV DJANGO_SETTINGS_MODULE=wui.settings.dev \
    PYTHONSTARTUP=/root/.pythonrc \
    PYTHONDEVMODE=0 \
    PYTHONBREAKPOINT=ipdb.set_trace \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
RUN --mount=type=cache,target=/root/.cache pip install -r requirements/dev.txt
CMD ["python", "/usr/src/app/manage.py", "runserver_plus", "0.0.0.0:8000"]

# ----------------------
FROM pk2_dev AS pk2_testing
ENV DJANGO_SETTINGS_MODULE=wui.settings.testing
RUN --mount=type=cache,target=/root/.cache pip install -r requirements/testing.txt

# ----------------------
FROM pk2_testing AS pk2_playwright
RUN playwright install --with-deps firefox
