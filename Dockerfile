FROM python:3.8-alpine

ENV \
  SUPERCRONIC_URL=https://github.com/aptible/supercronic/releases/download/v0.1.9/supercronic-linux-amd64 \
  SUPERCRONIC=supercronic-linux-amd64 \
  SUPERCRONIC_SHA1SUM=5ddf8ea26b56d4a7ff6faecdd8966610d5cb9d85

WORKDIR /usr/src/app

COPY . .

RUN \
  chmod +x synapse-purge.py && \
  mkdir /data && \
  apk --no-cache add \
    build-base \
    curl \
    postgresql-dev \
    su-exec && \
  curl -fsSLO "$SUPERCRONIC_URL" && \
  echo "${SUPERCRONIC_SHA1SUM}  ${SUPERCRONIC}" | sha1sum -c - && \
  chmod +x "$SUPERCRONIC" && \
  mv "$SUPERCRONIC" "/usr/local/bin/${SUPERCRONIC}" && \
  ln -s "/usr/local/bin/${SUPERCRONIC}" /usr/local/bin/supercronic && \
  pip install virtualenv && \
  virtualenv venv && \
  source venv/bin/activate && \
  pip install \
    loguru~=0.4.0 \
    postgres~=3.0.0 \
    requests~=2.22.0 && \
  rm -r ~/.cache && \
  apk del build-base

COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint
COPY docker-cmd-run.sh /usr/local/bin/run
COPY docker-cmd-cron.sh /usr/local/bin/cron
RUN \
  chmod +x /usr/local/bin/docker-entrypoint && \
  chmod +x /usr/local/bin/run && \
  chmod +x /usr/local/bin/cron

ENTRYPOINT ["/usr/local/bin/docker-entrypoint"]
CMD ["cron"]
