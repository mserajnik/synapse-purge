#!/bin/sh

cp .crontab.docker /tmp/.crontab
sed -i "s~SYNAPSE_PURGE_DOCKER_CRON_SCHEDULE~$SYNAPSE_PURGE_DOCKER_CRON_SCHEDULE~g" /tmp/.crontab

source venv/bin/activate

stop() {
  pkill supercronic
  sleep 1
}

trap "stop" SIGTERM

supercronic /tmp/.crontab &

wait $!
