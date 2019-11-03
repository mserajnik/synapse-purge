FROM python:3.8-alpine

ARG HOST_USER_ID=1000
ARG HOST_GROUP_ID=1000

ENV \
  HOST_USER_ID=$HOST_USER_ID \
  HOST_GROUP_ID=$HOST_GROUP_ID \
  SUPERCRONIC_URL=https://github.com/aptible/supercronic/releases/download/v0.1.9/supercronic-linux-amd64 \
  SUPERCRONIC=supercronic-linux-amd64 \
  SUPERCRONIC_SHA1SUM=5ddf8ea26b56d4a7ff6faecdd8966610d5cb9d85

RUN \
  if [ $(getent group ${HOST_GROUP_ID}) ]; then \
    adduser -D -u ${HOST_USER_ID} synapse-purge; \
  else \
    addgroup -g ${HOST_GROUP_ID} synapse-purge && \
    adduser -D -u ${HOST_USER_ID} -G synapse-purge synapse-purge; \
  fi

WORKDIR /usr/src/app

COPY . .

RUN \
  chown -R synapse-purge:synapse-purge /usr/src/app && \
  chmod +x synapse-purge.py && \
  mkdir /data && chown -R synapse-purge:synapse-purge /data && \
  apk --no-cache add \
    build-base \
    curl \
    postgresql-dev && \
  curl -fsSLO "$SUPERCRONIC_URL" && \
  echo "${SUPERCRONIC_SHA1SUM}  ${SUPERCRONIC}" | sha1sum -c - && \
  chmod +x "$SUPERCRONIC" && \
  mv "$SUPERCRONIC" "/usr/local/bin/${SUPERCRONIC}" && \
  ln -s "/usr/local/bin/${SUPERCRONIC}" /usr/local/bin/supercronic && \
  pip install virtualenv && \
  virtualenv venv && \
  source venv/bin/activate && \
  pip install \
    loguru~=0.3.2 \
    postgres~=3.0.0 \
    requests~=2.22.0 && \
  rm -r ~/.cache && \
  apk del build-base

COPY docker-entrypoint.sh /usr/local/bin/start
RUN chmod +x /usr/local/bin/start

USER synapse-purge

ENTRYPOINT ["/usr/local/bin/start"]
CMD ["cron"]
