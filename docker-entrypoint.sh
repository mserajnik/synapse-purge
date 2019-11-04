#!/bin/sh

if [[ $# -eq 0 ]]; then
  echo "No mode selected, exiting."
  exit 1
fi

if [[ $1 = cron ]]; then
  cp .crontab.docker .crontab
  sed -i "s~SYNAPSE_PURGE_DOCKER_CRON_SCHEDULE~$SYNAPSE_PURGE_DOCKER_CRON_SCHEDULE~g" .crontab

  source venv/bin/activate

  stop() {
    pkill supercronic
    sleep 1
  }

  trap "stop" SIGTERM

  supercronic .crontab &

  wait $!
elif [[ $1 = run ]]; then
  source venv/bin/activate

  ./synapse-purge.py
else
  echo "No mode selected, exiting."
  exit 1
fi
