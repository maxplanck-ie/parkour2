FROM node:20-bookworm
LABEL maintainer="Adrian S. <lims@omics.dev>"

ENV \
    DEBIAN_FRONTEND=noninteractive \
    LANG=en_US.UTF-8 \
    LANGUAGE=en_US:en \
    LC_ALL=en_US.UTF-8 \
    LC_TIME=en_DK.UTF-8 \
    TZ="Europe/Berlin"

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
COPY ./frontend .
EXPOSE 5173

CMD ["npm", "start"]
