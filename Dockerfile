# syntax = docker/dockerfile:experimental
FROM python:3.8.13-slim
WORKDIR /usr/src/app
COPY ./parkour_app .
RUN --mount=type=cache,target=/root/.cache pip install -r requirements/prod.txt
CMD gunicorn wui.wsgi:application -w 2 -b :8000  # TODO: -k uvicorn.workers.UvicornWorker
