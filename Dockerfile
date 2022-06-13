FROM python:3.6.15-bullseye
WORKDIR /usr/src/app
COPY ./parkour_app .
RUN pip install -r requirements/prod.txt
