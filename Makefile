.PHONY: *
SHELL := /bin/bash

deploy: set-prod deploy-full

help:
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST) | sort
	@echo "" && echo 'Please note: this is just a list of the most common available routines, for details see the source Makefile.'

deploy-full:  deploy-django deploy-caddy deploy-ready

set-prod:
	@sed -i -e '/^DJANGO_SETTINGS_MODULE/s/\(wui\.settings\.\).*/\1prod/' parkour.env
	@sed -i -e '/^RUN .* pip install/s/\(requirements\/\).*\(\.txt\)/\1prod\2/' Dockerfile
	@sed -E -i -e '/^CMD \["gunicorn/s/"-t", "[0-9]+"/"-t", "600"/' Dockerfile
	@sed -E -i -e '/^CMD \["gunicorn/s/"--reload", //' Dockerfile
	@sed -E -i -e '/^ +tty/s/: .*/: false/' \
		-e '/^ +stdin_open/s/: .*/: false/' docker-compose.yml
	@sed -i -e 's/\(client_body_timeout\).*/\1 120;/' \
		-e 's/\(client_header_timeout\).*/\1 120;/' \
		-e 's/\(keepalive_timeout\).*/\1 120;/' \
		-e 's/\(proxy_connect_timeout\).*/\1 120;/' \
		-e 's/\(proxy_read_timeout\).*/\1 120;/' nginx-server.conf

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

down:  ## Turn off running instance
	@docker compose -f docker-compose.yml -f caddy.yml -f nginx.yml -f rsnapshot.yml -f ncdb.yml down --volumes

clean: set-prod unset-caddy  ## Reset config(s) to production (default) state
	@echo "Config reset OK. Cleaning? Try: make prune"

prune:  ## USE WITH CAUTION. Remove every docker container, image and volume. Including those unrelated to parkour!
	@docker system prune -a -f --volumes

prod: set-prod deploy-django deploy-nginx deploy-ready  ## Deploy production instance with Nginx, and rsnapshot service
	@echo "Consider: make deploy-rsnapshot"

dev0: set-dev set-caddy deploy-full load-backup

dev: set-dev deploy-django deploy-nginx deploy-ready load-backup load-migrations  ## Deploy development instance with Nginx, and loaded media & postgres latest SQL dump

set-dev: set-prod unset-caddy
	@sed -i -e '/^DJANGO_SETTINGS_MODULE/s/\(wui\.settings\.\).*/\1dev/' parkour.env
	@sed -i -e '/^RUN .* pip install/s/\(requirements\/\).*\(\.txt\)/\1dev\2/' Dockerfile
	@sed -E -i -e '/^CMD \["gunicorn/s/"-t", "[0-9]+"/"--reload", "-t", "3600"/' Dockerfile
	@sed -E -i -e '/^ +tty/s/: .*/: true/' \
			-e '/^ +stdin_open/s/: .*/: true/' docker-compose.yml
	@sed -i -e 's/\(client_body_timeout\).*/\1 1h;/' \
		-e 's/\(client_header_timeout\).*/\1 1h;/' \
		-e 's/\(keepalive_timeout\).*/\1 1h;/' \
		-e 's/\(proxy_connect_timeout\).*/\1 1h;/' \
		-e 's/\(proxy_read_timeout\).*/\1 1h;/' nginx-server.conf

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

convert-backup:  ## Convert ./rsnapshot/../daily.0/parkour2_pgdb to ./latest.sqldump (will overwrite if there's one already)
	@docker compose -f convert-backup.yml up -d && \
		docker exec -it parkour2-convert-backup pg_dump -Fc postgres -U postgres -f /tmp/postgres_dump && \
        docker cp parkour2-convert-backup:/tmp/postgres_dump latest.sqldump && \
		docker compose -f convert-backup.yml down

load-media:  ## Copy all media files into running instance
	@[[ -d media_dump ]] && \
		find $$PWD/media_dump/ -maxdepth 1 -mindepth 1 -type d | \
			xargs -I _ docker cp _ parkour2-django:/usr/src/app/media/

load-postgres:  ## Restore instant snapshot (latest.sqldump) on running instance
	@[[ -f latest.sqldump ]] && \
		docker cp ./latest.sqldump parkour2-postgres:/tmp/parkour-postgres.dump && \
		docker exec -it parkour2-postgres pg_restore -d postgres -U postgres -1 -c /tmp/parkour-postgres.dump > /dev/null

load-backup: load-media load-postgres

backup: save-media save-postgres

save-media:  ## Copy over all media files (media_dump/)
	@docker cp parkour2-django:/usr/src/app/media/ . && mv media media_dump

save-postgres:  ## Create instant snapshot (latest.sqldump) of running database instance
	@docker exec -it parkour2-postgres pg_dump -Fc postgres -U postgres -f /tmp/postgres_dump && \
		docker cp parkour2-postgres:/tmp/postgres_dump latest.sqldump

deploy-rsnapshot:
	@docker compose -f rsnapshot.yml up -d && \
		sleep 1m && \
		docker exec -it parkour2-rsnapshot rsnapshot daily

test: down clean prod
	@echo "Testing on a 'clean' production deployment..."
	@docker compose run parkour2-django python manage.py validate_templates && \
		docker compose run parkour2-django python -Wa manage.py test

shell:
	@echo "Spawning bpython shell plus (only for dev deployments)..."
	@docker exec -it parkour2-django python manage.py shell_plus --bpython

reload-nginx:
	@docker exec -it parkour2-nginx nginx -s reload

reload-django:
	@find $$PWD/parkour_app/ -maxdepth 1 -type d -mtime -3 | \
		xargs -I _ docker cp _ parkour2-django:/usr/src/app/

graph_models:
	@docker exec -it parkour2-django sh -c \
	"apt update && apt install -y graphviz libgraphviz-dev pkg-config && pip install pygraphviz" && \
		docker exec -it parkour2-django python manage.py graph_models -a -g -o /tmp/parkour.png && \
		docker cp parkour2-django:/tmp/parkour.png models.png

show_urls:
	@docker exec -it parkour2-django python manage.py show_urls

compile:  ## Render parkour_app/requirements/*.in to TXT
	@source ./env/bin/activate && \
		pip-compile-multi -d parkour_app/requirements/ && \
		deactivate

dev-setup: ## Create virtualenv with development tools (e.g. pip compiler)
	@env python3 -m venv env && \
		source ./env/bin/activate && \
		env python3 -m pip install --upgrade pip && \
		pip install \
			pre-commit \
			pip-compile-multi

## TODO: ReadTheDocs (DEPRECATION)> sphinx sphinx-autobuild sphinx-rtd-theme


# Don't confuse 'dev-setup' with the app environment (dev.in & dev.txt) to run
# it in 'dev' mode, mind the 'hierarchical' difference. We're going to use
# pip-compile-multi to manage parkour_app/requirements/*.txt files.


# Last, but not least, please also note that there's pre-commit to keep a tidy
# repo. And, git-lfs (e.g.  `.gitattributes`) to track `parkour_app/static/`.
