#!/bin/bash

_loader_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
export sh_basedir="$(dirname "${_loader_dir}")"
_env_file="${sh_basedir}/.env"

if [ ! -f "${_env_file}" ]; then
  echo "ERROR: create ${_env_file} first (for example: cp .env.template .env)"
  if [ "${BASH_SOURCE[0]}" = "$0" ]; then
    exit 2
  else
    return 2
  fi
fi

set -a
. "${_env_file}"
set +a

export sh_penvdir="${sh_basedir}/penv"
export PATH="${sh_basedir}/bin:${PATH}"
export USERID="${USERID:-$(id -u)}"
export sh_logdir="${sh_logdir:-${sh_basedir}/logs}"
