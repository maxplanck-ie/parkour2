# syntax = docker/dockerfile:experimental
ARG PyVersion=3.11
FROM python:${PyVersion}-bullseye AS pk2_base

ENV \
    DEBIAN_FRONTEND=noninteractive \
    LANG=en_US.UTF-8 \
    LANGUAGE=en_US:en \
    LC_ALL=en_US.UTF-8 \
    LC_TIME=en_DK.UTF-8 \
    TZ="Europe/Berlin" \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_ROOT_USER_ACTION=ignore

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
ENV DJANGO_SETTINGS_MODULE=wui.settings.prod
ARG PyVersion=3.11
RUN --mount=type=cache,target=/root/.cache pip install -r requirements/${PyVersion}/base.txt
CMD ["gunicorn", "wui.wsgi:application", "--name=parkour2", "--timeout=600", "--workers=4", "--bind=0.0.0.0:8000"]

# ----------------------
FROM pk2_base AS pk2_prod
RUN --mount=type=cache,target=/root/.cache pip install -r requirements/${PyVersion}/prod.txt

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
RUN --mount=type=cache,target=/root/.cache pip install -r requirements/${PyVersion}/dev.txt
CMD ["python", "/usr/src/app/manage.py", "runserver_plus", "0.0.0.0:8000"]

# ----------------------
FROM pk2_dev AS pk2_testing
ENV DJANGO_SETTINGS_MODULE=wui.settings.testing
RUN --mount=type=cache,target=/root/.cache pip install -r requirements/${PyVersion}/testing.txt

# ----------------------
FROM pk2_testing AS pk2_playwright
RUN playwright install --with-deps firefox
