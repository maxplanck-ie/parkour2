FROM python:3.6.15-bullseye
WORKDIR /usr/src/app
COPY ./parkour_app .
RUN pip install -r requirements/prod.txt
CMD gunicorn wui.wsgi:application -w 2 -b :8000  # TODO: -k uvicorn.workers.UvicornWorker
