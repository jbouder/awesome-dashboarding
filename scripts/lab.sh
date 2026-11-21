#!/usr/bin/env bash
# The dashboard lab's command line. `make` calls this; you can too.
#
#   scripts/lab.sh doctor                   check Docker, memory, ports, and tools
#   scripts/lab.sh env                      create .env from .env.example
#   scripts/lab.sh pull [stack...]          download images ahead of time
#   scripts/lab.sh list                     every stack, its type, URL, and license
#   scripts/lab.sh up <stack...|all>        start stacks with the seed data loaded
#   scripts/lab.sh stop <stack...>          stop stacks, leave the rest running
#   scripts/lab.sh restart <stack...>       stop and start stacks again
#   scripts/lab.sh status                   each stack's state and URL
#   scripts/lab.sh open <stack...|all>      open stacks in the browser
#   scripts/lab.sh smoke                    check running stacks work and agree
#   scripts/lab.sh story                    the questions to ask, and the answer
#   scripts/lab.sh psql                     a psql shell on the warehouse (read-only)
#   scripts/lab.sh sql "<query>"            run one query on the warehouse
#   scripts/lab.sh incident [svc] [kind] [min]  start an incident (see incident.sh)
#   scripts/lab.sh logs <stack>             follow a stack's logs
#   scripts/lab.sh ps                       every lab container
#   scripts/lab.sh down                     stop everything, keep the data
#   scripts/lab.sh reset                    stop everything and delete all data
#   scripts/lab.sh reseed                   regenerate the seed data
#   scripts/lab.sh lint                     lint the lab's own scripts and Compose files
#
# Written for the bash 3.2 that ships with macOS.
set -euo pipefail
cd "$(dirname "$0")/.."

STACKS="superset metabase grafana rill holotable cube streamlit marimo"

# Per stack: type, URL, sign-in, license, long-running services, one-shot jobs.
stack_type() {
  case $1 in
    superset|metabase) echo "Strategic, analytical";;
    grafana) echo "Operational";;
    rill) echo "Analytical, operational";;
    holotable) echo "Generative";;
    cube) echo "Semantic layer";;
    streamlit|marimo) echo "AI-built app";;
  esac
}
stack_url() {
  case $1 in
    superset) echo "http://localhost:${SUPERSET_PORT:-8088}";;
    metabase) echo "http://localhost:${METABASE_PORT:-3002}";;
    grafana) echo "http://localhost:${GRAFANA_PORT:-3001}";;
    rill) echo "http://localhost:${RILL_PORT:-9009}";;
    holotable) echo "http://localhost:${HOLOTABLE_PORT:-3000}";;
    cube) echo "http://localhost:${CUBE_PORT:-4000}";;
    streamlit) echo "http://localhost:${STREAMLIT_PORT:-3003}";;
    marimo) echo "http://localhost:${MARIMO_PORT:-3004}";;
  esac
}
stack_login() {
  case $1 in
    superset) echo "admin / admin";;
    metabase) echo "admin@dashlab.local / dashlab-admin-1";;
    grafana) echo "none to view, admin / admin to edit";;
    holotable) echo "none (local owner)";;
    cube) echo "none (dev mode)";;
    *) echo "none";;
  esac
}
stack_license() {
  case $1 in
    grafana|metabase) echo "AGPL-3.0";;
    streamlit|holotable|cube|rill|marimo|superset) echo "Apache 2.0";;
  esac
}
stack_services() {
  case $1 in
    superset) echo "superset superset-mcp";;
    *) echo "$1";;
  esac
}
stack_jobs() {
  case $1 in
    superset) echo "superset-init superset-bootstrap";;
    holotable) echo "holotable-register";;
    metabase) echo "metabase-bootstrap";;
    *) echo "";;
  esac
}

# Load .env so ports and passwords printed here match what Compose uses.
# As in Compose, a variable already set in the shell wins over .env.
if [ -f .env ]; then
  while IFS='=' read -r key value; do
    case "$key" in ''|\#*|*[!A-Za-z0-9_]*) continue;; esac
    [ -n "${!key+x}" ] || export "$key=$value"
  done < .env
fi

say() { printf '\033[1m%s\033[0m\n' "$*"; }
die() { printf 'Error: %s\n' "$*" >&2; exit 1; }

known() { case " $STACKS " in *" $1 "*) return 0;; *) return 1;; esac; }

cmd_list() {
  printf '%-10s %-24s %-24s %-11s %s\n' STACK TYPE URL LICENSE SIGN-IN
  for s in $STACKS; do
    printf '%-10s %-24s %-24s %-11s %s\n' "$s" "$(stack_type "$s")" "$(stack_url "$s")" "$(stack_license "$s")" "$(stack_login "$s")"
  done
  echo
  echo "Guide only, no container: wrenai (see stacks/wrenai/README.md)"
  echo "Shared: warehouse on localhost:${WAREHOUSE_PORT:-5433} (lab_ro / lab_ro, database lab)"
}

cmd_up() {
  [ $# -gt 0 ] || die "name at least one stack, such as: make up superset. Stacks: $STACKS"
  local profiles="" services="" jobs="" s
  local list
  list=$(stacks_from "$@") || exit 1
  set -- $list
  for s in "$@"; do
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

# Expand "all" and check every name. Prints the stack names, one line.
stacks_from() {
  local s out=""
  [ $# -gt 0 ] || die "name at least one stack. Stacks: $STACKS"
  for s in "$@"; do [ "$s" = all ] && { echo "$STACKS"; return; }; done
  for s in "$@"; do known "$s" || die "unknown stack '$s'. Stacks: $STACKS"; out="$out $s"; done
  echo $out
}

stack_port() { stack_url "$1" | sed 's/.*://'; }

cmd_doctor() {
  local ok=1 v mem s port pid
  say "Checking what the lab needs"
  if ! command -v docker >/dev/null; then echo "  FAIL  docker is not installed"; ok=0
  elif ! docker info >/dev/null 2>&1; then echo "  FAIL  Docker is installed but not running. Start Docker Desktop or the daemon."; ok=0
  else echo "  PASS  Docker $(docker version --format '{{.Server.Version}}')"; fi
  if v=$(docker compose version --short 2>/dev/null); then
    case "$v" in 1.*|2.[0-9].*|2.1[0-9].*) echo "  FAIL  Compose $v. The lab needs 2.20 or later for include."; ok=0;;
      *) echo "  PASS  Compose $v";; esac
  else echo "  FAIL  docker compose is missing. Install Compose v2."; ok=0; fi
  mem=$(docker info --format '{{.MemTotal}}' 2>/dev/null || echo 0)
  if [ "${mem:-0}" -ge 4000000000 ] 2>/dev/null; then echo "  PASS  Docker memory $((mem / 1073741824)) GB"
  else echo "  WARN  Docker has $((${mem:-0} / 1073741824)) GB of memory. All stacks together need about 4 GB."; fi
  for t in make curl python3; do
    if command -v "$t" >/dev/null; then echo "  PASS  $t"; else echo "  WARN  $t not found. make smoke and make open need it."; fi
  done
  for s in $STACKS warehouse superset-mcp cube-sql; do
    case $s in
      warehouse) port=${WAREHOUSE_PORT:-5433};;
      superset-mcp) port=${SUPERSET_MCP_PORT:-5008};;
      cube-sql) port=${CUBE_SQL_PORT:-15432};;
      *) port=$(stack_port "$s");;
    esac
    pid=$(lsof -nP -iTCP:"$port" -sTCP:LISTEN -t 2>/dev/null | head -1 || true)
    if [ -z "$pid" ]; then echo "  PASS  port $port free ($s)"
    elif [ -n "$(docker compose --profile '*' ps -q 2>/dev/null)" ] && ps -p "$pid" -o comm= | grep -qi docker; then
      echo "  PASS  port $port in use by Docker, likely the lab ($s)"
    else echo "  WARN  port $port is taken by $(ps -p "$pid" -o comm= | xargs basename). Set a different port for $s in .env."; fi
  done
  [ $ok = 1 ] || die "fix the failures above, then run make up <stack>."
  echo; echo "Ready. Next: make up all"
}

cmd_env() {
  if [ -f .env ]; then echo ".env already exists. Compare it with .env.example by hand."; return; fi
  cp .env.example .env
  echo "Created .env. Set LLM_BASE_URL, LLM_API_KEY, and LLM_MODEL to turn on the AI features."
}

cmd_pull() {
  local profiles="" s
  local list
  [ $# -gt 0 ] || set -- all
  list=$(stacks_from "$@") || exit 1
  local services="warehouse" builds="seed"
  for s in $list; do
    profiles="$profiles --profile $s"
    case $s in
      streamlit|marimo|rill) builds="$builds $s";;  # built locally
      *) services="$services $(stack_services "$s")";;
    esac
  done
  docker compose $profiles pull $services
  docker compose $profiles build $builds
}

cmd_stop() {
  local s list
  list=$(stacks_from "$@") || exit 1
  for s in $list; do
    docker compose --profile "$s" rm --stop --force $(stack_services "$s") $(stack_jobs "$s")
    say "Stopped $s. Its data is kept."
  done
}

cmd_restart() {
  local list
  list=$(stacks_from "$@") || exit 1
  cmd_stop $list
  cmd_up $list
}

cmd_status() {
  local s svc state health code
  printf '%-10s %-28s %-24s %s\n' STACK STATE URL RESPONDS
  for s in warehouse stream $STACKS; do
    case $s in warehouse|stream) svc=$s;; *) svc=$(stack_services "$s" | cut -d' ' -f1);; esac
    state=$(docker compose --profile '*' ps -a --format '{{.State}} {{.Health}}' "$svc" 2>/dev/null | head -1)
    [ -n "$state" ] || state="not started"
    case $s in
      warehouse) printf '%-10s %-28s %-24s %s\n' "$s" "$state" "localhost:${WAREHOUSE_PORT:-5433}" "-" ;;
      stream) printf '%-10s %-28s %-24s %s\n' "$s" "$state" "-" "-" ;;
      *)
        code=$(curl -s -o /dev/null -m 3 -w '%{http_code}' "$(stack_url "$s")" 2>/dev/null || true)
        case "$code" in 2*|3*) health=yes;; 000|"") health=no;; *) health="HTTP $code";; esac
        printf '%-10s %-28s %-24s %s\n' "$s" "$state" "$(stack_url "$s")" "$health" ;;
    esac
  done
}

cmd_open() {
  local s opener
  if command -v open >/dev/null; then opener=open
  elif command -v xdg-open >/dev/null; then opener=xdg-open
  else die "no open or xdg-open command. Visit the URLs from make list."; fi
  local list
  list=$(stacks_from "$@") || exit 1
  for s in $list; do echo "Opening $s: $(stack_url "$s")"; $opener "$(stack_url "$s")"; done
}

cmd_smoke() { python3 scripts/smoke.py; }

warehouse_up() {
  [ -n "$(docker compose ps --status running -q warehouse 2>/dev/null)" ] || die "the warehouse is not running. Start a stack first: make up <stack>"
}

cmd_psql() { warehouse_up; exec docker compose exec warehouse psql -U lab_ro -d lab; }

cmd_sql() {
  [ $# -eq 1 ] && [ -n "$1" ] || die 'pass one query, such as: make sql Q="SELECT count(*) FROM shop.orders"'
  warehouse_up
  docker compose exec -T warehouse psql -U lab_ro -d lab -P pager=off -c "$1"
}

cmd_story() {
  warehouse_up
  say "Ask every tool these questions (from semantic/metrics.yml)"
  sed -n '/^questions:/,$p' semantic/metrics.yml | grep '^  - ' | sed 's/^  - /  /'
  echo
  say "The warehouse's answer: attainment by region, last full quarter"
  cmd_sql "SELECT region, round(sum(revenue)) AS revenue, round(sum(revenue_target)) AS target,
      round(100 * sum(revenue) / sum(revenue_target), 1) AS attainment_pct
    FROM metrics.monthly_kpis
    WHERE month >= date_trunc('quarter', now()) - interval '3 months' AND month < date_trunc('quarter', now())
    GROUP BY 1 ORDER BY 4"
  say "And why: EMEA revenue by channel, last two full quarters"
  cmd_sql "SELECT to_char(date_trunc('quarter', order_date), 'YYYY \"Q\"Q') AS quarter, channel, round(sum(revenue)) AS revenue
    FROM metrics.daily_revenue
    WHERE region = 'EMEA' AND order_date >= date_trunc('quarter', now()) - interval '6 months'
      AND order_date < date_trunc('quarter', now())
    GROUP BY 1, 2 ORDER BY 2, 1"
}

cmd_lint() {
  local failed=0
  say "Compose files"; docker compose --profile '*' config -q && echo "  ok" || failed=1
  say "Shell scripts"; bash -n scripts/*.sh && echo "  ok" || failed=1
  if command -v shellcheck >/dev/null; then shellcheck scripts/*.sh || failed=1; else echo "  shellcheck not installed, skipped"; fi
  say "Python"
  if command -v uvx >/dev/null; then uvx ruff check core stacks scripts && uvx ruff format --check core stacks scripts || failed=1
  else echo "  uv not installed, skipped (install uv to run ruff)"; fi
  [ $failed = 0 ] || die "lint failed"
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

cmd_help() { sed -n '2,23p' "$0" | sed 's/^# \{0,1\}//'; }

command="${1:-help}"
shift || true
case "$command" in
  doctor) cmd_doctor ;;
  env) cmd_env ;;
  pull) cmd_pull "$@" ;;
  list) cmd_list ;;
  up) cmd_up "$@" ;;
  stop) cmd_stop "$@" ;;
  restart) cmd_restart "$@" ;;
  status) cmd_status ;;
  open) cmd_open "$@" ;;
  smoke) cmd_smoke ;;
  story) cmd_story ;;
  psql) cmd_psql ;;
  sql) cmd_sql "$@" ;;
  incident) exec scripts/incident.sh "$@" ;;
  logs) cmd_logs "$@" ;;
  ps) cmd_ps ;;
  down) cmd_down ;;
  reset) cmd_reset ;;
  reseed) cmd_reseed ;;
  lint) cmd_lint ;;
  help|-h|--help) cmd_help ;;
  *) die "unknown command '$command'. Run: scripts/lab.sh help" ;;
esac
