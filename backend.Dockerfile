## Node runtime + ro-crate-html-js CLI, built once here so the Python image below
## can just copy the binaries in (no apt-installed Node in the Python image).
FROM node:24-bullseye AS ro_crate_html_tool
WORKDIR /opt/ro-crate-html-js
RUN npm install ro-crate-html-js

FROM python:3.12-bookworm AS pk2_base
ARG PyVersion=3.12

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
    UV_SYSTEM_PYTHON=1 \
    PYTHONIOENCODING="UTF-8" \
    PYTHONUTF8=1

RUN apt-get update --fix-missing \
    && apt-get install -y --no-install-recommends less locales \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN localedef -i en_US -f UTF-8 en_US.UTF-8

## Pinned so uv releases don't invalidate the apt layers above;
## kept up-to-date by the weekly deps.yml workflow
COPY --from=ghcr.io/astral-sh/uv:0.12.5 /uv /bin/uv

WORKDIR /usr/src/app

## Node binary + ro-crate-html-js CLI, copied from the ro_crate_html_tool stage above.
COPY --from=ro_crate_html_tool /usr/local/bin/node /usr/local/bin/node
COPY --from=ro_crate_html_tool /opt/ro-crate-html-js/node_modules /opt/ro-crate-html-js/node_modules
ENV PATH="/opt/ro-crate-html-js/node_modules/.bin:${PATH}"

## Pre-heat the cache
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install setuptools wheel psycopg2 gunicorn django~=5.2
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
