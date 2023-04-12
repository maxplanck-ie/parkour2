.PHONY: *
SHELL := /bin/bash

deploy: check-rootdir set-prod deploy-full  ## Deploy Gunicorn instance to 127.0.0.1:9980 (see: Caddyfile)

help: check-rootdir
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo "" && echo 'Please note: this is just a list of the most common available routines, for details see the source Makefile.'

check-rootdir:
	@test "$$(basename $$PWD)" == "parkour2" || \
		{ echo 'Makefile, and the corresponding compose YAML files, only work if parent directory is named "parkour2"'; \
		exit 1; }

deploy-full:  deploy-django deploy-caddy

set-prod:
	@sed -i -e '/^DJANGO_SETTINGS_MODULE/s/\(wui\.settings\.\).*/\1prod/' misc/parkour.env
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
		-e 's/\(proxy_read_timeout\).*/\1 120;/' misc/nginx-server.conf

deploy-django: deploy-network deploy-containers

deploy-network:
	@docker network create parkour2_default

deploy-containers:
	@docker compose build -q
	@docker compose up -d

deploy-ready: apply-migrations collect-static
	@docker compose exec parkour2-django find . -maxdepth 1 -mindepth 1 -type d \
		! -name media ! -name staticfiles ! -name logs ! -name htmlcov \
		-exec tar czf media/current_code_snapshot.tar.gz {} \+

collect-static:
	@docker compose exec parkour2-django python manage.py collectstatic --no-input

apply-migrations:
	@docker compose exec parkour2-django python manage.py migrate --traceback

migrasync:
	@docker compose exec parkour2-django python manage.py migrate --run-syncdb

migrate: apply-migrations

migrations:
	@docker compose exec parkour2-django python manage.py makemigrations

# TODO: add conditional 'if containers are running'; else: handle...
check-migras:
	@docker compose exec parkour2-django python manage.py makemigrations --no-input --check --dry-run

stop:
	@docker compose -f docker-compose.yml -f caddy.yml -f nginx.yml -f rsnapshot.yml -f ncdb.yml -f pgadmin.yml stop

down-full: down-lite rm-volumes  ## Turn off running instance (removing all volumes)

rm-volumes:
	@VOLUMES=$$(docker volume ls -q | grep "^parkour2_") || :
	@test $${#VOLUMES[@]} -gt 1 && docker volume rm -f $$VOLUMES > /dev/null || :

down-lite: clearpy
	@CONTAINERS=$$(docker ps -a -f status=exited | awk '/^parkour2_parkour2-/ { print $$7 }') || :
	@test $${#CONTAINERS[@]} -gt 1 && docker rm $$CONTAINERS > /dev/null || :
	@docker compose -f docker-compose.yml -f caddy.yml -f nginx.yml -f rsnapshot.yml -f ncdb.yml -f pgadmin.yml down
	@docker volume rm -f parkour2_pgdb > /dev/null

down: down-lite  ## Turn off running instance (persisting media & staticfiles' volumes)

clean: set-prod unset-caddy  ## Reset config(s) to production (default) state
	@git status
	@echo "Config reset OK. You may also be interested into: make prune sweep"

sweep:  ## Remove any sqldump snapshot in ./misc/ that is older than a day
	@find ./misc -mtime +1 -name \*.sqldump -exec /bin/rm -rf {} +;

prune:
	@echo "Removing EVERY docker container, image and volume (even those unrelated to parkour2!)"
	@sleep 10s && docker system prune -a -f --volumes

clearpy:
	@find . -type f -name "*.py[co]" -delete
	@find . -type d -name "__pycache__" -delete

prod: set-prod deploy-django deploy-nginx deploy-rsnapshot  ## Deploy Gunicorn instance with Nginx, and rsnapshot service

dev-easy: set-dev set-caddy deploy-full  ## Deploy Werkzeug instance (see: caddyfile.in.use)

dev: set-dev deploy-django deploy-nginx  ## Deploy Werkzeug instance with Nginx (incl. TLS)

set-dev: set-prod unset-caddy
	@sed -i -e '/^DJANGO_SETTINGS_MODULE/s/\(wui\.settings\.\).*/\1dev/' misc/parkour.env
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
		-e 's/\(proxy_read_timeout\).*/\1 1h;/' misc/nginx-server.conf

set-caddy:
	@sed -i -e "/\:\/etc\/caddy\/Caddyfile$$/s/\.\/.*\:/\.\/misc\/caddyfile\.in\.use\:/" caddy.yml

unset-caddy:
	@sed -i -e 's/pgadmin/nocodb/' misc/caddyfile.in.use
	@sed -i -e "/\:\/etc\/caddy\/Caddyfile$$/s/\.\/.*\:/\.\/misc\/Caddyfile\:/" caddy.yml

deploy-caddy:
	@docker compose -f caddy.yml up -d

deploy-nginx:
	@docker compose -f nginx.yml up -d

deploy-ncdb:
	@docker compose -f ncdb.yml up -d
	@CONTAINERS=$$(docker ps -a -f status=running | awk '/^parkour2-/ { print $$1}') || :
	@[[ $${CONTAINERS[*]} =~ nginx ]] && $(MAKE) add-ncdb-nginx || :
	@[[ $${CONTAINERS[*]} =~ caddy ]] && sed -i -e 's/pgadmin/nocodb/' misc/caddyfile.in.use || :

add-ncdb-nginx: check-nginx-conf
	@docker cp misc/nginx-ncdb.conf parkour2-nginx:/etc/nginx/conf.d/
	@docker exec parkour2-nginx nginx -s reload

deploy-pgadmin:
	@docker compose -f pgadmin.yml up -d
	@CONTAINERS=$$(docker ps -a -f status=running | awk '/^parkour2-/ { print $$1}') || :
	@[[ $${CONTAINERS[*]} =~ nginx ]] && $(MAKE) add-pgadmin-nginx || :
	@[[ $${CONTAINERS[*]} =~ caddy ]] && sed -i -e 's/nocodb/pgadmin/' misc/caddyfile.in.use || :

add-pgadmin-nginx: check-nginx-conf
	@docker cp misc/nginx-pgadmin.conf parkour2-nginx:/etc/nginx/conf.d/
	@docker exec parkour2-nginx nginx -s reload

check-nginx-conf:
	@test "$$(docker exec parkour2-nginx ls /etc/nginx/conf.d/ | wc -l)" -eq 1 || \
		{ echo 'There is already an extra NGINX config in place! Keep in mind that both NocoDB and pgAdmin default to the same subdomain, so this requires your quick manual intervention.'; \
		exit 1; }

convert-backup:  ## Convert daily.0's pgdb to ./misc/latest.sqldump (overwriting if there's one already)
	@docker compose -f convert-backup.yml up -d && sleep 1m && \
		echo "If this fails, most probably pg was still starting... retry manually!" && \
		docker exec parkour2-convert-backup sh -c \
			"pg_dump -Fc postgres -U postgres -f /tmp/postgres_dump" && \
		docker cp parkour2-convert-backup:/tmp/postgres_dump misc/latest.sqldump && \
		docker compose -f convert-backup.yml down

load-media:  ## Copy all media files into running instance
	@[[ -d media_dump ]] && \
		find $$PWD/media_dump/ -maxdepth 1 -mindepth 1 -type d | \
			xargs -I {} docker cp {} parkour2-django:/usr/src/app/media/ && \
		echo "Loaded media file(s)." || \
		echo 'Folder media_dump not found!'

load-postgres:  ## Restore instant snapshot (sqldump) on running instance
	@[[ -f misc/latest.sqldump ]] && \
		docker cp -L ./misc/latest.sqldump parkour2-postgres:/tmp/parkour-postgres.dump && \
		docker exec parkour2-postgres pg_restore -d postgres -U postgres -1 -c /tmp/parkour-postgres.dump > /dev/null && \
		echo "Loaded PostgreSQL database OK." || \
		echo '$ scp root@production:~/parkour2/misc/latest.sqldump .'

load-postgres-plain:
	@echo "cd /parkour/data/docker/postgres_dumps/; ln -s this.sql 2022-Aug-04.sql"
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

save-media:
	@docker cp parkour2-django:/usr/src/app/media/ . && mv media media_dump

timestamp := $(shell date +%Y%m%d-%H%M%S)
save-postgres:  ## Create instant snapshot (latest.sqldump) of running database instance
	@docker exec parkour2-postgres pg_dump -Fc postgres -U postgres -f /tmp/postgres_dump && \
		docker cp parkour2-postgres:/tmp/postgres_dump misc/db_$(timestamp).sqldump
	@rm -f misc/latest.sqldump && ln -s db_$(timestamp).sqldump misc/latest.sqldump

# check later: https://docs.djangoproject.com/en/3.2/ref/django-admin/#fixtures-compression
save-db-json:
	@docker exec parkour2-django sh -c 'python manage.py dumpdata --exclude contenttypes --exclude auth.permission --exclude sessions | tail -1 > /tmp/postgres_dump' && \
		docker cp parkour2-django:/tmp/postgres_dump misc/db_$(timestamp)-dump.json
	@rm -f misc/latest-dump.json && ln -s db_$(timestamp)-dump.json misc/latest-dump.json

load-db-json:
	@docker cp misc/latest-dump.json parkour2-django:/tmp/postgres_dump.json && \
		docker exec parkour2-django python manage.py loaddata /tmp/postgres_dump.json

reload-json-dev: down prep4json dev migrasync load-db-json restore-prep4json

reload-json-ez: down prep4json dev-easy migrasync load-db-json restore-prep4json

prep4json:
	@rm -f parkour_app/library_preparation/apps.py
	@rm -f parkour_app/library_preparation/signals.py
	@rm -f parkour_app/pooling/apps.py
	@rm -f parkour_app/pooling/signals.py

restore-prep4json:
	@git restore -W parkour_app/library_preparation/apps.py
	@git restore -W parkour_app/library_preparation/signals.py
	@git restore -W parkour_app/pooling/apps.py
	@git restore -W parkour_app/pooling/signals.py

reload-json-prod: down prep4json dev migrasync load-db-json restore-prep4json-prod

restore-prep4json-prod:
	@scp -i ~/.ssh/parkour2 ~/parkour2/parkour_app/library_preparation/apps.py ${VM_PROD}:~/parkour2/parkour_app/library_preparation/
	@scp -i ~/.ssh/parkour2 ~/parkour2/parkour_app/library_preparation/signals.py ${VM_PROD}:~/parkour2/parkour_app/library_preparation/
	@scp -i ~/.ssh/parkour2 ~/parkour2/parkour_app/pooling/apps.py ${VM_PROD}:~/parkour2/parkour_app/pooling/
	@scp -i ~/.ssh/parkour2 ~/parkour2/parkour_app/pooling/signals.py ${VM_PROD}:~/parkour2/parkour_app/pooling/

VM_PROD := root@parkour
# ssh-keygen -t rsa -b 4096 -f ~/.ssh/parkour2 -C "your@email.tld"
# ssh-copy-id -i ~/.ssh/parkour2.pub root@parkour

import-media:
	@rsync -rauL -vhP -e "ssh -i ~/.ssh/parkour2" \
		${VM_PROD}:~/parkour2/rsnapshot/backups/halfy.0/localhost/data/parkour2_media/ ./media_dump/

import-pgdb: sweep  ## Run save-postgres on $VM_PROD, and bring all their sqldumps. Note: first we sweep local sqldumps!
	@ssh -i ~/.ssh/parkour2 ${VM_PROD} -t "make --directory ~/parkour2 save-postgres"
	@rsync -rauL -vhP -e "ssh -i ~/.ssh/parkour2" --exclude='*' --include='*.sqldump' \
		${VM_PROD}:~/parkour2/misc misc/

full-import-json:
	@ssh -i ~/.ssh/parkour2 ${VM_PROD} -t "make --directory ~/parkour2 save-db-json"
	@scp -i ~/.ssh/parkour2 ${VM_PROD}:~/parkour2/misc/latest-dump.json misc/

upgrade:
	@echo '# TODO:'
	@echo '# - BarcodeCounter has a bug! keeps being reset whenever we load json dump. Adjust manually?'
	@echo '# - lastest{sqldump,json} should be symlinks to dated filenames, update save-{} rules'
	@echo '# - Disable down rule, or prepend- a save-postgres + rename snapshots with date'
	@echo '# - Wrap these into a script.'
	@echo '# - ~~Add maintenance mode?~~'
	@echo '# Prepare'
	@echo make compile full-import-json reload-json save-postgres
	@echo make migrations
	@echo make down dev migrate load-postgres
	@echo ssh -i ~/.ssh/parkour2 ${VM_PROD} -t "rm -rf ~/pk2_old"
	@echo '# Backup'
	@echo ssh -i ~/.ssh/parkour2 ${VM_PROD} -t "docker ps > ~/last.txt && git --git-dir=~/parkour2/.git --work-tree=~/parkour2 log | head -1 >> ~/last.txt"
	@echo ssh -i ~/.ssh/parkour2 ${VM_PROD} -t "docker exec parkour2-rsnapshot rsnapshot halfy"
	@echo ssh -i ~/.ssh/parkour2 ${VM_PROD} -t "make --directory ~/parkour2 save-postgres"
	@echo ssh -i ~/.ssh/parkour2 ${VM_PROD} -t "docker system prune -a"
	@echo ssh -i ~/.ssh/parkour2 ${VM_PROD} -t "docker-compose -f docker-compose.yml -f nginx.yml -f rsnapshot.yml stop"
	@echo ssh -i ~/.ssh/parkour2 ${VM_PROD} -t "make --directory ~/parkour2 clean"
	@echo ssh -i ~/.ssh/parkour2 ${VM_PROD} -t "mv ~/parkour2 ~/pk2_old"
	@echo '# Deployment'
	@echo '## Prepare static'
	@echo ssh -i ~/.ssh/parkour2 ${VM_PROD} -t "mkdir -p ~/parkour2/parkour_app/static/main-hub/"
	@echo ssh -i ~/.ssh/parkour2 ${VM_PROD} -t "cp -ruva ~/pk2_old/parkour_app/static/main-hub/app ~/parkour2/parkour_app/static/main-hub/"
	@echo '## Ship code (asks for password, TODO)'
	@echo rsync -rauL -vhP --delete \
		--exclude={'.git','env','*.env','*.pem','rsnapshot/backups','frontend','media_dump'} \
		~/parkour2 ${VM_PROD}:~/
	@echo '## Corrections'
	@echo ssh -i ~/.ssh/parkour2 ${VM_PROD} -t "sed -i \'s/docker compose/docker-compose/g\' ~/parkour2/Makefile"
	@echo ssh -i ~/.ssh/parkour2 ${VM_PROD} -t "sed -i \'/^RUN/s/RUN --mount=.* pip/RUN pip/\' ~/parkour2/Dockerfile"
	@echo '## Symlinks'
	@echo ssh -i ~/.ssh/parkour2 ${VM_PROD} -t "ln -s /parkour/backups ~/parkour2/rsnapshot/backups"
	@echo ssh -i ~/.ssh/parkour2 ${VM_PROD} -t "ln -s /parkour/backups/halfy.0/localhost/data/parkour2_media ~/parkour2/media_dump"
	@echo ssh -i ~/.ssh/parkour2 ${VM_PROD} -t "ln -s ~/parkour2/parkour_app/static/main-hub/app ~/parkour2/frontend"
	@echo '## Configuration'
	@echo ssh -i ~/.ssh/parkour2 ${VM_PROD} -t '"echo -n y | cp ~/pk2_old/misc/parkour.env ~/parkour2/misc/"'
	@echo ssh -i ~/.ssh/parkour2 ${VM_PROD} -t '"echo -n y | cp /root/pk2_old/misc/cert.pem ~/parkour2/misc/"'
	@echo ssh -i ~/.ssh/parkour2 ${VM_PROD} -t '"echo -n y | cp /root/pk2_old/misc/key.pem ~/parkour2/misc/"'
	@echo '## Get JSON dump and start the service...'
	@echo ssh -i ~/.ssh/parkour2 ${VM_PROD} -t "cp ~/pk2_old/misc/latest-dump.json ~/parkour2/misc/"
	#echo ssh -i ~/.ssh/parkour2 ${VM_PROD} -t "git init && git add ."  # Otherwise restore-prep4json wouldn't work. FIXME (replace git with scp from pk-test?) DONE (pero cambiarlo para q sea from pk-prod)
	@echo ssh -i ~/.ssh/parkour2 ${VM_PROD} -t "make --directory ~/parkour2 clearpy prep4json prod migrasync load-db-json"
	@echo 'SKIP: Here would go the option to do the legacy procedure, moving SQLdump... (TODO), something in the lines of: make clearpy prod migrate load-postgres'
	@echo make restore-prep4json-prod
	@echo ssh -i ~/.ssh/parkour2 ${VM_PROD} -t "make --directory ~/parkour2 collect-static deploy-rsnapshot"
	@echo '## Manual login OK? Proceeding...'
	@echo ssh -i ~/.ssh/parkour2 ${VM_PROD} -t "docker exec parkour2-rsnapshot rsnapshot halfy"
	@echo ssh -i ~/.ssh/parkour2 ${VM_PROD} -t "docker exec parkour2-django python manage.py check"
	@echo "make git-release  # Further instructions to follow if everything went alright..."

git-release:
	@echo '# Release'
	@echo gh pr create --fill -B main
	@echo git checkout main
	@echo git pull
	@echo git tag -a "0.4.0" -m "Small bug fixes, overall performance improvement and better stability."
	@echo git push --tags
	@echo git checkout develop
	@echo gh release create --generate-notes

deploy-rsnapshot:
	@docker compose -f rsnapshot.yml up -d && \
		sleep 1m && \
		docker exec parkour2-rsnapshot rsnapshot halfy

test: down-full clean set-prod deploy-django
	@docker compose run parkour2-django python manage.py validate_templates && \
		docker compose run parkour2-django python -Wa manage.py test --buffer --reverse --failfast --timing

shell:
	@docker exec -it parkour2-django python manage.py shell_plus --bpython

# TODO: https://django-user-sessions.readthedocs.io
# + set a timeout (only for non-staff users)
list-sessions:
	@docker exec -it parkour2-django python manage.py shell --command="from common.models import User; from django.contrib.sessions.models import Session; print([ User.objects.get(id=s.get_decoded().get('_auth_user_id')) for s in Session.objects.iterator() ])"

kill-sessions:
	@docker exec -it parkour2-django python manage.py shell --command="from common.models import User; from django.contrib.sessions.models import Session; for s in Session.objects.iterator(): s.delete()"

## This should be a cronjob on your host VM/ production deployment machine.
clearsessions:
	@docker exec -it parkour2-django python manage.py clearsessions

dbshell:  ## Open PostgreSQL shell
	@docker exec -it parkour2-postgres psql -U postgres -p 5432

reload-nginx:
	@docker exec parkour2-nginx nginx -s reload

graph_models:
	@docker exec parkour2-django sh -c \
	"apt update && apt install -y graphviz libgraphviz-dev pkg-config && pip install pygraphviz" && \
		docker exec parkour2-django python manage.py graph_models -a -g -o /tmp/parkour.png && \
		docker cp parkour2-django:/tmp/parkour.png models.png

show_urls:
	@docker exec parkour2-django python manage.py show_urls

compile:
	@test -d ./env && \
		source ./env/bin/activate && \
		pip-compile-multi -d parkour_app/requirements/ && \
		deactivate || echo "venv not found! Try: make env-setup-dev"

env-setup-dev:
	@env python3 -m venv env && \
		source ./env/bin/activate && \
		env python3 -m pip install --upgrade pip && \
		pip install \
			pre-commit \
			pip-compile-multi && \
		pip install -r parkour_app/requirements/dev.txt && \
	deactivate

# Remember: (docker compose run == docker exec) != docker run
