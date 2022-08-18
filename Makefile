.PHONY: *
SHELL := /bin/bash

deploy: set-prod deploy-full

deploy-full:  deploy-django deploy-caddy deploy-ready

set-prod:
	@sed -i -e '/^DJANGO_SETTINGS_MODULE/s/\(wui\.settings\.\).*/\1prod/' parkour.env
	@sed -i -e '/^RUN .* pip install/s/\(requirements\/\).*\(\.txt\)/\1prod\2/' Dockerfile
	@sed -E -i -e '/^CMD \["gunicorn/s/"-t", "[0-9]+"/"-t", "600"/' Dockerfile
	@sed -E -i -e '/^CMD \["gunicorn/s/"--reload", //' Dockerfile
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
	@docker compose -f docker-compose.yml -f caddy.yml -f nginx.yml -f rsnapshot.yml -f ncdb.yml stop

down:
	@docker compose -f docker-compose.yml -f caddy.yml -f nginx.yml -f rsnapshot.yml -f ncdb.yml down --volumes

clean: set-prod unset-caddy
	@echo "Config reset OK. Cleaning? Try: make prune"

prune:
	@docker system prune -a -f --volumes

prod: set-prod deploy-django deploy-nginx deploy-ready
	@echo "Consider: make deploy-rsnapshot"

dev0: set-dev set-caddy deploy-full load-backup

dev: set-dev deploy-django deploy-nginx deploy-ready load-backup load-migrations

set-dev:
	@sed -i -e '/^DJANGO_SETTINGS_MODULE/s/\(wui\.settings\.\).*/\1dev/' parkour.env
	@sed -i -e '/^RUN .* pip install/s/\(requirements\/\).*\(\.txt\)/\1dev\2/' Dockerfile
	@sed -E -i -e '/^CMD \["gunicorn/s/"-t", "[0-9]+"/"--reload", "-t", "3600"/' Dockerfile
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
	@[[ -d media_dump ]] && \
		find $$PWD/media_dump/ -maxdepth 1 -type d | \
			xargs -I _ docker cp _ parkour2-django:/usr/src/app/media/

load-postgres:
	@[[ -f latest.sqldump ]] && \
		docker cp ./latest.sqldump parkour2-postgres:/tmp/parkour-postgres.dump && \
		docker exec -it parkour2-postgres pg_restore -d postgres -U postgres -1 -c /tmp/parkour-postgres.dump > /dev/null

load-backup: load-media load-postgres

backup: save-media save-postgres

save-media:
	@docker cp parkour2-django:/usr/src/app/media/ . && mv media media_dump

save-postgres:
	@docker exec -it parkour2-postgres pg_dump -Fc postgres -U postgres -f /tmp/postgres_dump && \
		docker cp parkour2-postgres:/tmp/postgres_dump latest.sqldump

deploy-rsnapshot:
	@docker compose -f rsnapshot.yml up -d && \
		sleep 1m && \
		docker exec -it parkour2-rsnapshot rsnapshot daily

test: down clean prod
	@echo "Testing on a 'clean' production deployment..."
	@docker compose run parkour2-django python -Wa manage.py test

shell:
	@echo "Spawning bpython shell plus (only for dev deployments)..."
	@docker exec -it parkour2-django python manage.py shell_plus --bpython

reload-nginx:
	@docker exec -it parkour2-nginx nginx -s reload

reload-django:
	@find $$PWD/parkour_app/ -maxdepth 1 -type d -mtime -3 | \
		xargs -I _ docker cp _ parkour2-django:/usr/src/app/

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
