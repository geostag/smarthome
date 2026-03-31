#!/bin/bash
set -euo pipefail

cd /app
mkdir -p /app/logs

declare -a discovered_scripts
mapfile -t discovered_scripts < <(find /app/bin -maxdepth 1 -type f -name '*2influxdb.py' -printf '%f\n' | sort)

declare -a extra_scripts
if [ -n "${SCRIPTS_EXTRA_FILES:-}" ]; then
  read -r -a extra_scripts <<< "${SCRIPTS_EXTRA_FILES}"
else
  extra_scripts=()
fi

declare -A seen_scripts=()
declare -a all_scripts=()
for script in "${discovered_scripts[@]}" "${extra_scripts[@]}"; do
  [ -n "${script}" ] || continue
  if [ -z "${seen_scripts[${script}]+x}" ]; then
    seen_scripts["${script}"]=1
    all_scripts+=("${script}")
  fi
done

declare -A one_shot_scripts=()
for script in ${SCRIPTS_ONE_SHOT_FILES:-}; do
  [ -n "${script}" ] || continue
  one_shot_scripts["${script}"]=1
done

declare -a daemon_pids=()
declare -a one_shot_pids=()

start_script() {
  local script="$1"
  local mode="$2"
  local logfile="/app/logs/${script%.py}.log"

  echo "Starting ${mode} script ${script} -> ${logfile}"
  python -u "/app/bin/${script}" >> "${logfile}" 2>&1 &
  local pid=$!

  if [ "${mode}" = "daemon" ]; then
    daemon_pids+=("${pid}")
  else
    one_shot_pids+=("${pid}")
  fi
}

terminate_children() {
  local pids=("${daemon_pids[@]}" "${one_shot_pids[@]}")
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

  if [ -n "${one_shot_scripts[${script}]+x}" ]; then
    start_script "${script}" "one-shot"
  else
    start_script "${script}" "daemon"
  fi
done

if [ "${#daemon_pids[@]}" -eq 0 ]; then
  echo "No daemon scripts configured. Waiting for one-shot jobs to finish."
  wait "${one_shot_pids[@]}"
  exit 0
fi

while true; do
  set +e
  wait -n "${daemon_pids[@]}"
  status=$?
  set -e

  echo "A daemon script exited with status ${status}. Stopping the scripts container."
  terminate_children
  exit "${status}"
done
