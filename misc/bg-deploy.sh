#!/usr/bin/env bash
## Blue/green deploys of the Parkour2 backend (misc/bluegreen.yml). Wiki: Blue-Green-Deployment.
##
##   bg-deploy.sh deploy [VERSION] [--yes] [--compatible] [--breaking]
##   bg-deploy.sh rollback
##   bg-deploy.sh status
##   bg-deploy.sh active        # print the live django container name
##   bg-deploy.sh ensure-conf   # create misc/active/backend.conf (legacy upstream) if missing
##
## misc/active/backend.conf is what nginx includes, hence the single source of truth for which
## container is live. Sessions live in Postgres and SECRET_KEY is shared (parkour.env), so a
## flip does not log anybody out.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

ACTIVE_DIR=misc/active
CONF=$ACTIVE_DIR/backend.conf
NGINX=parkour2-nginx
RSNAPSHOT=parkour2-rsnapshot
LEGACY=parkour2-django         # the pre-blue/green container (docker-compose.yml)
PREFIX=parkour2-django-         # + blue|green
SMOKE_REQUESTS=20
DRAIN_MAX=190                   # s; nginx worker_shutdown_timeout is 180s
COMPOSE=(docker compose -f misc/bluegreen.yml --project-name=parkour2-bg)

log() { echo "[bg] $*"; }
die() { echo "[bg] ERROR: $*" >&2; exit 1; }

write_conf() { # container color dest
	cat >"$3" <<EOF
upstream backend {
	server $1:8000;
}
map \$host \$pk2_color {
	default $2;
}
EOF
}

ensure_conf() {
	mkdir -p "$ACTIVE_DIR"
	[[ -f $CONF ]] || { write_conf "$LEGACY" legacy "$CONF"; log "created $CONF -> $LEGACY"; }
}

active_container() {
	[[ -f $CONF ]] || { echo "$LEGACY"; return; }
	sed -n 's/^[[:space:]]*server[[:space:]]\{1,\}\([^:[:space:]]\{1,\}\):8000;.*/\1/p' "$CONF" | head -n1
}

color_of() { [[ $1 == "$LEGACY" ]] && echo legacy || echo "${1#"$PREFIX"}"; }

idle_of() {
	case $(color_of "$1") in
		blue) echo "${PREFIX}green" ;;
		*) echo "${PREFIX}blue" ;;   # green, or legacy
	esac
}

exists() { docker inspect "$1" >/dev/null 2>&1; }
running() { [[ $(docker inspect -f '{{.State.Running}}' "$1" 2>/dev/null || true) == true ]]; }

wait_healthy() {
	local c=$1 i
	for ((i = 0; i < 60; i++)); do
		running "$c" || die "$c is not running; see: docker logs $c"
		[[ $(docker inspect -f '{{.State.Health.Status}}' "$c") == healthy ]] && return 0
		sleep 5
	done
	die "$c not healthy after 5 min; see: docker logs $c"
}

smoke_direct() { # container: GET /login/ straight on gunicorn
	docker exec -i "$1" python - <<'PY'
import sys, urllib.request
sys.exit(0 if urllib.request.urlopen("http://127.0.0.1:8000/login/", timeout=30).status == 200 else 1)
PY
}

verify_via_nginx() { # color
	local want=$1 i out status got
	for ((i = 1; i <= SMOKE_REQUESTS; i++)); do
		out=$(curl -sk -o /dev/null -D - --max-time 20 https://127.0.0.1/login/ | tr -d '\r' || true)
		status=$(awk 'NR==1{print $2}' <<<"$out")
		got=$(awk -F': ' 'tolower($1)=="x-pk2-color"{print $2}' <<<"$out")
		if [[ $status != 200 || $got != "$want" ]]; then
			log "request $i via nginx: HTTP '${status:-none}', color '${got:-none}' (wanted 200, '$want')"
			return 1
		fi
	done
}

restore_conf() {
	mv -f "$CONF.prev" "$CONF"
	docker exec "$NGINX" nginx -t && docker exec "$NGINX" nginx -s reload
}

flip() { # target container
	local target=$1 color
	color=$(color_of "$target")
	cp -f "$CONF" "$CONF.prev"
	write_conf "$target" "$color" "$CONF.new"
	mv -f "$CONF.new" "$CONF"   # same dir as the nginx mount: atomic, new inode is visible
	if ! docker exec "$NGINX" nginx -t; then
		restore_conf || true
		die "nginx rejected the new config; old backend is still live"
	fi
	docker exec "$NGINX" nginx -s reload
	if ! verify_via_nginx "$color"; then
		restore_conf || true
		die "traffic check failed after flip; restored the previous backend"
	fi
	rm -f "$CONF.prev"
	log "live backend: $target ($color)"
}

wait_nginx_drain() { # old nginx workers finish in-flight requests, then exit
	local i
	for ((i = 0; i < DRAIN_MAX; i += 5)); do
		docker exec "$NGINX" sh -c 'grep -al "shutting [d]own" /proc/[0-9]*/cmdline' >/dev/null 2>&1 || return 0
		sleep 5
	done
	log "nginx workers still draining after ${DRAIN_MAX}s; stopping the old backend anyway"
}

retire() { # old container
	exists "$1" || return 0
	log "stopping $1 (gunicorn finishes in-flight requests, up to 180s)"
	docker stop -t 180 "$1" >/dev/null
	if [[ $1 == "$LEGACY" ]]; then
		# its ./backend bind mount now holds the new release: no valid rollback target
		docker rm "$1" >/dev/null
		log "removed legacy container $LEGACY"
	fi
}

preflight() {
	[[ -f misc/parkour.env ]] || die "misc/parkour.env missing"
	[[ -f $CONF ]] || die "$CONF missing: run 'make bg-init' first"
	running "$NGINX" || die "$NGINX is not running"
	docker inspect -f '{{range .Mounts}}{{.Destination}} {{end}}' "$NGINX" | grep -q '/etc/nginx/active' ||
		die "$NGINX has no /etc/nginx/active mount: run 'make bg-init' (recreates nginx, a few seconds)"
	docker network inspect parkour2_default >/dev/null 2>&1 || die "docker network parkour2_default missing"
	docker volume inspect parkour2_staticfiles >/dev/null 2>&1 || die "docker volume parkour2_staticfiles missing"
	command -v curl >/dev/null || die "curl missing on host"
}

migration_gate() { # reads `migrate --plan` output on stdin; prints findings; returns 1 if schema-breaking
	local blocking=0 line app name file
	local hard='RemoveField|DeleteModel|RenameField|RenameModel|AlterField|AlterModelTable|AlterUniqueTogether|AlterIndexTogether|RemoveIndex|RemoveConstraint'
	local soft='RunPython|RunSQL'
	while IFS= read -r line; do
		[[ $line =~ ^([a-z_0-9]+)\.([0-9]{4}_[A-Za-z0-9_]+)$ ]] || continue
		app=${BASH_REMATCH[1]} name=${BASH_REMATCH[2]}
		file=backend/$app/migrations/$name.py
		[[ -f $file ]] || { log "gate: $app.$name has no file in backend/ (third party?), not checked"; continue; }
		if grep -nE "\b($hard)\b" "$file" >&2; then
			log "gate: $file has schema-breaking operations (above)"
			blocking=1
		fi
		if grep -nE "\b($soft)\b" "$file" >&2; then
			log "gate: $file runs data/SQL code (above): review it"
		fi
	done
	return $blocking
}

final_backup() {
	make --no-print-directory save-postgres tar-old-migras
	docker exec "$RSNAPSHOT" rsnapshot halfy || log "WARN: rsnapshot halfy failed"
}

cmd_deploy() {
	local version="" yes=0 compatible=0 breaking=0 a
	for a in "$@"; do
		case $a in
			--yes) yes=1 ;;
			--compatible) compatible=1 ;;
			--breaking) breaking=1 ;;
			-*) die "unknown flag $a" ;;
			*) version=$a ;;
		esac
	done
	if [[ -n $version ]]; then
		[[ $(git rev-parse "$version^{commit}" 2>/dev/null) == "$(git rev-parse HEAD)" ]] ||
			die "HEAD is not $version: 'git checkout $version' first (the image is built from this checkout)"
	else
		version=$(git describe --tags --always)
	fi
	[[ $version =~ ^[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}$ ]] || die "'$version' is not a valid image tag"
	[[ -z $(git status --porcelain --untracked-files=no -- backend shared backend.Dockerfile) ]] ||
		die "uncommitted changes in backend/, shared/ or backend.Dockerfile: the image would not match $version"
	preflight

	local old idle plan
	old=$(active_container)
	idle=$(idle_of "$old")
	running "$old" || die "live backend $old is not running; fix that first (or 'make bg-rollback')"
	log "live: $old ($(color_of "$old")); deploying $version to $idle"
	if running "$idle"; then
		log "$idle is running but not live (previous attempt?): stopping it"
		docker stop -t 180 "$idle" >/dev/null
	fi

	log "backup before touching anything"
	make --no-print-directory save-postgres
	docker exec "$RSNAPSHOT" rsnapshot halfy || log "WARN: rsnapshot halfy failed"

	export PK2_VERSION=$version
	"${COMPOSE[@]}" build "$idle"
	"${COMPOSE[@]}" up -d --no-deps --force-recreate "$idle"
	wait_healthy "$idle"

	plan=$(docker exec "$idle" python manage.py migrate --plan)
	echo "$plan"
	if ! migration_gate <<<"$plan"; then
		((compatible || breaking)) ||
			die "schema-breaking migrations. Old code runs on the new schema until the flip. Re-run with --compatible (you checked old code still works: zero downtime) or --breaking (maintenance window)"
	fi
	if ((!yes)); then
		read -r -p "[bg] Apply migrations and make $idle live? [y/N] " a
		[[ $a == y || $a == Y ]] || die "aborted; $idle is left running but gets no traffic"
	fi

	if ((breaking)); then
		log "maintenance window: stopping $old (users get 502 until the flip)"
		docker stop -t 180 "$old" >/dev/null
	fi
	docker exec "$idle" python manage.py migrate --no-input
	docker exec "$idle" python manage.py collectstatic --no-input
	smoke_direct "$idle" || die "$idle fails GET /login/ directly; $old ${breaking:+was stopped and }stays configured as live"

	flip "$idle"
	((breaking)) || wait_nginx_drain
	retire "$old"

	final_backup
	{
		date
		docker ps
		echo "bg-deploy $version -> $idle (previous: $old)"
		echo -e "SUCCESS\n"
	} >>"$HOME/last.txt"
	log "done: $idle serves $version. Rollback: make bg-rollback"
}

cmd_rollback() {
	preflight
	local cur prev
	cur=$(active_container)
	prev=$(idle_of "$cur")
	if ! exists "$prev" || [[ $prev == "$LEGACY" ]]; then die "no previous color ($prev) to roll back to"; fi
	log "rolling back $cur -> $prev (database migrations are NOT reverted)"
	docker start "$prev" >/dev/null
	wait_healthy "$prev"
	smoke_direct "$prev" || die "$prev fails GET /login/ directly; staying on $cur"
	flip "$prev"
	wait_nginx_drain
	docker stop -t 180 "$cur" >/dev/null
	log "rolled back to $prev. If a migration was breaking, restore the dump from before the deploy."
}

cmd_status() {
	local c
	log "live: $(active_container)"
	for c in "$LEGACY" "${PREFIX}blue" "${PREFIX}green"; do
		exists "$c" || continue
		printf '[bg] %-24s %-8s health=%-10s image=%s\n' "$c" \
			"$(docker inspect -f '{{.State.Status}}' "$c")" \
			"$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}-{{end}}' "$c")" \
			"$(docker inspect -f '{{.Config.Image}}' "$c")"
	done
	curl -skI --max-time 20 https://127.0.0.1/login/ | tr -d '\r' | grep -i '^\(HTTP\|x-pk2-color\)' | sed 's/^/[bg] nginx: /' || true
}

case ${1:-} in
	deploy) shift; cmd_deploy "$@" ;;
	rollback) cmd_rollback ;;
	status) cmd_status ;;
	active) active_container ;;
	ensure-conf) ensure_conf ;;
	*) sed -n '2,9p' "$0" | sed 's/^## \{0,1\}//'; exit 2 ;;
esac
