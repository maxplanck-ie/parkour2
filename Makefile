.PHONY: *
SHELL := /bin/bash

ifeq ($(OS),Windows_NT)
	NcpuThird := 2
else	
	NcpuThird := $(shell LC_NUMERIC=C echo "scale=0; ($$(nproc --all)*.333)" | bc | xargs printf "%.0f")
endif

stamp := $(shell date +%Y%m%d_%H%M%S)_$(shell git log --oneline -1 | cut -d' ' -f1)

deploy: check-rootdir set-prod deploy-django deploy-caddy collect-static load-fixtures  ## Deploy to localhost:9980 with initial and required data loaded!

help: check-rootdir
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo "" && echo 'Please note: this is just a list of the most common available routines, for details see the source Makefile.'

check-rootdir:
	@test "$$(basename $$PWD)" == "parkour2" || \
		{ echo 'Makefile, and the corresponding compose YAML files, only work if parent directory is named "parkour2"'; \
		exit 1; }

set-prod:
	@sed -i -e 's#\(target:\) pk2_.*#\1 pk2_prod#' docker-compose.yml
	@sed -i -e 's#\(^CMD \["npm", "run", "start-\).*\]#\1prod"\]#' frontend.Dockerfile

deploy-django: deploy-network deploy-containers

deploy-network:
	@docker network create parkour2

deploy-containers:
	@docker compose build
	@docker compose up -d

deploy-ready: apply-migrations collect-static

collect-static:
	@docker compose exec parkour2-django python manage.py collectstatic --no-input

check-templates:
	@docker compose exec parkour2-django python manage.py validate_templates

update-extjs:
	@which sencha > /dev/null \
		&& cd ./backend/static/main-hub \
		&& OPENSSL_CONF=/dev/null sencha app build development \
		|| echo "Warning: Sencha is not installed. See: https://github.com/maxplanck-ie/parkour2/wiki/Sencha-CMD"

apply-migrations:
	@docker compose exec parkour2-django python manage.py migrate --traceback

migrasync:
	@docker compose exec parkour2-django python manage.py migrate --run-syncdb

migrate: apply-migrations

schema: apply-migrations

lint-migras:
	@docker compose exec parkour2-django python manage.py lintmigrations || exit 0

migrations:
	@docker compose exec parkour2-django python manage.py makemigrations

check-migras:
	@docker compose exec parkour2-django python manage.py makemigrations --no-input --check --dry-run

stop:
	@docker compose -f docker-compose.yml -f caddy.yml -f nginx.yml -f rsnapshot.yml -f pgadmin.yml stop

rm-volumes:
	@VOLUMES=$$(docker volume ls -q | grep "^parkour2_") || :
	@test $${#VOLUMES[@]} -gt 1 && docker volume rm -f $$VOLUMES > /dev/null || :

down: clean  ## Turn off running instance (persisting media & staticfiles' volumes)
	@CONTAINERS=$$(docker ps -a -f status=exited | awk '/^parkour2_parkour2-/ { print $$7 }') || :
	@test $${#CONTAINERS[@]} -gt 1 && docker rm $$CONTAINERS > /dev/null || :
	@docker compose -f docker-compose.yml -f caddy.yml -f nginx.yml -f rsnapshot.yml -f pgadmin.yml down
	@docker volume rm -f parkour2_pgdb > /dev/null
	@docker network rm -f parkour2

set-base:
	@sed -i -e 's#\(target:\) pk2_.*#\1 pk2_base#' docker-compose.yml

clean:
	#@docker compose exec parkour2-django rm -f backend/logs/*.log
	@$(MAKE) set-base hardreset-caddyfile > /dev/null
	@test -e ./misc/parkour.env.ignore && git checkout ./misc/parkour.env || :

sweep:  ## Remove any sqldump and migrations tar gzipped older than a week. (Excluding current symlink targets.)
	@find ./misc -ctime +7 -name db_\*.sqldump \
		-not -name "$$(file misc/latest.sqldump | sed 's/.*\(db_.*\.sqldump\).*/\1/')" \
		-exec /bin/rm -rf {} +;
	@find ./misc -ctime +7 -name migras_\*.tar.gz \
		-not -name "$$(file misc/migras.tar.gz | sed 's/.*\(migras_.*\.tar\.gz\).*/\1/')" \
		-exec /bin/rm -rf {} +;

prune:
	@echo "Warning: Removing EVERY docker container, image and volume (even those unrelated to parkour2!)"
	@sleep 10s && docker system prune -a -f --volumes

clearpy:  ## Removes some files, created by 'prod' deployment and owned by root. TODO: we should probably have to check duties/static/dist (buildDir from vite.cfg.js); among other directories like backend/.pytest_cache ... gotta check.
	@docker compose exec parkour2-django find . -type f -name "*.py[co]" -exec /bin/rm -rf {} +;
	@docker compose exec parkour2-django find . -type d -name "__pycache__" -exec /bin/rm -rf {} +;

prod: down clean deploy-django deploy-nginx collect-static deploy-rsnapshot  ## Deploy Gunicorn instance with Nginx, and rsnapshot service

dev-easy: down set-dev deploy-django deploy-caddy collect-static clean  ## Deploy Werkzeug instance with Caddy

dev: down set-dev deploy-django deploy-nginx collect-static clean  ## Deploy Werkzeug instance with Nginx (incl. TLS)

set-dev: hardreset-caddyfile
	@sed -i -e 's#\(target:\) pk2_.*#\1 pk2_dev#' docker-compose.yml
	# @sed -i -e 's#\(^CMD \["npm", "run", "start-\).*\]#\1dev"\]#' frontend.Dockerfile
	@test -e ./misc/parkour.env.ignore && cp ./misc/parkour.env.ignore ./misc/parkour.env || :

add-pgadmin-caddy: hardreset-caddyfile
	@echo -e "\nhttp://*:9981 {\n\thandle {\n\t\treverse_proxy parkour2-pgadmin:8080\n\t}\n\tlog\n}" >> misc/Caddyfile

hardreset-caddyfile:
	@echo -e "http://*:9980 {\n\thandle /static/* {\n\t\troot * /parkour2\n\t\tfile_server\n\t}\n\thandle /protected_media/* {\n\t\troot * /parkour2\n\t\tfile_server\n\t}\n\thandle /vue/* {\n\t\treverse_proxy parkour2-vite:5173\n\t}\n\thandle /vue-assets/* {\n\t\treverse_proxy parkour2-vite:5173\n\t}\n\thandle {\n\t\treverse_proxy parkour2-django:8000\n\t}\n\tlog\n}" > misc/Caddyfile

hardreset-envfile:
	@echo -e "TIME_ZONE=Europe/Berlin\nADMIN_NAME=admin\nADMIN_EMAIL=your@mail.server.tld\nEMAIL_HOST=mail.server.tld\nEMAIL_SUBJECT_PREFIX=[Parkour]\nSERVER_EMAIL=your@mail.server.tld\nCSRF_TRUSTED_ORIGINS=http://127.0.0.1,https://*.server.tld,http://localhost:5174\nPOSTGRES_USER=postgres\nPOSTGRES_DB=postgres\nPOSTGRES_PASSWORD=change_me__stay_safe\nDATABASE_URL=postgres://postgres:change_me__stay_safe@parkour2-postgres:5432/postgres\nSECRET_KEY=generate__one__with__openssl__rand__DASH_hex__32" > misc/parkour.env

deploy-caddy:
	@docker compose -f caddy.yml up -d

deploy-nginx:
	@test -e ./misc/key.pem && test -e ./misc/cert.pem || \
		{ echo "ERROR: TLS certificates not found!"; exit 1; }
	@docker compose -f nginx.yml up -d

deploy-pgadmin:
	@docker compose -f pgadmin.yml up -d
	@CONTAINERS=$$(docker ps -a -f status=running | awk '/^parkour2-/ { print $$1}') || :
	@[[ $${CONTAINERS[*]} =~ nginx ]] && $(MAKE) add-pgadmin-nginx || :
	@[[ $${CONTAINERS[*]} =~ caddy ]] && $(MAKE) add-pgadmin-caddy || :

add-pgadmin-nginx:
	@docker cp misc/nginx-pgadmin.conf parkour2-nginx:/etc/nginx/conf.d/
	@docker exec parkour2-nginx nginx -s reload

convert-backup:  ## Convert xxxly.0's pgdb to ./misc/*.sqldump (updating symlink too)
	@docker compose -f convert-backup.yml up -d && sleep 1m && \
		echo "Warning: If this fails, most probably pg was still starting... retry manually!" && \
		docker exec parkour2-convert-backup sh -c \
			"pg_dump -Fc postgres -U postgres -f tmp_parkour_dump" && \
		docker cp parkour2-convert-backup:/tmp_parkour_dump misc/db_$(stamp).sqldump
		docker compose -f convert-backup.yml down
	@ln -sf db_$(stamp).sqldump misc/latest.sqldump

load-media:  ## Copy all media files into running instance
	@[[ -d media_dump ]] && \
		find $$PWD/media_dump/ -maxdepth 1 -mindepth 1 -type d | \
			xargs -I {} docker cp {} parkour2-django:/usr/src/app/media/ && \
		echo "Info: Loaded media file(s)." || \
		echo 'ERROR: Folder media_dump not found!'

load-postgres:  ## Restore instant snapshot (sqldump) on running instance
	@[[ -f misc/latest.sqldump ]] && \
		docker cp -L ./misc/latest.sqldump parkour2-postgres:/tmp_parkour-postgres.dump
	@docker exec parkour2-postgres sh -c "pg_restore --data-only --disable-triggers \
		--dbname=postgres --username=postgres tmp_parkour-postgres.dump \
		1> /tmp/pg_log_out.txt 2> /tmp/pg_log_err.txt" || \
			docker exec parkour2-postgres cat /tmp/pg_log_err.txt

load-postgres-plain:
	@test -e ./this.sql && \
		docker cp ./this.sql parkour2-postgres:/tmp_parkour-postgres.dump && \
		docker exec parkour2-postgres sh -c \
			"psql -d postgres -U postgres < tmp_parkour-postgres.dump > /dev/null" || \
		echo "ERROR: ./this.sql not found, do something in the lines of... cd /parkour/data/docker/postgres_dumps/; ln -s this.sql 2022-Aug-04.sql"

pg-analyze:
	@docker exec -it parkour2-postgres psql -d postgres -U postgres -c 'ANALYZE VERBOSE'  > pg-analyze.txt.ignore

db: schema load-postgres  ## Alias to: apply-migrations && load-postgres

load-fixtures: apply-migrations
	@docker compose exec parkour2-django python manage.py load_initial_data

load-backup: load-postgres load-media

save-media:
	@rm -rf media_dump && docker cp parkour2-django:/usr/src/app/media/ . && mv media media_dump

save-postgres:  ## Create instant snapshot (latest.sqldump) of running database instance
	@docker exec parkour2-postgres pg_dump -Fc postgres -U postgres -f tmp_parkour_dump && \
		docker cp parkour2-postgres:/tmp_parkour_dump misc/db_$(stamp).sqldump
	@ln -sf db_$(stamp).sqldump misc/latest.sqldump

import-media:
	@ssh -i ~/.ssh/parkour2 root@parkour -t "make --directory ~/parkour2 save-media"
	@rsync -rauL -vhP -e "ssh -i ~/.ssh/parkour2" root@parkour:~/parkour2/media_dump .

import-pgdb:
	@ssh -i ~/.ssh/parkour2 root@parkour -t "make --directory ~/parkour2 save-postgres"
	@rsync -raul -vhP -e "ssh -i ~/.ssh/parkour2" \
		--include='migras*.tar.gz' --include='*.sqldump' --exclude='*' \
		root@parkour:~/parkour2/misc/ misc/

# git-release:
# 	@echo '# Release'
# 	@echo gh pr create --fill -B main
# 	@echo git checkout main
# 	@echo git pull
# 	@echo git tag -a "0.4.0" -m "Small bug fixes, overall performance improvement and better stability."
# 	@echo git push --tags
# 	@echo git checkout develop
# 	@echo gh release create --generate-notes

deploy-rsnapshot:
	@docker compose -f rsnapshot.yml up -d && \
		sleep 1m && \
		docker exec parkour2-rsnapshot rsnapshot halfy

# --buffer --reverse --failfast --timing
djtest: down set-testing deploy-django clean  ## Re-deploy and run Backend tests
	@docker compose exec parkour2-django python manage.py test --parallel

set-testing:
	@sed -i -e 's#\(target:\) pk2_.*#\1 pk2_testing#' docker-compose.yml

set-playwright:
	@sed -i -e 's#\(target:\) pk2_.*#\1 pk2_playwright#' docker-compose.yml

# pytest: down set-testing deploy-django
# 	@docker compose exec parkour2-django pytest -n auto

playwright: down set-playwright deploy-django deploy-caddy collect-static load-fixtures e2e  ## Re-deploy and run Frontend tests

playwright-migras: down set-playwright deploy-django deploy-caddy collect-static load-fixtures-migras e2e

e2e:
	@docker compose exec parkour2-django pytest -n $(NcpuThird) -c playwright.ini

create-admin:
	@docker compose exec parkour2-django sh -c \
		"DJANGO_SUPERUSER_PASSWORD=testing.password DJANGO_SUPERUSER_EMAIL=test.user@test.com \
			python manage.py createsuperuser --no-input"

coverage-xml: down set-testing deploy-django
	@docker compose exec parkour2-django pytest -n auto --cov=./ --cov-config=.coveragerc --cov-report=xml

coverage-html: down set-testing deploy-django
	@docker compose exec parkour2-django coverage erase
	@docker compose exec parkour2-django coverage run -m pytest -n auto --cov=./ --cov-config=.coveragerc --cov-report=html

test: playwright lint-migras check-migras check-templates coverage-html  ## Run all tests, on every level

shell:
	@docker exec -it parkour2-django python manage.py shell_plus --ipython

# list-sessions:
# 	@docker exec -it parkour2-django python manage.py shell --command="from common.models import User; from django.contrib.sessions.models import Session; print([ User.objects.get(id=s.get_decoded().get('_auth_user_id')) for s in Session.objects.iterator() ])"
## https://django-user-sessions.readthedocs.io/en/stable/
# kill-sessions:
# 	@docker exec -it parkour2-django python manage.py shell --command="from common.models import User; from django.contrib.sessions.models import Session; for s in Session.objects.iterator(): s.delete()"

reload-code:  ## Gracefully ship small code updates into production backend
	@docker compose exec -it parkour2-django kill -1 1

## This should be a cronjob on your host VM/ production deployment machine.
clearsessions:
	@docker exec -it parkour2-django python manage.py clearsessions

dbshell:  ## Open PostgreSQL shell
	@docker exec -it parkour2-postgres psql -U postgres -p 5432

reload-nginx:
	@docker exec parkour2-nginx nginx -s reload

models:
	@docker exec parkour2-django sh -c "apt update && \
		apt install -y pdfposter graphviz libgraphviz-dev pkg-config && \
		pip install pydot && \
		python manage.py graph_models -n --pydot -g -a -o /tmp_parkour.dot && \
		sed -i -e 's/\(fontsize\)=[0-9]\+/\1=20/' /tmp_parkour.dot && \
		dot -T pdf -o /tmp_parkour.dot"
	@docker exec parkour2-django sh -c \
		"pdfposter -mA3 -pA1 /tmp_parkour.pdf /tmp_models.A3.pdf && \
		pdfposter -mA4 -pA1 /tmp_parkour.pdf /tmp_models.A4.pdf && \
		pdfposter -mA4 /tmp_parkour.pdf /tmp_models.pdf"
	@docker cp parkour2-django:/tmp_models.A3.pdf models_poster_using_A3.pdf
	@docker cp parkour2-django:/tmp_models.A4.pdf models_poster_using_A4.pdf
	@docker cp parkour2-django:/tmp_models.pdf models_A4_preview.pdf

show-urls:
	@docker exec parkour2-django python manage.py show_urls

maintenance: compile precomitupd ncu

precomitupd:
	@pre-commit autoupdate

compile:
	# @test -d ./env_dev || \
	# 	{ echo "ERROR: venv not found! Try: make env-setup-dev"; exit 1; }
	# @if [[ :$PATH: == *:"env_dev":* ]] ; then
	# 	source ./env_dev/bin/activate && echo "venv activated!"
	# 	pip install --upgrade pip wheel setuptools pip-compile-multi
	# else
	# 	exit 1
	# fi
	@pip-compile-multi --allow-unsafe -d backend/requirements/

ncu:
	# @npm install -g npm-check-updates
	@cd frontend && ncu -u

get-pin:
	@docker compose logs parkour2-django | grep PIN | cut -d':' -f2 | uniq

env-setup-dev:
	@env python3 -m venv env_dev && \
		source ./env_dev/bin/activate && \
		env python3 -m pip install --upgrade pip && \
		pip install \
			pre-commit \
			pip-tools \
			pip-compile-multi
	deactivate

open-pr:
	@git pull && git push && git pull origin develop
	@gh pr create --title "quick upgrade" --fill -B develop
	@echo "Info: Pull Request OPENED"

# merge-pr:
# 	@CURRENT_BRANCH=$$(git rev-parse --abbrev-ref HEAD) \
# 	&& git pull origin main \
# 	&& git checkout main \
# 	&& git merge $$CURRENT_BRANCH \
# 	&& git push -u origin main \
# 	&& echo "-- Pull Request MERGED" \
# 	&& git checkout $$CURRENT_BRANCH

## DO NOT USE WITH PRODUCTION DATA, BarcodeCounter bug is still in place!
# check later: https://docs.djangoproject.com/en/3.2/ref/django-admin/#fixtures-compression
save-db-json:
	@docker exec parkour2-django sh -c 'python manage.py dumpdata --exclude contenttypes --exclude auth.permission --exclude sessions | tail -1 > /tmp/postgres_dump' && \
		docker cp parkour2-django:/tmp/postgres_dump misc/db_$(stamp)-dump.json
	@ln -sf db_$(stamp)-dump.json misc/demo-dump.json

load-db-json:
	@docker cp misc/demo-dump.json parkour2-django:/tmp/postgres_dump.json && \
		docker exec parkour2-django python manage.py loaddata /tmp/postgres_dump.json

reload-json-dev: down prep4json dev migrasync load-db-json restore-prep4json

reload-json-ez: down prep4json dev-easy migrasync load-db-json restore-prep4json

prep4json:
	@rm -f backend/library_preparation/apps.py
	@rm -f backend/library_preparation/signals.py
	@rm -f backend/pooling/apps.py
	@rm -f backend/pooling/signals.py

restore-prep4json:
	@git restore -W backend/library_preparation/apps.py
	@git restore -W backend/library_preparation/signals.py
	@git restore -W backend/pooling/apps.py
	@git restore -W backend/pooling/signals.py

# reload-json-prod: down prep4json dev migrasync load-db-json restore-prep4json-prod

# restore-prep4json-prod:
# 	@scp -i ~/.ssh/parkour2 ~/parkour2/backend/library_preparation/apps.py ${VM_PROD}:~/parkour2/backend/library_preparation/
# 	@scp -i ~/.ssh/parkour2 ~/parkour2/backend/library_preparation/signals.py ${VM_PROD}:~/parkour2/backend/library_preparation/
# 	@scp -i ~/.ssh/parkour2 ~/parkour2/backend/pooling/apps.py ${VM_PROD}:~/parkour2/backend/pooling/
# 	@scp -i ~/.ssh/parkour2 ~/parkour2/backend/pooling/signals.py ${VM_PROD}:~/parkour2/backend/pooling/

rm-migras:
	@rm -rf backend/**/migrations/*

tar-old-migras:
	@find ./backend/*/ -path '**/migrations' \
			-exec tar czf ./misc/migras_$(stamp).tar.gz {} \+ && \
		ln -sf migras_$(stamp).tar.gz misc/migras.tar.gz

put-old-migras:
	@[[ -f misc/migras.tar.gz ]] && \
		$(MAKE) rm-migras && \
		tar xzf misc/migras.tar.gz || \
		ls -l misc/migras.tar.gz

dev-migras: dev db-migras
dev-ez: dev-easy db-migras

db-migras: put-old-migras db put-new-migras  ## Useful after 'git checkout <tag> && tar-old-migras && git switch -'

put-new-migras:
	@git restore -W backend/**/migrations/
	@$(MAKE) migrate

load-fixtures-migras: put-old-migras apply-migrations
	@docker compose exec parkour2-django python manage.py load_initial_data
	@$(MAKE) put-new-migras

# Remember: (docker compose run == docker exec) != docker run
