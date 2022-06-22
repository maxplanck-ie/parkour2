# syntax = docker/dockerfile:experimental
FROM python:3.8.13
WORKDIR /usr/src/app
COPY ./parkour_app .
RUN --mount=type=cache,target=/root/.cache pip install -r requirements/prod.txt
EXPOSE 8000
CMD gunicorn wui.wsgi:application -w 2 -b :8000  # TODO: -k uvicorn.workers.UvicornWorker
