#!/bin/sh

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
