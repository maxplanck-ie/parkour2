.PHONY: *
SHELL := /bin/bash

deploy: check-rootdir set-prod deploy-full  ## Deploy Gunicorn instance to 127.0.0.1:9980 (see: Caddyfile)

help: check-rootdir
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST) | sort
	@echo "" && echo 'Please note: this is just a list of the most common available routines, for details see the source Makefile.'

check-rootdir:
	@test "$$(basename $$PWD)" == "parkour2" || \
		{ echo 'Makefile, and the corresponding compose YAML files, only work if parent directory is named "parkour2"'; \
		exit 1; }

deploy-full:  deploy-django deploy-caddy collect-static apply-migrations

set-prod:
	@sed -i -e '/^DJANGO_SETTINGS_MODULE/s/\(wui\.settings\.\).*/\1prod/' parkour.env
	@sed -E -i -e '/^#CMD \["gunicorn/s/#CMD/CMD/' Dockerfile
	@sed -i -e '/^RUN .* pip install/s/\(requirements\/\).*\(\.txt\)/\1prod\2/' Dockerfile
	@sed -E -i -e '/^CMD \["gunicorn/s/"-t", "[0-9]+"/"-t", "600"/' Dockerfile
	@sed -E -i -e '/^CMD \["gunicorn/s/"--reload", //' Dockerfile
	@sed -E -i -e '/^CMD \["python",.*"runserver_plus"/s/CMD/#CMD/' Dockerfile
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

deploy-ready: apply-migrations collect-static
	@docker compose exec parkour2-django find . -maxdepth 1 -mindepth 1 -type d \
		! -name media ! -name staticfiles ! -name logs ! -name htmlcov \
		-exec tar czf media/current_code_snapshot.tar.gz {} \+

collect-static:
	@docker compose exec parkour2-django python manage.py collectstatic --no-input

apply-migrations:
	@docker compose exec parkour2-django python manage.py migrate

migrations:
	@docker compose exec parkour2-django python manage.py makemigrations

get-migrations:
	@docker compose exec parkour2-django python manage.py makemigrations --check && \
		docker compose exec parkour2-django python manage.py migrate \
			--fake-initial --check --traceback --verbosity 2
	@docker exec parkour2-django sh -c \
		"apt update && apt install -y rsync && \
		mkdir -p /usr/src/app/staticfiles/migrations && \
		find **/migrations/ -maxdepth 1 -mindepth 1 -type f | \
		xargs -I {} rsync -qaR {} /usr/src/app/staticfiles/migrations/"
	@echo "Following command (using staticfiles volume) is dependant on default docker settings..."
	cp -rv /var/lib/docker/volumes/parkour2_staticfiles/_data/migrations/* parkour_app/
	@rm -rf /var/lib/docker/volumes/parkour2_staticfiles/_data/migrations
	@docker compose exec parkour2-django python manage.py check
	@docker compose exec parkour2-django python manage.py showmigrations -l

stop:
	@docker compose -f docker-compose.yml -f caddy.yml -f nginx.yml -f rsnapshot.yml -f ncdb.yml stop

down-full: down-lite rm-volumes  ## Turn off running instance (removing all volumes)

rm-volumes:
	@VOLUMES=$$(docker volume ls -q | grep "^parkour2_") || :
	@test $${#VOLUMES[@]} -gt 1 && docker volume rm -f $$VOLUMES > /dev/null || :

down-lite:
	@CONTAINERS=$$(docker ps -a -f status=exited | awk '/^parkour2_parkour2-/ { print $$7}') || :
	@test $${#CONTAINERS[@]} -gt 1 && docker rm $$CONTAINERS > /dev/null || :
	@docker compose -f docker-compose.yml -f caddy.yml -f nginx.yml -f rsnapshot.yml -f ncdb.yml down
	@docker volume rm -f parkour2_pgdb > /dev/null

down: down-lite  ## Turn off running instance (persisting media & staticfiles volumes)

clean: set-prod unset-caddy  ## Reset config(s) to production (default) state
	@git status
	@echo "Config reset OK. Do we need to clean docker? Try: make prune"

prune:  ## Remove EVERY docker container, image and volume (even those unrelated to parkour)
	@docker system prune -a -f --volumes

clearpy:
	@find . -type f -name "*.py[co]" -delete
	@find . -type d -name "__pycache__" -delete

prod: set-prod deploy-django deploy-nginx deploy-ready  ## Deploy production instance with Nginx, and rsnapshot service
	@echo "Consider: make deploy-rsnapshot"

dev-easy: set-dev set-caddy deploy-full  ## Deploy Werkzeug instance (see: caddyfile.in.use)
	@echo "WARNING: latest.sqldump not loaded..."
	@echo "optional: $ make deploy-ncdb"

dev: set-dev deploy-django deploy-nginx deploy-ready  ## Deploy Werkzeug instance with Nginx (incl. TLS)
	@echo "WARNING: latest.sqldump not loaded..."
	@echo "optional: $ make deploy-ncdb add-ncdb-nginx"

dev0: set-dev deploy-django deploy-nginx deploy-ready load-backup

set-dev: set-prod unset-caddy
	@sed -i -e '/^DJANGO_SETTINGS_MODULE/s/\(wui\.settings\.\).*/\1dev/' parkour.env
	@sed -E -i -e '/^#CMD \["python",.*"runserver_plus"/s/#CMD/CMD/' Dockerfile
	@sed -i -e '/^RUN .* pip install/s/\(requirements\/\).*\(\.txt\)/\1dev\2/' Dockerfile
	@sed -E -i -e '/^CMD \["gunicorn/s/"-t", "[0-9]+"/"--reload", "-t", "3600"/' Dockerfile
	@sed -E -i -e '/^CMD \["gunicorn/s/CMD/#CMD/' Dockerfile
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
	@echo 'Using Caddyfile (Dev-easy)? Ok. Using Nginx? run add-ncdb-nginx rule.'

add-ncdb-nginx:
	@docker cp nginx-ncdb.conf parkour2-nginx:/etc/nginx/conf.d/
	@docker exec parkour2-nginx nginx -s reload

convert-backup:  ## Convert daily.0's pgdb to ./latest.sqldump (overwriting if there's one already)
	@docker compose -f convert-backup.yml up -d && sleep 1m && \
		echo "If this fails, most probably pg was still starting... retry manually!" && \
		docker exec parkour2-convert-backup sh -c \
			"pg_dump -Fc postgres -U postgres -f /tmp/postgres_dump" && \
		docker cp parkour2-convert-backup:/tmp/postgres_dump latest.sqldump && \
		docker compose -f convert-backup.yml down

load-media:  ## Copy all media files into running instance
	@[[ -d media_dump ]] && \
		find $$PWD/media_dump/ -maxdepth 1 -mindepth 1 -type d | \
			xargs -I {} docker cp {} parkour2-django:/usr/src/app/media/

load-postgres:  ## Restore instant snapshot (latest.sqldump) on running instance
	@[[ -f latest.sqldump ]] && \
		docker cp ./latest.sqldump parkour2-postgres:/tmp/parkour-postgres.dump && \
		docker exec parkour2-postgres pg_restore -d postgres -U postgres -1 -c /tmp/parkour-postgres.dump > /dev/null

load-postgres-plain:
	@#cd /parkour/data/docker/postgres_dumps/; ln -s this.sql 2022-Aug-04.sql
	@docker cp ./this.sql parkour2-postgres:/tmp/parkour-postgres.dump && \
		docker exec parkour2-postgres sh -c "psql -d postgres -U postgres < /tmp/parkour-postgres.dump > /dev/null"

load-fixtures:
	@#fd -g \*.json | cut -d"/" -f5 | rev | cut -d"." -f2 | rev | tr '\n' ' '
	@docker compose exec parkour2-django python manage.py loaddata \
		cost_units organizations principal_investigators sequencers pool_sizes fixed_costs \
		library_preparation_costs sequencing_costs concentration_methods index_pairs index_types \
		index_types_data indices_i5 indices_i7 library_protocols library_types organisms read_lengths \
		nucleic_acid_types

load-backup: load-postgres load-media
	@echo "Loaded media file(s) & PostgreSQL database OK."

backup: save-media save-postgres

save-media:  ## Copy over all media files (media_dump/)
	@docker cp parkour2-django:/usr/src/app/media/ . && mv media media_dump

save-postgres:  ## Create instant snapshot (latest.sqldump) of running database instance
	@docker exec parkour2-postgres pg_dump -Fc postgres -U postgres -f /tmp/postgres_dump && \
		docker cp parkour2-postgres:/tmp/postgres_dump latest.sqldump

save-postgres-json:
	@docker exec parkour2-django sh -c 'python manage.py dumpdata | tail -1 > /tmp/postgres_dump' && \
		docker cp parkour2-django:/tmp/postgres_dump latest-dump.json

load-postgres-json:
	@docker cp latest-dump.json parkour2-django:/tmp/postgres_dump.json && \
		docker exec parkour2-django python manage.py loaddata /tmp/postgres_dump.json

deploy-rsnapshot:
	@docker compose -f rsnapshot.yml up -d && \
		sleep 1m && \
		docker exec parkour2-rsnapshot rsnapshot daily

test: down-full clean prod
	@echo "Testing on a 'clean' production deployment..."
	@docker compose run parkour2-django python manage.py validate_templates && \
		docker compose run parkour2-django python -Wa manage.py test --buffer --reverse --pdb --failfast --timing

shell:
	@echo "Spawning bpython shell plus (only for dev deployments)..."
	@docker exec -it parkour2-django python manage.py shell_plus --bpython

dbshell:  ## Open PostgreSQL shell
	@docker exec -it parkour2-postgres psql -U postgres -p 5432

reload-nginx:
	@docker exec parkour2-nginx nginx -s reload

#reload-django:  ## If only docker-rsync existed... Alas, even docker-cp lacks "-u"
#	@find parkour_app/ -mtime 1 -type f | \
#		xargs -I {} docker rsync -qaR {} parkour2-django:/usr/src/app/
## Alternatives? Maybe https://github.com/emacs-pe/docker-tramp.el

reload: down dev load-backup clean  ## "Have you tried turning it off and on again?"
	@clear && docker ps

graph_models:
	@docker exec parkour2-django sh -c \
	"apt update && apt install -y graphviz libgraphviz-dev pkg-config && pip install pygraphviz" && \
		docker exec parkour2-django python manage.py graph_models -a -g -o /tmp/parkour.png && \
		docker cp parkour2-django:/tmp/parkour.png models.png

show_urls:
	@docker exec parkour2-django python manage.py show_urls

compile:  ## Render parkour_app/requirements/*.in to TXT
	@source ./env/bin/activate && \
		pip-compile-multi -d parkour_app/requirements/ && \
		deactivate

env-setup-dev: ## Create virtualenv with development tools (e.g. pip compiler)
	@env python3 -m venv env && \
		source ./env/bin/activate && \
		env python3 -m pip install --upgrade pip && \
		pip install \
			pre-commit \
			pip-compile-multi && \
	deactivate


# Don't confuse 'env-setup-dev' with the app environment (dev.in & dev.txt) to
# run it in 'dev' mode, mind the 'hierarchical' difference. We're going to use
# pip-compile-multi to manage parkour_app/requirements/*.txt files. And, please
# also note that there's pre-commit to keep a tidy repo.

# Remember: (docker compose run == docker exec) != docker run
