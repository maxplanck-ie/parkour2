# syntax = docker/dockerfile:experimental
FROM python:3.8.13
WORKDIR /usr/src/app
COPY ./parkour_app .
RUN --mount=type=cache,target=/root/.cache pip install -r requirements/prod.txt
EXPOSE 8000
# RUN adduser --system --no-create-home staysafe
# USER staysafe
ENV PYTHONBREAKPOINT ipdb.set_trace
ENV PYTHONUNBUFFERED 1
CMD gunicorn wui.wsgi:application -t 600 -w 2 -b :8000  # TODO: -k uvicorn.workers.UvicornWorker
