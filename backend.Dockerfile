ARG PyVersion=3.12  # to be repeated after FROM, docker syntax is at fault.
FROM python:${PyVersion}-bullseye AS pk2_base
ARG PyVersion=3.12
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

ENV \
    DEBIAN_FRONTEND=noninteractive \
    LANG=en_US.UTF-8 \
    LANGUAGE=en_US:en \
    LC_ALL=en_US.UTF-8 \
    LC_TIME=en_DK.UTF-8 \
    TZ="Europe/Berlin" \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_ROOT_USER_ACTION=ignore \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_SYSTEM_PYTHON=1

RUN apt-get update --fix-missing \
    && apt-get -y upgrade \
    && apt-get install -y software-properties-common \
    && apt-get install -y --no-install-recommends less locales \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN localedef -i en_US -f UTF-8 en_US.UTF-8

WORKDIR /usr/src/app

## Pre-heat the cache
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install setuptools wheel psycopg2 gunicorn django~=4.2
## First, bring dependencies specification and install them
COPY ./backend/requirements requirements
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install -r requirements/${PyVersion}/base.txt
## Second, bring source code, without invalidating the docker layer ;)
COPY ./backend .

EXPOSE 8000
ENV DJANGO_SETTINGS_MODULE=wui.settings.prod
CMD ["gunicorn", "wui.wsgi:application", "--bind=0.0.0.0:8000", "--name=pk2", "--timeout=600", \
     "--worker-class=gthread", "--worker-tmp-dir=/dev/shm", "--workers=4", "--threads=6"]

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
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install -r requirements/${PyVersion}/dev.txt
CMD ["python", "/usr/src/app/manage.py", "runserver_plus", "0.0.0.0:8000"]

# ----------------------
FROM pk2_dev AS pk2_testing
ENV DJANGO_SETTINGS_MODULE=wui.settings.testing
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install -r requirements/${PyVersion}/testing.txt

# ----------------------
FROM pk2_testing AS pk2_playwright
RUN playwright install --with-deps firefox
