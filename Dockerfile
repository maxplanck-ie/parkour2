# syntax = docker/dockerfile:experimental
FROM python:3.8.13
WORKDIR /usr/src/app
COPY ./parkour_app .
RUN --mount=type=cache,target=/root/.cache pip install -r requirements/prod.txt
EXPOSE 8000
ENV PYTHONBREAKPOINT ipdb.set_trace
ENV PYTHONUNBUFFERED 1
CMD ["gunicorn", "wui.wsgi:application", "-t", "3600", "-w", "2", "-b", ":8000"]
