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

To carry out the deployment (ideally, on a server) we're using
[Docker](https://docs.docker.com/get-started/) with `docker-compose-plugin`
(v2). To ease the task, common docker CLI commands are bundled as rules at our
`Makefile`. First, install these system requirements 🐳, then download/ clone
the latest version of this repo.

In second place, after decompressing the code into a folder, rename
`parkour.env.sample` file to `parkour.env` and edit its contents according to
your liking.

Finally, run this command: `make`. Afterwards, you may access the application
at: <http://127.0.0.1/>, run `docker compose logs -f` if you want to see what's
going on.

Use `make clean` to stop all the composed services without saving any data (the
docker images remain).

> In more real scenarios, you'll need to: preserve data between docker runs,
> configure TLS certificates, add DNS records, secure database access, set a
> back-up policy, a mailserver, etc. All these tasks are beyond the scope of this
> quickstart guide.
