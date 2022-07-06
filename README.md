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

> To carry out the deployment (ideally, on a server) of this Django application,
> we're using [Docker](https://docs.docker.com/get-started/) with
> `docker-compose-plugin` (v2).
>
> To ease the task, common docker CLI commands are bundled as rules at our
> `Makefile`. Please feel free to look into it.

1. Install the system requirements 🐳, then download/ clone the latest version of this repo.
1. Rename `parkour.env.sample` file to `parkour.env` and edit its contents accordingly.
1. Run this command: `make`. Then, you may access the application at: <http://127.0.0.1/>.
1. Create an admin user with the following command: `docker compose run parkour2-django python manage.py createsuperuser`.
1. Access <http://127.0.0.1/admin> and start adding your data (_see the user manual for details_).

To uninstall, use `make clean` (the docker images remain).

> Please note that in a real scenario, you'll need to: preserve data
> between docker runs, configure TLS certificates, add DNS records,
> secure database access, set a back-up policy, a mailserver, etc.
