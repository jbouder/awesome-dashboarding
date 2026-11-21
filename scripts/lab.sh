#!/usr/bin/env bash
# The dashboard lab's command line. `make` calls this; you can too.
#
#   scripts/lab.sh list                     every stack, its type, URL, and license
#   scripts/lab.sh up <stack>...            start stacks with the seed data loaded
#   scripts/lab.sh down                     stop everything, keep the data
#   scripts/lab.sh reset                    stop everything and delete all data
#   scripts/lab.sh reseed                   regenerate the seed data
#   scripts/lab.sh incident [svc] [kind] [min]  start an incident (see incident.sh)
#   scripts/lab.sh ps                       what is running
#   scripts/lab.sh logs <stack>             follow a stack's logs
#
# Written for the bash 3.2 that ships with macOS.
set -euo pipefail
cd "$(dirname "$0")/.."

STACKS="superset grafana holotable metabase"

# Per stack: type, URL, sign-in, license, long-running services, one-shot jobs.
stack_type()    { case $1 in superset) echo "Strategic, analytical";; grafana) echo "Operational";; holotable) echo "Generative";; metabase) echo "Strategic, analytical";; esac; }
stack_url()     { case $1 in superset) echo "http://localhost:${SUPERSET_PORT:-8088}";; grafana) echo "http://localhost:${GRAFANA_PORT:-3001}";; holotable) echo "http://localhost:${HOLOTABLE_PORT:-3000}";; metabase) echo "http://localhost:${METABASE_PORT:-3002}";; esac; }
stack_login()   { case $1 in superset) echo "admin / admin";; grafana) echo "none to view, admin / admin to edit";; holotable) echo "none (local owner)";; metabase) echo "admin@dashlab.local / dashlab-admin-1";; esac; }
stack_license() { case $1 in superset) echo "Apache 2.0";; grafana) echo "AGPL-3.0";; holotable) echo "Apache 2.0";; metabase) echo "AGPL-3.0";; esac; }
stack_services() { case $1 in superset) echo "superset superset-mcp";; grafana) echo "grafana";; holotable) echo "holotable";; metabase) echo "metabase";; esac; }
stack_jobs()    { case $1 in superset) echo "superset-init superset-bootstrap";; grafana) echo "";; holotable) echo "holotable-register";; metabase) echo "metabase-bootstrap";; esac; }

# Load .env so ports and passwords printed here match what Compose uses.
if [ -f .env ]; then set -a; . ./.env; set +a; fi

say() { printf '\033[1m%s\033[0m\n' "$*"; }
die() { printf 'Error: %s\n' "$*" >&2; exit 1; }

known() { case " $STACKS " in *" $1 "*) return 0;; *) return 1;; esac; }

cmd_list() {
  printf '%-10s %-22s %-24s %-11s %s\n' STACK TYPE URL LICENSE SIGN-IN
  for s in $STACKS; do
    printf '%-10s %-22s %-24s %-11s %s\n' "$s" "$(stack_type "$s")" "$(stack_url "$s")" "$(stack_license "$s")" "$(stack_login "$s")"
  done
  echo
  echo "Guide only, no container: wrenai (see stacks/wrenai/README.md)"
  echo "Shared: warehouse on localhost:${WAREHOUSE_PORT:-5433} (lab_ro / lab_ro, database lab)"
}

cmd_up() {
  [ $# -gt 0 ] || die "name at least one stack, such as: make up superset. Stacks: $STACKS"
  local profiles="" services="" jobs="" s
  for s in "$@"; do
    [ "$s" = all ] && { set -- $STACKS; break; }
  done
  for s in "$@"; do
    known "$s" || die "unknown stack '$s'. Stacks: $STACKS"
    profiles="$profiles --profile $s"
    services="$services $(stack_services "$s")"
    jobs="$jobs $(stack_jobs "$s")"
  done

  say "Starting the warehouse, seed data, and: $*"
  docker compose $profiles up -d --build
  say "Waiting for services to be healthy"
  docker compose $profiles up -d --wait warehouse stream $services
  for j in seed $jobs; do
    # docker wait returns the exit code, even for a job that already finished.
    id=$(docker compose $profiles ps -a -q "$j" | head -1)
    code=$([ -n "$id" ] && docker wait "$id" || echo missing)
    if [ "$code" != "0" ]; then
      docker compose logs --tail 30 "$j" >&2 || true
      die "$j failed (exit ${code:-unknown}). Its last log lines are above."
    fi
  done

  echo
  say "Ready"
  for s in "$@"; do
    printf '  %-10s %-24s %s\n' "$s" "$(stack_url "$s")" "$(stack_login "$s")"
  done
  echo
  echo "Tours: stacks/<name>/README.md. Stop with: make down"
}

cmd_down()   { docker compose --profile '*' down; }
cmd_reset()  { docker compose --profile '*' down --volumes; say "All lab data deleted."; }
cmd_ps()     { docker compose --profile '*' ps; }

cmd_reseed() {
  docker compose up -d --wait warehouse
  docker compose build seed
  SEED_FORCE=1 docker compose run --rm seed
}

cmd_logs() {
  [ $# -eq 1 ] || die "name one stack, such as: make logs superset"
  known "$1" || die "unknown stack '$1'. Stacks: $STACKS"
  docker compose --profile "$1" logs -f $(stack_services "$1") $(stack_jobs "$1")
}

cmd_help() { sed -n '2,13p' "$0" | sed 's/^# \{0,1\}//'; }

command="${1:-help}"
shift || true
case "$command" in
  list) cmd_list ;;
  up) cmd_up "$@" ;;
  down) cmd_down ;;
  reset) cmd_reset ;;
  reseed) cmd_reseed ;;
  incident) exec scripts/incident.sh "$@" ;;
  ps) cmd_ps ;;
  logs) cmd_logs "$@" ;;
  help|-h|--help) cmd_help ;;
  *) die "unknown command '$command'. Run: scripts/lab.sh help" ;;
esac
