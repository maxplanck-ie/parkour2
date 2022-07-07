# Parkour

![Parkour](./readme.png)

Parkour is a Laboratory Information Management System (LIMS) software package
for sample processing and quality management of high-throughput sequencing
(HTS) experiments. It was designed to coordinate laboratory work by clearly
structuring tasks and facilitate high-quality sample preparation. Deep
sequencing users, laboratory personnel, and data managers will benefit from
using Parkour LIMS as a central laboratory and quality management platform:
_quickly jump to that information you need!_ 🤸🏻‍♀️

#### Demo

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

The **user manual** can be viewed at →
[ReadTheDocs](https://parkour.readthedocs.io/) 📖.

### Installation

To carry out the deployment (ideally, on a server) of this Django application,
we're using [Docker](https://docs.docker.com/get-started/) with
`docker-compose-plugin` (v2).

1. Install the system requirements 🐳, then download/ clone the latest version
   of this repo.
1. Rename `parkour.env.sample` file to `parkour.env` and edit its contents
   accordingly. For demo purposes, you can leave this as it is for the time
   being.
1. Run this command: `make`. Then, you may access the application at:
   <http://127.0.0.1/>. To log-in, you'll need to set users and passwords...
1. Optionally, you may load the database from our demo instance (as you would
   load any backup) with this "2 in 1" command: `docker cp demo.dump.sql
   parkour2-postgres:/tmp/pg.dump && docker exec -it parkour2-postgres pg_restore
   -d postgres -U postgres -c -1 /tmp/pg.dump`. This will also bring both the
   `parkour-staff` and `parkour-admin` users, as with any other data loaded in
   your database: it's up to you to keep (or remove) it.
1. Create one or more admin user(s) with the following command: `docker compose
   run parkour2-django python manage.py createsuperuser`.
1. Access <http://127.0.0.1/admin> and edit the data needed to get going (_see
   the user manual for details_).

To ease further _DevOps_ tasks, common docker commands are bundled as rules at
the `Makefile`. To uninstall, use `make clean` (the docker images remain). You
may use `make dev` to deploy an (insecure) development installation, and `make
prod` for production (Please note: in a real scenario, you'll need to: preserve
data between docker runs, configure TLS certificates, add DNS records, set a
back-up policy, probably provision a mailserver, etcetera.)
