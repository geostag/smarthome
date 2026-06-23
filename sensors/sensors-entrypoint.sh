#!/bin/bash
set -euo pipefail

while true; do
  if [ -f /etc/smarthome-secrets/.env ]; then
    . /etc/smarthome-secrets/.env
    if [ "_$INFLUX_READALL_TOKEN" != "_" ]; then
      echo "found. starting up"
      break
    fi
  fi
  echo "please run bootstrap.sh once to set up influxdb, grafana and secrets"
  echo "waiting 60 seconds"
  sleep 60
done


cd /app
mkdir -p /app/logs

declare -A seen_scripts=()
declare -a all_scripts=()
for script in ${SENSORS}; do
  [ -n "${script}" ] || continue
  if [ -z "${seen_scripts[${script}]+x}" ]; then
    seen_scripts["${script}"]=1
    all_scripts+=("${script}")
  fi
done

declare -a daemon_pids=()

start_script() {
  local script="$1"

  echo "Starting script ${script}"
  python -u "/app/bin/${script}" &
  local pid=$!

  daemon_pids+=("${pid}")
}

terminate_children() {
  local pids=("${daemon_pids[@]}")
  if [ "${#pids[@]}" -gt 0 ]; then
    kill "${pids[@]}" 2>/dev/null || true
    wait "${pids[@]}" 2>/dev/null || true
  fi
}

trap terminate_children SIGINT SIGTERM

for script in "${all_scripts[@]}"; do
  if [ ! -f "/app/bin/${script}" ]; then
    echo "Skipping missing script ${script}"
    continue
  fi

  start_script "${script}"
done

while true; do
  set +e
  wait -n "${daemon_pids[@]}"
  status=$?
  set -e

  date
  echo "A daemon script exited with status ${status}. Stopping the scripts container."
  terminate_children
  exit "${status}"
done
