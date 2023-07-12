# syntax = docker/dockerfile:experimental
FROM python:3.11-bullseye AS pk2_base
LABEL maintainer="Adrian S. <lims@omics.dev>"

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update --fix-missing \
    && apt-get -y upgrade \
    && apt-get install -y software-properties-common \
    && apt-get install -y --no-install-recommends \
       locales \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN localedef -i en_US -f UTF-8 en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8
ENV LC_TIME en_DK.UTF-8
ENV TZ "Europe/Berlin"

WORKDIR /usr/src/app
COPY ./parkour_app .
RUN --mount=type=cache,target=/root/.cache pip install -r requirements/prod.txt
EXPOSE 8000
ENV PYTHONDEVMODE 0
ENV PYTHONBREAKPOINT ipdb.set_trace
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
#CMD ["python", "/usr/src/app/manage.py", "runserver_plus", "0.0.0.0:8000"]
CMD ["gunicorn", "wui.wsgi:application", "-t", "600", "-w", "4", "-b", ":8000"]

FROM pk2_base AS pk2_playwright

RUN playwright install --install-deps  # FIXME
