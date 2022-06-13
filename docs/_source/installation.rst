============
Installation
============


Quick start
===========

It is assumed you have a recent version of `Docker`_ running and the `docker-compose`_ tool installed.

Clone the repository::

  git clone https://github.com/maxplanck-ie/docker-parkour.git
  cd docker-parkour

Customize your environment variables as given in this template::

  parkour.env
  
Build the images and start the services::

  docker-compose up -d --build

Migrate the database tables::

  docker-compose run parkour-web python manage.py migrate

Collect static files::

  docker-compose run parkour-web python manage.py collectstatic --no-input --verbosity 0

Create a superuser (admin)::

  docker-compose run parkour-web python manage.py createsuperuser

Open Parkour LIMS at ``http://localhost/``


Manual setup
============

Prerequisites
-------------

* Python 3.6
* PostgreSQL

Configure the database
----------------------

.. code-block:: sql

   CREATE DATABASE <DB_NAME>;
   CREATE USER <DB_USER> WITH PASSWORD <DB_PASS>;
   GRANT ALL PRIVILEGES ON DATABASE <DB_NAME> TO <DB_USER>;

Export environment variables
----------------------------

.. code-block:: bash

  export SECRET_KEY=<SECRET_KEY>
  export DJANGO_SETTINGS_MODULE=wui.settings.dev
  export DATABASE_URL=postgres://<DB_USER>@<DB_HOST>:<DB_PORT>/<DB_NAME>

Installation steps
------------------

Clone the repository::

  git clone https://github.com/maxplanck-ie/parkour.git
  cd parkour

Install the requirements::

  pip install -r requirements/dev.txt

Migrate the database tables::

  python manage.py migrate

Create a superuser (admin)::

  python manage.py createsuperuser

Run the server::

  ./manage.py runserver


.. _Docker: https://docker.com/

.. _docker-compose: https://docs.docker.com/compose/install/
