.PHONY: *
SHELL := /bin/bash

ifeq ($(OS),Windows_NT)
	NcpuThird := 2
else	
	NcpuThird := $(shell LC_NUMERIC=C echo "scale=0; ($$(nproc --all)*.333)" | bc | xargs printf "%.0f")
endif

stamp := $(shell date +%Y%m%d_%H%M%S)_$(shell git log --oneline -1 | cut -d' ' -f1)

deploy: check-rootdir set-prod deploy-webapp deploy-caddy collect-static load-fixtures  ## Deploy to localhost:9980 with initial and required data loaded!

help: check-rootdir
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo "" && echo 'Please note: this is just a list of the most common available routines, for details see the source Makefile.'

check-deploy-matrix:
	@set -euo pipefail; \
	echo "[1/6] Checking Makefile wiring..."; \
	grep -q '^set-prod: .*hardreset-caddyfile-prod.*hardreset-nginx-server-prod' Makefile || { echo 'FAIL: set-prod must depend on caddy+nginx prod hardreset targets'; exit 1; }; \
	grep -q '^set-dev: .*hardreset-caddyfile-dev.*hardreset-nginx-server-dev' Makefile || { echo 'FAIL: set-dev must depend on caddy+nginx dev hardreset targets'; exit 1; }; \
	grep -q '^set-playwright: hardreset-caddyfile-prod$$' Makefile || { echo 'FAIL: set-playwright must depend on hardreset-caddyfile-prod'; exit 1; }; \
	echo "[2/6] Checking frontend command defaults..."; \
	grep -q '^CMD \["npm", "run", "start-prod"\]$$' frontend.Dockerfile || { echo 'FAIL: frontend.Dockerfile default CMD must be start-prod'; exit 1; }; \
	echo "[3/6] Validating prod caddy profile..."; \
	$(MAKE) --no-print-directory hardreset-caddyfile-prod > /dev/null; \
	grep -q 'reverse_proxy parkour2-vite:5173' misc/Caddyfile || { echo 'FAIL: prod caddy profile must proxy frontend to :5173'; exit 1; }; \
	echo "[4/6] Validating dev caddy profile..."; \
	$(MAKE) --no-print-directory hardreset-caddyfile-dev > /dev/null; \
	grep -q 'reverse_proxy parkour2-vite:5174' misc/Caddyfile || { echo 'FAIL: dev caddy profile must proxy frontend to :5174'; exit 1; }; \
	grep -q '/@vite/\*' misc/Caddyfile || { echo 'FAIL: dev caddy profile must include vite internal routes'; exit 1; }; \
	echo "[5/6] Restoring default caddy profile..."; \
	$(MAKE) --no-print-directory hardreset-caddyfile-prod > /dev/null; \
	echo "[6/6] Checking compose parse..."; \
	docker compose config > /tmp/parkour2_compose_config.out; \
	echo 'PASS: deploy matrix wiring looks consistent.'

check-rootdir: check-deploy-matrix
	@test "$$(basename $$PWD)" == "parkour2" || \
		{ echo 'Makefile, and the corresponding compose YAML files, only work if parent directory is named "parkour2"'; \
		exit 1; }

set-prod: hardreset-caddyfile-prod hardreset-nginx-server-prod
	@sed -i -e 's#\(target:\) pk2_.*#\1 pk2_base#' docker-compose.yml
	@sed -i -e 's#\(^CMD \["npm", "run", "start-\).*\]#\1prod"\]#' frontend.Dockerfile
	@test -e ./misc/parkour.env.ignore && cp ./misc/parkour.env.ignore ./misc/parkour.env || :

deploy-webapp:
	@docker compose build
	@docker compose --project-name=parkour2 up -d
	@git checkout docker-compose.yml

deploy-ready: apply-migrations collect-static

collect-static:
	@docker compose exec parkour2-django python manage.py collectstatic --no-input

check-templates:
	@docker compose exec parkour2-django python manage.py validate_templates

update-extjs:  ## See: https://github.com/maxplanck-ie/parkour2/wiki/Sencha-CMD
	@cd ./backend/static/main-hub \
		&& OPENSSL_CONF=/dev/null sencha app build development

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
	@#find backend/ -user root -path '**/migrations/*.py' -print0 | xargs -0 -n 1 -I {_} echo docker compose exec parkour2-django chown 1000:1000 {_}  ## adjust `uid` and `gid`, and run this manually to fix permissions from within container.

check-migras:
	@docker compose exec parkour2-django python manage.py makemigrations --no-input --check --dry-run

stop:
	@docker compose -f docker-compose.yml -f misc/caddy.yml -f misc/nginx.yml -f misc/rsnapshot.yml stop

rm-volumes:
	@VOLUMES=$$(docker volume ls -q | grep "^parkour2_") || :
	@test $${#VOLUMES[@]} -gt 1 && docker volume rm -f $$VOLUMES > /dev/null || :

down: clean  ## Turn off running instance (persisting media & staticfiles' volumes)
	@CONTAINERS=$$(docker ps -a -f status=exited | awk '/^parkour2_parkour2-/ { print $$7 }') || :
	@test $${#CONTAINERS[@]} -gt 1 && docker rm $$CONTAINERS > /dev/null || :
	@docker compose -f docker-compose.yml -f misc/caddy.yml -f misc/nginx.yml -f misc/rsnapshot.yml down
	@docker volume rm -f parkour2_pgdb > /dev/null
	@docker network rm -f parkour2

set-base:
	@sed -i -e 's#\(target:\) pk2_.*#\1 pk2_base#' docker-compose.yml

clean:
	@#docker compose exec parkour2-django rm -f backend/logs/*.log
	@$(MAKE) set-base hardreset-caddyfile-prod hardreset-nginx-server-prod hardreset-frontend-dockerfile disable-explorer > /dev/null
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

clearpy:  ## Removes some files, created by 'prod' deployment and owned by root. 
	@docker compose exec parkour2-django find . -type f -name "*.py[co]" -exec /bin/rm -rf {} +;
	@docker compose exec parkour2-django find . -type d -name "__pycache__" -exec /bin/rm -rf {} +;
	@#docker compose exec parkour2-vite find . -type d -name "dist" -exec /bin/rm -rf {} +;

prod: down set-prod check-prod-tls deploy-webapp deploy-nginx collect-static deploy-rsnapshot clean  ## Deploy Gunicorn instance with Nginx, and rsnapshot service

check-prod-tls:
	@test -e ./misc/cert.pem || { echo "ERROR: Missing TLS certificate: ./misc/cert.pem (required for 'make prod')."; exit 1; }
	@test -e ./misc/key.pem || { echo "ERROR: Missing TLS private key: ./misc/key.pem (required for 'make prod')."; exit 1; }

prod-ci: down set-prod deploy-webapp collect-static apply-migrations clean
	@docker exec parkour2-django python manage.py check

dev-easy: down set-dev deploy-webapp deploy-caddy collect-static clean  ## Deploy Werkzeug instance with Caddy

dev: down set-dev deploy-webapp deploy-nginx collect-static clean  ## Deploy Werkzeug instance with Nginx (incl. TLS)

set-dev: hardreset-caddyfile-dev hardreset-nginx-server-dev
	@sed -i -e 's#\(target:\) pk2_.*#\1 pk2_dev#' docker-compose.yml
	@sed -i -e 's#\(^CMD \["npm", "run", "start-\).*\]#\1dev"\]#' frontend.Dockerfile
	@test -e ./misc/parkour.env.ignore && cp ./misc/parkour.env.ignore ./misc/parkour.env || :

hardreset-caddyfile: hardreset-caddyfile-prod

hardreset-nginx-server-prod:
	@sed -i -e 's#\(server parkour2-vite:\).*#\15173;#' misc/nginx-server.conf

hardreset-nginx-server-dev:
	@sed -i -e 's#\(server parkour2-vite:\).*#\15174;#' misc/nginx-server.conf

hardreset-frontend-dockerfile:
	@sed -i -e 's#\(^CMD \["npm", "run", "start-\).*\]#\1prod"\]#' frontend.Dockerfile

hardreset-caddyfile-prod:
	@echo -e "http://*:9980 {\n\thandle /static/* {\n\t\troot * /parkour2\n\t\tfile_server\n\t}\n\thandle /protected_media/* {\n\t\troot * /parkour2\n\t\tfile_server\n\t}\n\thandle /vue/vue-assets/* {\n\t\turi strip_prefix /vue\n\t\treverse_proxy parkour2-vite:5173\n\t}\n\thandle /vue/* {\n\t\treverse_proxy parkour2-vite:5173\n\t}\n\thandle /vue-assets/* {\n\t\treverse_proxy parkour2-vite:5173\n\t}\n\thandle {\n\t\treverse_proxy parkour2-django:8000\n\t}\n\tlog\n}" > misc/Caddyfile

hardreset-caddyfile-dev:
	@echo -e "http://*:9980 {\n\thandle /static/* {\n\t\troot * /parkour2\n\t\tfile_server\n\t}\n\thandle /protected_media/* {\n\t\troot * /parkour2\n\t\tfile_server\n\t}\n\thandle /vue/vue-assets/* {\n\t\turi strip_prefix /vue\n\t\treverse_proxy parkour2-vite:5174 {\n\t\t\theader_up Host parkour2-vite:5174\n\t\t}\n\t}\n\t@vite_dev {\n\t\tpath /vue/* /vue-assets/* /@vite/* /src/* /node_modules/* /@id/* /@fs/* /__vite_ping\n\t}\n\thandle @vite_dev {\n\t\treverse_proxy parkour2-vite:5174 {\n\t\t\theader_up Host parkour2-vite:5174\n\t\t}\n\t}\n\thandle {\n\t\treverse_proxy parkour2-django:8000\n\t}\n\tlog\n}" > misc/Caddyfile

hardreset-envfile:
	@echo -e "TIME_ZONE=Europe/Berlin\nADMIN_NAME=admin\nADMIN_EMAIL=your@mail.server.tld\nEMAIL_HOST=mail.server.tld\nEMAIL_SUBJECT_PREFIX=[Parkour2]\nSERVER_EMAIL=errors@mail.server.tld\nCSRF_TRUSTED_ORIGINS=http://127.0.0.1,https://*.server.tld,http://localhost:5174\nPOSTGRES_DB=postgres\nPOSTGRES_USER=postgres\nPOSTGRES_PASSWORD=change_me__stay_safe\nDATABASE_URL=postgres://postgres:change_me__stay_safe@parkour2-postgres:5432/postgres\nREADONLY_USER=ropg\nREADONLY_PASSWORD=change_me__stay_safe2\nREADONLY_DATABASE_URL=postgres://ropg:change_me__stay_safe2@parkour2-postgres:5432/postgres\nOPENROUTER_API_KEY=aaaaaaaaaaaaaaaaa\nSECRET_KEY=generate__one__with__openssl__rand__DASH_hex__32" > misc/parkour.env

deploy-caddy:
	@docker compose -f misc/caddy.yml --project-name=parkour2 up -d

deploy-nginx:
	@test -e ./misc/key.pem && test -e ./misc/cert.pem || \
		{ echo "ERROR: TLS certificates not found!"; exit 1; }
	@docker compose -f misc/nginx.yml --project-name=parkour2 up -d

convert-backup:  ## Convert xxxly.0's pgdb to ./misc/*.sqldump (updating symlink too)
	@docker compose -f misc/convert-backup.yml --project-name=parkour2 up -d && sleep 1m && \
		echo "Warning: If this fails, most probably pg was still starting... retry manually!" && \
		docker exec parkour2-convert-backup sh -c \
			"pg_dump -Fc postgres -U postgres -f tmp_parkour_dump" && \
		docker cp parkour2-convert-backup:/tmp_parkour_dump misc/db_$(stamp).sqldump
		docker compose -f misc/convert-backup.yml down
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
	@$(MAKE) clean

load-postgres-plain:
	@test -e ./this.sql && \
		docker cp ./this.sql parkour2-postgres:/tmp_parkour-postgres.dump && \
		docker exec parkour2-postgres sh -c \
			"psql -d postgres -U postgres < tmp_parkour-postgres.dump > /dev/null" || \
		echo "ERROR: ./this.sql not found, do something in the lines of... cd /parkour/data/docker/postgres_dumps/; ln -s this.sql 2022-Aug-04.sql"

get-schema:  ## Get schema of running instance (for prompting LLMs)
	@cat misc/get_schema.sql | \
		docker exec -i parkour2-postgres sh -c 'psql -d postgres -U postgres'

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
	@docker compose -f misc/rsnapshot.yml --project-name=parkour2 up -d && \
		sleep 1m && \
		docker exec parkour2-rsnapshot rsnapshot halfy

# --buffer --reverse --failfast --timing
djtest:  ## Run Backend tests (reuse running container when available)
	@if docker compose ps --status running --services | grep -q '^parkour2-django$$'; then \
		echo "Info: Reusing running parkour2-django container for tests."; \
		docker compose exec parkour2-django python manage.py test --parallel; \
	else \
		echo "Info: parkour2-django is not running, redeploying test stack first."; \
		$(MAKE) down set-testing deploy-webapp clean; \
		docker compose exec parkour2-django python manage.py test --parallel; \
	fi

set-testing:
	@sed -i -e 's#\(target:\) pk2_.*#\1 pk2_testing#' docker-compose.yml

set-playwright: hardreset-caddyfile-prod
	@sed -i -e 's#\(target:\) pk2_.*#\1 pk2_playwright#' docker-compose.yml
	@sed -i -e 's#\(^CMD \["npm", "run", "start-\).*\]#\1prod"\]#' frontend.Dockerfile

# pytest: down set-testing deploy-webapp
# 	@docker compose exec parkour2-django pytest -n auto

playwright:  ## Run Frontend tests (reuse running container when available)
	@if docker compose ps --status running --services | grep -q '^parkour2-django$$'; then \
		if docker compose exec parkour2-django sh -lc 'command -v pytest > /dev/null && pytest --help | grep -q -- --browser && find /root/.cache/ms-playwright -path "*/firefox/firefox" -type f 2>/dev/null | grep -q .'; then \
			echo "Info: Reusing running parkour2-django container for Playwright tests."; \
			$(MAKE) load-fixtures; \
			$(MAKE) e2e; \
		else \
			echo "Info: Testing runtime not ready in running container, installing testing requirements."; \
			if docker compose exec parkour2-django sh -lc 'PY_VERSION=$$(python -c "import sys; print(f\"{sys.version_info.major}.{sys.version_info.minor}\")"); uv pip install -r requirements/$${PY_VERSION}/testing.txt && playwright install --with-deps firefox' \
				&& docker compose exec parkour2-django sh -lc 'command -v pytest > /dev/null && pytest --help | grep -q -- --browser && find /root/.cache/ms-playwright -path "*/firefox/firefox" -type f 2>/dev/null | grep -q .'; then \
				echo "Info: Testing dependencies installed, running Playwright tests."; \
				$(MAKE) load-fixtures; \
				$(MAKE) e2e; \
			else \
				echo "Info: Could not prepare running container for Playwright tests, redeploying stack first."; \
				$(MAKE) down set-playwright deploy-webapp deploy-caddy collect-static load-fixtures; \
				$(MAKE) e2e; \
			fi; \
		fi; \
	else \
		echo "Info: parkour2-django is not running, redeploying Playwright stack first."; \
		$(MAKE) down set-playwright deploy-webapp deploy-caddy collect-static load-fixtures; \
		$(MAKE) e2e; \
	fi

playwright-migras: down set-playwright deploy-webapp deploy-caddy collect-static load-fixtures-migras e2e

e2e:
	@docker compose exec parkour2-django pytest -n $(NcpuThird) -c playwright.ini

create-admin:
	@docker compose exec parkour2-django sh -c \
		"DJANGO_SUPERUSER_PASSWORD=testing.password DJANGO_SUPERUSER_EMAIL=test.user@test.com \
			python manage.py createsuperuser --no-input"

coverage-xml: down set-testing deploy-webapp
	@docker compose exec parkour2-django pytest -n auto --cov=./ --cov-config=.coveragerc --cov-report=xml

coverage-html: down set-testing deploy-webapp
	@docker compose exec parkour2-django coverage erase
	@docker compose exec parkour2-django coverage run -m pytest -n auto --cov=./ --cov-config=.coveragerc --cov-report=html

test: playwright lint-migras check-migras check-templates coverage-html  ## Run all tests, on every level

shell:
	@docker exec -it parkour2-django python manage.py shell_plus --ipython

reload-code:  ## Gracefully ship small code updates into production Backend
	@docker compose exec -it parkour2-django kill -1 1

reload-ux:  ## Gracefully ship small code updates into production Frontend
	@if docker compose ps --status running --services | grep -q '^parkour2-vite$$'; then \
		docker compose exec parkour2-vite sh -lc "npm run build"; \
	else \
		echo "Info: parkour2-vite was not running, restarting container instead."; \
		docker compose restart parkour2-vite; \
	fi

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
		uv pip install --system pydot && \
		python manage.py graph_models -n --pydot -g -a -o /tmp_parkour.dot && \
		sed -i -e 's/\(fontsize\)=[0-9]\+/\1=20/' /tmp_parkour.dot && \
		dot -T pdf -o /tmp_parkour.pdf /tmp_parkour.dot"
	@docker exec parkour2-django sh -c \
		"pdfposter -mA3 -pA1 /tmp_parkour.pdf /tmp_models.A3.pdf && \
		pdfposter -mA4 -pA1 /tmp_parkour.pdf /tmp_models.A4.pdf && \
		pdfposter -mA4 /tmp_parkour.pdf /tmp_models.pdf"
	@docker cp parkour2-django:/tmp_models.A3.pdf models_poster_using_A3.pdf
	@docker cp parkour2-django:/tmp_models.A4.pdf models_poster_using_A4.pdf
	@docker cp parkour2-django:/tmp_models.pdf models_A4_preview.pdf

show-urls:
	@docker exec parkour2-django python manage.py show_urls

maintenance: compile ncu
	@uv tool upgrade pre-commit
	@pre-commit autoupdate

compile:
	@PY_VERSIONS=$$(awk '/python-version:/ { \
		match($$0, /\[(.*)\]/, a); \
		split(a[1], versions, ","); \
		for (i in versions) { \
			gsub(/^[ '\'']+|[ '\'']+$$/, "", versions[i]); \
			print versions[i]; \
		} \
	}' .github/workflows/django.yml); \
	for version in $$PY_VERSIONS; do \
		this=backend/requirements/$$version; \
		mkdir -p $$this; \
		uv pip compile --upgrade --quiet --no-progress --universal --python-version $$version \
			backend/requirements/base.in -o $$this/base.txt; \
		uv pip compile --upgrade --quiet --no-progress --universal --python-version $$version \
			backend/requirements/dev.in -c $$this/base.txt -o $$this/dev.txt; \
		uv pip compile --upgrade --quiet --no-progress --universal --python-version $$version \
			backend/requirements/testing.in -c $$this/dev.txt -o $$this/testing.txt; \
	done

ncu:
	# TODO: upgrade ncu first?
	@cd frontend && ncu \!ag-grid-* -u

get-pin:
	@docker compose logs parkour2-django | grep PIN | cut -d':' -f2 | uniq

env-setup-dev:
	@echo "First, install uv: https://docs.astral.sh/uv/getting-started/installation/"
	@echo "$ uv python install 3.12"
	@echo "$ echo ruff black djlint | xargs -n1 uv tool install --python 3.12"
	@echo "$ uv tool install --python 3.12 pre-commit --with pre-commit-uv"
	## We're skipping this for now, since it's covered by the CI anyway.
	#@echo "Second, install npm: https://docs.npmjs.com/downloading-and-installing-node-js-and-npm"
	#@echo "$ npm install -g npm-check-updates"

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
		{ echo -n 'Symlink seems to be broken, '; ls -L misc/migras.tar.gz; exit 1; }

dev-migras: dev db-migras
dev-ez: dev-easy db-migras

db-migras: put-old-migras db put-new-migras  ## Useful after 'git checkout <tag> && tar-old-migras && git switch -'

put-new-migras:
	@git checkout -- backend/**/migrations/
	@$(MAKE) migrate

load-fixtures-migras: put-old-migras apply-migrations
	@docker compose exec parkour2-django python manage.py load_initial_data
	@$(MAKE) put-new-migras

update-fixtures: dev-easy load-fixtures-migras  ## Redeploy (local) with fixtures, migrate fields, save data to json.
	@docker compose exec parkour2-django python manage.py save_initial_data

enable-ollama:
	@docker run -d -v ./misc/ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama
	@echo "Work In Progress: this feature was not finalized, open an issue (or PR :D) if you need it."

enable-explorer:
	@docker exec parkour2-django python manage.py create_readonly_pg
	@sed -i -e \
		's%# \(path("explorer/", include("explorer.urls")),\)%\1%' \
		backend/wui/urls.py
	@sed -i -e \
		's%# \("explorer",\)%\1%' \
		backend/wui/settings/dev.py
	@$(MAKE) schema collect-static
	@docker exec parkour2-django python manage.py create_sample_queries

disable-ollama:
	@docker container stop ollama
	@docker container prune -f

disable-explorer:
	@sed -i -e \
		's%^\(\s*\)\(path("explorer/", include("explorer.urls")),\)%\1# \2%' \
		backend/wui/urls.py
	@sed -i -e \
		's%^\(\s*\)\("explorer",\)%\1# \2%' \
		backend/wui/settings/dev.py

# aider:
# 	@export OPENROUTER_API_KEY=$$(grep OPENROUTER_API_KEY misc/parkour.env.ignore | cut -d'=' -f2)
# 	@cd backend/ && aider --subtree-only --model openrouter/google/gemma-2-9b-it:free

deploy2dev:
	@git diff > test.patch && scp test.patch root@parkour-dev:~
	@ssh root@parkour-dev "cd parkour2 && \
		/root/anaconda/bin/git restore . && \
		/root/anaconda/bin/git apply ~/test.patch"

# Remember: (docker compose run == docker exec) != docker run
