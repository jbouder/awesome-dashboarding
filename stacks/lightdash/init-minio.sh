#!/bin/sh
# MinIO for Lightdash's S3 storage: start it, then create the bucket.
set -e
minio server /data &
until mc alias set local http://localhost:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD" >/dev/null 2>&1; do
  sleep 1
done
mc mb -p local/lightdash >/dev/null 2>&1 || true
echo "MinIO ready with bucket lightdash"
wait
