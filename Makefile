SHELL := /bin/bash

deploy: set-local set-prod deploy-full

deploy-full:  deploy-django deploy-caddy deploy-ready

set-local:
	sed -i '/^http/s/http\:\/\/.* {/http:\/\/127\.0\.0\.1 {/' Caddyfile

set-prod:
	sed -i '/^DJANGO_SETTINGS_MODULE/s/\(wui\.settings\.\).*/\1prod/' parkour.env
	sed -i '/^RUN .* pip install/s/\(requirements\/\).*\(\.txt\)/\1prod\2/' Dockerfile

deploy-django: deploy-network deploy-containers

deploy-network:
	docker network create parkour2_default

deploy-containers:
	docker compose build
	docker compose up -d

deploy-ready: collect-static load-migrations

collect-static:
	docker compose run parkour2-django python manage.py collectstatic --noinput

load-migrations:
	docker compose run parkour2-django python manage.py makemigrations && \
        docker compose run parkour2-django python manage.py migrate

down:
	docker compose -f docker-compose.yml -f caddy.yml down

clean: down
	docker volume rm parkour2_caddy_config parkour2_caddy_data parkour2_pgdb parkour2_media parkour2_staticfiles
	docker images -f "dangling=true" -q  # docker rmi
	# rm -rf ./cache_pip

## DevOps ##################################################################

prod: set-prod deploy-full load-backup

dev: set-dev deploy-full load-backup

set-dev:
	sed -i '/^DJANGO_SETTINGS_MODULE/s/\(wui\.settings\.\).*/\1dev/' parkour.env
	sed -i '/^RUN .* pip install/s/\(requirements\/\).*\(\.txt\)/\1dev\2/' Dockerfile

deploy-caddy:
	docker compose -f caddy.yml up -d

load-backup:
	[[ -e latest.dump.sql ]]; docker cp ./latest.dump.sql parkour2-postgres:/tmp/parkour-postgres.dump && \
	docker exec -it parkour2-postgres pg_restore -d postgres -U postgres -c -1 /tmp/parkour-postgres.dump

reload:
	docker container stop parkour2-django
	$(MAKE) deploy-containers deploy-caddy load-migrations
	docker compose logs

test:
	docker compose run parkour2-django python manage.py test

compile:
	cd parkour_app/ && \
	source ./env/bin/activate && \
	pip-compile-multi

dev-setup:
	cd parkour_app/ && \
	env python3 -m venv env && \
	source ./env/bin/activate && \
	pip install \
		pre-commit \
		pip-compile-multi

# Don't confuse this ^up^here^ with the app development environment (dev.in &
# dev.txt), mind the 'hierarchical' difference. We're going to use
# pip-compile-multi to manage parkour_app/requirements/*.txt files.


# Last, but not least, please also note that there's pre-commit to keep a tidy
# repo. And, git-lfs (e.g.  `.gitattributes`) to track `parkour_app/static/`.
