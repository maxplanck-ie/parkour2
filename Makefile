.PHONY: *
SHELL := /bin/bash
timestamp := $(shell date +%Y%m%d-%H%M%S)
NcpuThird := $(shell LC_NUMERIC=C echo "scale=0; ($$(nproc --all)*.333)" | bc | xargs printf "%.0f")

deploy: check-rootdir set-prod deploy-django deploy-caddy collect-static load-fixtures  ## Deploy to 127.0.0.1:9980 with initial and required data loaded!

help: check-rootdir
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo "" && echo 'Please note: this is just a list of the most common available routines, for details see the source Makefile.'

check-rootdir:
	@test "$$(basename $$PWD)" == "parkour2" || \
		{ echo 'Makefile, and the corresponding compose YAML files, only work if parent directory is named "parkour2"'; \
		exit 1; }

set-prod:
	@-test -e misc/parkour.env && \
		sed -i -e '/^DJANGO_SETTINGS_MODULE/s/\(wui\.settings\.\).*/\1prod/' misc/parkour.env || \
		echo "Warning: misc/parkour.env file not found."
	@sed -E -i -e '/^#CMD \["gunicorn/s/#CMD/CMD/' Dockerfile
	@sed -i -e '/^RUN .* pip install/s/\(requirements\/\).*\(\.txt\)/\1prod\2/' Dockerfile
	@sed -E -i -e '/^CMD \["python",.*"runserver_plus"/s/CMD/#CMD/' Dockerfile
	@#sed -E -i -e '/^ENV PYTHONDEVMODE/s/1/0/' Dockerfile
	@sed -i -e 's#\(target:\) pk2_playwright#\1 pk2_base#' docker-compose.yml

deploy-django: deploy-network deploy-containers

deploy-network:
	@docker network create parkour2

deploy-containers:
	@docker compose build
	@docker compose up -d

deploy-ready: apply-migrations collect-static
	@docker compose exec parkour2-django find . -maxdepth 1 -mindepth 1 -type d \
		! -name media ! -name staticfiles ! -name logs ! -name htmlcov \
		-exec tar czf media/current_code_snapshot.tar.gz {} \+

collect-static:
	@docker compose exec parkour2-django python manage.py collectstatic --no-input

check-templates:
	@docker compose exec parkour2-django python manage.py validate_templates

update-extjs:
	@which sencha > /dev/null \
		&& cd ./parkour_app/static/main-hub \
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

down-full: down-lite rm-volumes  ## Turn off running instance (removing all volumes)

rm-volumes:
	@VOLUMES=$$(docker volume ls -q | grep "^parkour2_") || :
	@test $${#VOLUMES[@]} -gt 1 && docker volume rm -f $$VOLUMES > /dev/null || :

down-lite: clearpy
	@CONTAINERS=$$(docker ps -a -f status=exited | awk '/^parkour2_parkour2-/ { print $$7 }') || :
	@test $${#CONTAINERS[@]} -gt 1 && docker rm $$CONTAINERS > /dev/null || :
	@docker compose -f docker-compose.yml -f caddy.yml -f nginx.yml -f rsnapshot.yml -f pgadmin.yml down
	@docker volume rm -f parkour2_pgdb > /dev/null
	@docker network rm -f parkour2

down: down-lite  ## Turn off running instance (persisting media & staticfiles' volumes)

clean:
	@sleep 1s
	@$(MAKE) set-prod hardreset-caddyfile > /dev/null

sweep:
	@find ./misc -mtime +1 -name \*.sqldump -exec /bin/rm -rf {} +;

prune:
	@echo "Warning: Removing EVERY docker container, image and volume (even those unrelated to parkour2!)"
	@sleep 10s && docker system prune -a -f --volumes

clearpy:
	@find . -type f -name "*.py[co]" -delete
	@find . -type d -name "__pycache__" -delete

prod: down set-prod deploy-django deploy-nginx collect-static deploy-rsnapshot  ## Deploy Gunicorn instance with Nginx, and rsnapshot service

try-prod: down set-dev deploy-django deploy-caddy collect-static

dev-easy: down set-dev deploy-django deploy-caddy collect-static  ## Deploy Werkzeug instance with Caddy

dev: down set-dev deploy-django deploy-nginx collect-static set-prod  ## Deploy Werkzeug instance with Nginx (incl. TLS)

set-dev:
	@sed -i -e '/^DJANGO_SETTINGS_MODULE/s/\(wui\.settings\.\).*/\1dev/' misc/parkour.env
	@sed -E -i -e '/^#CMD \["python",.*"runserver_plus"/s/#CMD/CMD/' Dockerfile
	@sed -i -e '/^RUN .* pip install/s/\(requirements\/\).*\(\.txt\)/\1dev\2/' Dockerfile
	@sed -E -i -e '/^CMD \["gunicorn/s/CMD/#CMD/' Dockerfile
	@#sed -E -i -e '/^ENV PYTHONDEVMODE/s/0/1/' Dockerfile
	@sed -i -e 's#\(target:\) pk2_playwright#\1 pk2_base#' docker-compose.yml

add-pgadmin-caddy: hardreset-caddyfile
	@echo -e "\nhttp://127.0.0.1:9981 {\n\thandle {\n\t\treverse_proxy parkour2-pgadmin:8080\n\t}\n\tlog\n}" >> misc/Caddyfile

hardreset-caddyfile:
	@echo -e "http://127.0.0.1:9980 {\n\thandle /static/* {\n\t\troot * /parkour2\n\t\tfile_server\n\t}\n\thandle /protected_media/* {\n\t\troot * /parkour2\n\t\tfile_server\n\t}\n\thandle {\n\t\treverse_proxy parkour2-django:8000\n\t}\n\tlog\n}\n" > misc/Caddyfile

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
		docker cp parkour2-convert-backup:/tmp_parkour_dump misc/db_$(timestamp).sqldump
		docker compose -f convert-backup.yml down
	@rm -f misc/latest.sqldump && ln -s db_$(timestamp).sqldump misc/latest.sqldump

load-media:  ## Copy all media files into running instance
	@[[ -d media_dump ]] && \
		find $$PWD/media_dump/ -maxdepth 1 -mindepth 1 -type d | \
			xargs -I {} docker cp {} parkour2-django:/usr/src/app/media/ && \
		echo "Info: Loaded media file(s)." || \
		echo 'ERROR: Folder media_dump not found!'

load-postgres:  ## Restore instant snapshot (sqldump) on running instance
	@[[ -f misc/latest.sqldump ]] && \
		docker cp -L ./misc/latest.sqldump parkour2-postgres:/tmp_parkour-postgres.dump && \
		docker exec parkour2-postgres pg_restore -d postgres -U postgres -c tmp_parkour-postgres.dump > /dev/null && \
		echo "Info: Loaded PostgreSQL database OK." || \
		echo '$ scp root@production:~/parkour2/misc/latest.sqldump .'

load-postgres-plain:
	@test -e ./this.sql && \
		docker cp ./this.sql parkour2-postgres:/tmp_parkour-postgres.dump && \
		docker exec parkour2-postgres sh -c \
			"psql -d postgres -U postgres < tmp_parkour-postgres.dump > /dev/null" || \
		echo "ERROR: ./this.sql not found, do something in the lines of... cd /parkour/data/docker/postgres_dumps/; ln -s this.sql 2022-Aug-04.sql"

db: schema load-postgres  ## Alias to: apply-migrations && load-postgres

load-fixtures:
	@docker compose exec parkour2-django python manage.py load_initial_data

# load-initial-data:
# 	@docker compose exec parkour2-django python manage.py loaddata \
# 		$$(fd -g \*.json | cut -d"/" -f5 | rev | cut -d"." -f2 | rev | tr '\n' ' ')

load-backup: load-postgres load-media

# In our production VM, media_dump is a symlink to another partition (mounted
# as /parkour) with its own set of backup rules set by Core IT. The last
# command (mv) will move subfolders (e.g. request_files) in this partition.
# Also, note that this partition is where rsnapshot is writing every time.
save-media:
	@docker cp parkour2-django:/usr/src/app/media/ . && mv media media_dump

save-postgres:  ## Create instant snapshot (latest.sqldump) of running database instance
	@docker exec parkour2-postgres pg_dump -Fc postgres -U postgres -f tmp_parkour_dump && \
		docker cp parkour2-postgres:/tmp_parkour_dump misc/db_$(timestamp).sqldump
	@rm -f misc/latest.sqldump && ln -s db_$(timestamp).sqldump misc/latest.sqldump

import-media:
	@rsync -rauL -vhP -e "ssh -i ~/.ssh/parkour2" \
		root@parkour:~/parkour2/rsnapshot/backups/halfy.0/localhost/data/parkour2_media/ ./media_dump/

import-pgdb:
	@ssh -i ~/.ssh/parkour2 root@parkour -t "make --directory ~/parkour2 save-postgres"
	@rsync -raul -vhP -e "ssh -i ~/.ssh/parkour2" --include='*.sqldump' \
		--exclude='*.conf' --exclude='*.pem' --exclude='*.yml' \
		--exclude='*.txt' --exclude='*.json' --exclude='*.env' \
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
djtest: down set-prod deploy-django
	@docker compose exec parkour2-django python manage.py test --parallel

set-testing: set-prod
	@sed -i -e '/^DJANGO_SETTINGS_MODULE/s/\(wui\.settings\.\).*/\1testing/' misc/parkour.env
	@sed -i -e '/^RUN .* pip install/s/\(requirements\/\).*\(\.txt\)/\1testing\2/' Dockerfile

set-testing-front: set-testing
	@sed -i -e 's#\(target:\) pk2_base#\1 pk2_playwright#' docker-compose.yml

pytest: down set-testing deploy-django
	@docker compose exec parkour2-django pytest -n auto

create-admin:
	@docker compose exec parkour2-django sh -c \
		"DJANGO_SUPERUSER_PASSWORD=testing.password DJANGO_SUPERUSER_EMAIL=test.user@test.com \
			python manage.py createsuperuser --no-input"

playwright: down set-testing-front deploy-django deploy-caddy collect-static apply-migrations load-fixtures create-admin set-prod
	@docker compose exec parkour2-django pytest -n $(NcpuThird) -c playwright.ini

coverage-xml: down set-testing deploy-django
	@docker compose exec parkour2-django pytest -n auto --cov=./ --cov-config=.coveragerc --cov-report=xml

coverage-html: down set-testing deploy-django
	@docker compose exec parkour2-django coverage erase
	@docker compose exec parkour2-django coverage run -m pytest -n auto --cov=./ --cov-config=.coveragerc --cov-report=html

test: lint-migras check-migras check-templates coverage-html  ## Run all tests, on every level

shell:
	@docker exec -it parkour2-django python manage.py shell_plus --bpython

# list-sessions:
# 	@docker exec -it parkour2-django python manage.py shell --command="from common.models import User; from django.contrib.sessions.models import Session; print([ User.objects.get(id=s.get_decoded().get('_auth_user_id')) for s in Session.objects.iterator() ])"

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

models:  ## Printable A1 PDF posters using smaller A4 or A3 sheets.
	@docker exec parkour2-django sh -c \
	"apt update && apt install -y pdfposter graphviz libgraphviz-dev pkg-config && pip install pydot && \
		python manage.py graph_models -n --pydot -g -a -o /tmp_parkour.dot && \
		sed -i -e 's/\(fontsize\)=[0-9]\+/\1=20/' /tmp_parkour.dot && \
		dot -T pdf -o /tmp_parkour.dot && \
		pdfposter -mA3 -pA1 /tmp_parkour.pdf /tmp_models.A3.pdf && \
		pdfposter -mA4 -pA1 /tmp_parkour.pdf /tmp_models.A4.pdf && \
		pdfposter -mA4 /tmp_parkour.pdf /tmp_models.pdf"
	@docker cp parkour2-django:/tmp_models.A3.pdf models_poster_using_A3.pdf
	@docker cp parkour2-django:/tmp_models.A4.pdf models_poster_using_A4.pdf
	@docker cp parkour2-django:/tmp_models.pdf models_A4_preview.pdf

show_urls:
	@docker exec parkour2-django python manage.py show_urls

compile:
	@test -d ./env || \
		{ echo "ERROR: venv not found! Try: make env-setup-dev"; exit 1; }
	@source ./env/bin/activate && \
		pip-compile-multi -d parkour_app/requirements/ && \
		deactivate

get-pin:
	@docker compose logs parkour2-django | grep PIN | cut -d':' -f2

# Support installation without docker
## https://github.com/maxplanck-ie/parkour2/wiki/Installation-without-docker
#
# install: check-python-version env-setup-app load-env-vars  ## Install without Docker (WIP)
#
## TODO: Doesn't makefile rules run in subshells? needs to be tested.
# load-env-vars:
# 	@test -e misc/parkour.env && \
# 		set +a; source misc/parkour.env; set -a || \
# 		echo "ERROR: misc/parkour.env was not found, you may copy misc/parkour.env.sample"
#
# check-python-version:
# 	@test $(env python3 -V | cut -d. -f2) -gt 8 || echo "Warning: Python version <= 9 is not tested."
# 	@test $(env python3 -V | cut -d. -f2) -lt 11 || echo "Warning: Python version >=12 is not tested."
#
# env-setup-app: 
# 	@env python3 -m venv env_app/ && \
# 		source ./env_app/bin/activate && \
# 		env python3 -m pip install --upgrade pip && \
# 		pip install -r parkour_app/requirements/prod.txt
# 	deactivate
# 	@echo "Info: venv env_app created, source it (together with env-vars) and then use django command runserver. Good luck!"

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

# Remember: (docker compose run == docker exec) != docker run
