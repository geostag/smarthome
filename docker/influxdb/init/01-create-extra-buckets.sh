#!/bin/bash
set -euo pipefail

create_bucket() {
  local bucket_name="$1"

  if [ -z "${bucket_name}" ]; then
    return 0
  fi

  influx bucket create \
    --host http://localhost:8086 \
    --org "${DOCKER_INFLUXDB_INIT_ORG}" \
    --token "${DOCKER_INFLUXDB_INIT_ADMIN_TOKEN}" \
    --name "${bucket_name}" \
    --retention 0 \
    >/dev/null 2>&1 || true
}

create_bucket "${INFLUX_DERIVED_BUCKET:-}"
create_bucket "${INFLUX_LONGRANGE_BUCKET:-}"
