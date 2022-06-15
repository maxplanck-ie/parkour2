# Parkour LIMS
[![Build Status](https://travis-ci.org/maxplanck-ie/parkour.svg?branch=master)](https://travis-ci.org/maxplanck-ie/parkour) [![Documentation Status](https://readthedocs.org/projects/parkour/badge/?version=latest)](http://parkour.readthedocs.io/?badge=latest)

![Parkour LIMS](./readme.png)

Parkour LIMS (Laboratory Information Management System) is a software package
for sample processing and quality management of next-generation sequencing
(NGS) data and samples. Besides extensive functionality, most of existing LIMS
are missing electronic laboratory notebook aspects to support, organize, and
ultimately standardize initial laboratory-intensive sample preparation steps.
The LIMS was designed to coordinate laboratory work by clearly structuring
tasks and facilitate high-quality sample preparation. Deep sequencing users,
laboratory personnel, and data managers will benefit from using Parkour LIMS as
a central laboratory and quality management platform.

### Demo

A demonstration instance is available at
[http://parkour-demo.ie-freiburg.mpg.de](http://parkour-demo.ie-freiburg.mpg.de).
The following accounts are available on that instance:

 - A typical "staff" account with the username
   "parkour-staff@parkour-demo.ie-freiburg.mpg.de" and password
"parkour-staff".
 - A typical "admin" account with the username
   "parkour-admin@parkour-demo.ie-freiburg.mpg.de" and password
"parkour-admin".

Please note that the instance is reset every 12 hours!


## Documentation

Documentation and user manual can be viewed
[here](https://parkour.readthedocs.io/).

#### Deployment

We're using [Docker](https://docs.docker.com/get-started/) with
`docker-compose-plugin` (v2) in our `Makefile`. First, install these system
requirements (on Windows and Mac, you only need Docker Desktop).

Before running this Django application, populate your own `parkour.env` file
with the following configuration variables. This file sits in the project root
(e.g.  next to `caddy.yml`). You may copy, and edit:

```
SECRET_KEY=generate one with openssl
DJANGO_SETTINGS_MODULE=wui.settings.prod
ADMIN_NAME=admin
ADMIN_EMAIL=your email
EMAIL_HOST=mail.server.tld
EMAIL_SUBJECT_PREFIX=[Parkour]
SERVER_EMAIL=your email
DATABASE_URL=postgres://postgres:change_me__stay_safe@parkour2-postgres:5432/postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=change_me__stay_safe
TIME_ZONE=Europe/Berlin
```

Finally, run this command: `make`. Afterwards, you may access the application
at: <http://127.0.0.1:8000>, run `docker compose logs -f` if you want to see
what's going on, and use `make clean` to stop all the composed services without
saving any data (only the vanilla docker images remain).

In more real scenarios, you'll need to switch to production environment,
preserve data between docker runs, configure TLS certificates, add DNS records,
secure database access, set a back-up policy, a mailserver, etc. All these
tasks are beyond the scope of this quickstart guide. We are using Caddy as
webserver for production, and thanks to the structure of the project, you may
easily switch to Nginx or whatever you prefer 🚪...


## Development

The `Makefile` is a good place to start diving deeper. It has a sane set of
rules to deploy with debugging, or not.

We're in the process of updating the codebase to the upcoming Django 4.2 LTS
version. On a much longer-term goal, there's the possibility of getting a whole
new UX, dropping the old Ext JS dependency.
