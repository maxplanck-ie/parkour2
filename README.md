# Parkour LIMS
[![Build Status](https://travis-ci.org/maxplanck-ie/parkour.svg?branch=master)](https://travis-ci.org/maxplanck-ie/parkour) [![Documentation Status](https://readthedocs.org/projects/parkour/badge/?version=latest)](http://parkour.readthedocs.io/?badge=latest)

![Parkour LIMS](./readme.png)

Parkour LIMS (Laboratory Information Management System) is a software package for sample processing and quality management of next-generation sequencing (NGS) data and samples. Besides extensive functionality, most of existing LIMS are missing electronic laboratory notebook aspects to support, organize, and ultimately standardize initial laboratory-intensive sample preparation steps. The LIMS was designed to coordinate laboratory work by clearly structuring tasks and facilitate high-quality sample preparation. Deep sequencing users, laboratory personnel, and data managers will benefit from using Parkour LIMS as a central laboratory and quality management platform.

### Demo

A demonstration instance is available at [http://parkour-demo.ie-freiburg.mpg.de](http://parkour-demo.ie-freiburg.mpg.de). The following accounts are available on that instance:

 - A typical "staff" account with the username "parkour-staff@parkour-demo.ie-freiburg.mpg.de" and password "parkour-staff".
 - A typical "admin" account with the username "parkour-admin@parkour-demo.ie-freiburg.mpg.de" and password "parkour-admin".

Please note that the instance is reset every 12 hours!

## Documentation

Documentation and user manual can be viewed [here](https://parkour.readthedocs.io/).

#### Deployment

To get started, populate your own `parkour.env` file with the configuration variables. This files sits in the project root. You may copy, and edit this:

```
SECRET_KEY=generate one with openssl
DJANGO_SETTINGS_MODULE=wui.settings.prod
ADMIN_NAME=admin
ADMIN_EMAIL=your email
EMAIL_HOST=mail.server.tld
EMAIL_SUBJECT_PREFIX=[Parkour]
SERVER_EMAIL=your email
DATABASE_URL=postgres://postgres:postgres@postgres:5432/postgres
```

Finally, run this command: `make`. Afterwards, you may access the application at: <http://127.0.0.1:8000>. In more real scenarios, you'll need to secure database access, configure TLS encryption, add DNS records, etc. All these tasks are beyond the scope of this quickstart guide, and should probably count with the support of your IT department.

## Contributions

We're in the process of updating the codebase to the upcoming Django 4.2 LTS version. On a much longer-term goal, there's the possibility of getting a whole new UX, dropping the old Ext JS dependency.

<!--
Developer onboarding:
1. Makefile
1. To manage parkour_app/requirements/ we're using pip-compile-multi: https://pip-compile-multi.readthedocs.io/en/latest/installation.html there's parkour_app/env already in git ignore. Don't confuse this with the app development environment (dev.in & dev.txt), mind the 'hierarchical' difference.
1. ...etc
1. Details: .gitattributes (lfs)
-->


