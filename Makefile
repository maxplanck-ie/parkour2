.PHONY: *
SHELL := /bin/bash

deploy: set-prod deploy-full

deploy-full:  deploy-django deploy-caddy deploy-ready

set-prod:
	@sed -i -e '/^DJANGO_SETTINGS_MODULE/s/\(wui\.settings\.\).*/\1prod/' parkour.env
	@sed -i -e '/^RUN .* pip install/s/\(requirements\/\).*\(\.txt\)/\1prod\2/' Dockerfile
	@sed -E -i -e '/^CMD gunicorn/s/-t [0-9]+/-t 600/' Dockerfile
	@sed -E -i -e '/^ +tty/s/: .*/: false/' \
			-e '/^ +stdin_open/s/: .*/: false/' docker-compose.yml


deploy-django: deploy-network deploy-containers

deploy-network:
	@docker network create parkour2_default

deploy-containers:
	@docker compose build
	@docker compose up -d

deploy-ready: collect-static load-migrations

collect-static:
	@docker compose run parkour2-django python manage.py collectstatic --noinput > /dev/null

load-migrations:
	@docker compose run parkour2-django python manage.py makemigrations > /dev/null && \
	docker compose run parkour2-django python manage.py migrate --noinput > /dev/null

stop:
	@docker compose -f docker-compose.yml -f caddy.yml -f nginx.yml -f ncdb.yml stop

down:
	@docker compose -f docker-compose.yml -f caddy.yml -f nginx.yml -f ncdb.yml down

clean: set-prod unset-caddy
	@echo "Not Run:"
	@echo "docker volume rm $$(docker volume ls -f dangling=true -q) > /dev/null"
	@echo "docker rmi $$(docker images -f "dangling=true" -q) > /dev/null"

prune: clean
	@docker system prune -a -f --volumes

prod: set-prod deploy-django deploy-nginx deploy-ready

dev: set-dev set-caddy deploy-full load-media load-backup

pk7: set-dev deploy-django deploy-nginx deploy-ready load-media load-backup

set-dev:
	@sed -i -e '/^DJANGO_SETTINGS_MODULE/s/\(wui\.settings\.\).*/\1dev/' parkour.env
	@sed -i -e '/^RUN .* pip install/s/\(requirements\/\).*\(\.txt\)/\1dev\2/' Dockerfile
	@sed -E -i -e '/^CMD gunicorn/s/-t [0-9]+/-t 36000/' Dockerfile
	@sed -E -i -e '/^ +tty/s/: .*/: true/' \
			-e '/^ +stdin_open/s/: .*/: true/' docker-compose.yml

set-caddy:
	@sed -i -e "/\:\/etc\/caddy\/Caddyfile$$/s/\.\/.*\:/\.\/caddyfile\.in\.use\:/" caddy.yml

unset-caddy:
	@sed -i -e "/\:\/etc\/caddy\/Caddyfile$$/s/\.\/.*\:/\.\/Caddyfile\:/" caddy.yml

deploy-caddy:
	@docker compose -f caddy.yml up -d

deploy-nginx:
	@docker compose -f nginx.yml up -d

deploy-ncdb:
	@docker compose -f ncdb.yml up -d

load-media:
	@[[ -d media_dumps ]] && \
		find $$PWD/media_dumps/latest/ -maxdepth 1 -type d | \
			xargs -I _ docker cp _ parkour2-django:/usr/src/app/media/

load-backup:
	@[[ -f latest.sqldump ]] && \
		docker cp ./latest.sqldump parkour2-postgres:/tmp/parkour-postgres.dump && \
		docker exec -it parkour2-postgres pg_restore -d postgres -U postgres -1 -c /tmp/parkour-postgres.dump > /dev/null

test: clean prod
	@echo "Testing on a 'clean' production deployment..."
	@docker compose run parkour2-django python -Wa manage.py test

shell:
	@echo "Spawning bpython shell plus (only for dev deployments)..."
	@docker exec -it parkour2-django python manage.py shell_plus --bpython

compile:
	@cd parkour_app/ && \
		source ./env/bin/activate && \
		pip-compile-multi

dev-setup:
	@cd parkour_app/ && \
		env python3 -m venv env && \
		source ./env/bin/activate && \
		env python3 -m pip install --upgrade pip && \
		pip install \
			pre-commit \
			pip-compile-multi \
			sphinx

# Don't confuse this ^up^here^ with the app development environment (dev.in &
# dev.txt), mind the 'hierarchical' difference. We're going to use
# pip-compile-multi to manage parkour_app/requirements/*.txt files.
#
#
# Last, but not least, please also note that there's pre-commit to keep a tidy
# repo. And, git-lfs (e.g.  `.gitattributes`) to track `parkour_app/static/`.
