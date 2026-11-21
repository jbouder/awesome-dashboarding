#!/usr/bin/env bash
# Start an incident the metrics streamer plays back.
#
#   scripts/incident.sh [service] [kind] [minutes]
#
# service  web, checkout, payments, search, inventory  (default: checkout)
# kind     errors or latency                           (default: errors)
# minutes  how long it lasts                           (default: 3)
set -euo pipefail
cd "$(dirname "$0")/.."

service="${1:-checkout}"
kind="${2:-errors}"
minutes="${3:-3}"

case "$service" in web|checkout|payments|search|inventory) ;; *)
  echo "Unknown service: $service. Use web, checkout, payments, search, or inventory." >&2; exit 1 ;;
esac
case "$kind" in errors|latency) ;; *)
  echo "Unknown kind: $kind. Use errors or latency." >&2; exit 1 ;;
esac
[[ "$minutes" =~ ^[0-9]+$ ]] || { echo "Minutes must be a whole number." >&2; exit 1; }

docker compose exec -T warehouse psql -q -U lab -d lab -v ON_ERROR_STOP=1 \
  -c "INSERT INTO ops.incidents (service, kind, ends_at) VALUES ('$service', '$kind', now() + interval '$minutes minutes')"

echo "Started a $minutes-minute $kind incident on $service."
if [ "$kind" = "errors" ]; then
  echo "Grafana's \"High error rate\" alert fires about 30 seconds after the error rate passes 5%."
fi
