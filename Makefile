
deploy:
	docker network create parkour2_default
	docker compose build
	docker compose up -d
	docker compose -f caddy.yml up -d
	docker compose run parkour2-django python manage.py makemigrations
	docker compose run parkour2-django python manage.py migrate
	docker compose run parkour2-django python manage.py collectstatic --noinput


loadBackup:
	docker cp ./latest.dump.sql parkour2-postgres:/tmp/parkour-postgres.dump
	docker exec -it parkour2-postgres pg_restore -d postgres -U postgres -c -1 /tmp/parkour-postgres.dump


clean:
	docker compose -f docker-compose.yml -f caddy.yml down
	docker volume rm parkour2_caddy_config parkour2_caddy_data parkour2_pgdb parkour2_media parkour2_staticfiles 
