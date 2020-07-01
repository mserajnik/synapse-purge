# synapse-purge [![Docker Hub build][docker-hub-badge]][docker-hub]

> A script to purge content from Synapse servers

This is a simple script to purge content from [Synapse][synapse] servers. It
deletes events, local media and cached remote media up to a specified point in
time. Old user and room avatars are (for now) excluded from getting purged due
to issues with the latest ones getting removed as well. Currently, only Synapse
instances using a [PostgreSQL][postgresql] database are supported.

Note that content on remote (federated) servers can obviously not be deleted
and that Synapse might not consider the most recent content as _history_, which
excludes it from beling deleted even if it is technically inside the specified
purge timeframe.

## Table of contents

+ [Install](#install)
  + [Installing with Docker](#installing-with-docker)
  + [Installing without Docker](#installing-without-docker)
  + [Dependencies](#dependencies)
  + [Updating](#updating)
    + [Updating with Docker](#updating-with-docker)
    + [Updating without Docker](#updating-without-docker)
+ [Usage](#usage)
  + [Running with Docker](#running-with-docker)
  + [Running without Docker](#running-without-docker)
  + [Configuration](#configuration)
+ [Maintainer](#maintainer)
+ [Contribute](#contribute)
+ [License](#license)

## Install

The recommended way to run is via [Docker][docker]. Basic instructions on how
to run without it are also provided.

### Installing with Docker

To install for running with Docker, you can simply pull the prebuilt image from
[Docker Hub][docker-hub]:

```zsh
user@local:~$ docker pull mtbl/synapse-purge
```

Alternatively, you can also build the image yourself. The user that is used
inside the container has UID `1000` and GID `1000` by default. You can adjust
this (e.g., to match your host UID/GID) by providing the arguments `USER_ID`
and `GROUP_ID` when making a build.

### Installing without Docker

To install without Docker, you can simply clone the repository and install
dependencies using Poetry.

```zsh
user@local:~$ git clone https://github.com/imtbl/synapse-purge.git
user@local:~$ cd synapse-purge
user@local:synapse-purge$ poetry install
```

### Dependencies

+ [Docker][docker] (when running with Docker)
+ [Python 3.7+][python] (when running without Docker)
+ [Poetry][poetry] (when running without Docker)

### Updating

This script follows [semantic versioning][semantic-versioning] and any breaking
changes that require additional attention will be released under a new major
version (e.g., `2.0.0`). Minor version updates (e.g., `1.1.0` or `1.2.0`) are
therefore always safe to simply install.

When necessary, this section will be expanded with upgrade guides for new major
versions.

#### Updating with Docker

Simply pull the latest Docker image to update:

```zsh
user@local:~$ docker pull mtbl/synapse-purge
```

#### Updating without Docker

If you have installed via cloning the repository, you can update using Git as
well:

```zsh
user@local:synapse-purge$ git pull
```

## Usage

### Running with Docker

To make running with Docker as easy as possible, a working
[Docker Compose][docker-compose] example setup is provided. To get started with
this example setup, simply duplicate `docker-compose.yml.example` as
`docker-compose.yml` and adjust the path to the Synapse data directory in the
`volumes` section, the variables in the `environment` section as
described [here](#configuration) and change the `command` if you want to (you
can either run the script once or periodically via cron job).

Take note of the time zone set via the `TZ` environment variable. This is
particularly important for the cron job to run at the time you expect it to.
The time zone has to be set in the
[tz database format][tz-database-time-zones].

Finally, start the container:

```zsh
user@local:synapse-purge$ docker-compose up -d
```

Depending on your choice, the script will now either run once (with command
`run`) or periodically via cron job until stopped (with command `cron`).

The user that is used inside the container when the script is run has the UID
`1000` and the GID `1000` by default. You can change these by providing the
environment variables `CUSTOM_UID` and `CUSTOM_GID` when creating a container.

### Running without Docker

First of all, spawn a shell within the virtual environment (this also creates
the environment if it does not exist yet):

```zsh
user@local:synapse-purge$ poetry shell
```

You can use either environment variables or arguments to configure the script
when running without Docker. The script will look for the provided argument
first and fall back to the respective environment variable if the argument is
not provided.

To see the required and optional arguments, simple launch the script with the
`-h` flag:

```zsh
user@local:synapse-purge$ ./synapse-purge.py -h
usage: synapse-purge.py [-h] [--delta DELTA] [--logging-level {TRACE,DEBUG,INFO,SUCCESS,WARNING,ERROR,CRITICAL}] [--api-url API_URL] [--media-store MEDIA_STORE]
                        [postgres_connection_string] [synapse_auth_token]

positional arguments:
  postgres_connection_string
  synapse_auth_token

optional arguments:
  -h, --help            show this help message and exit
  --delta DELTA, -d DELTA
  --logging-level {TRACE,DEBUG,INFO,SUCCESS,WARNING,ERROR,CRITICAL}, -l {TRACE,DEBUG,INFO,SUCCESS,WARNING,ERROR,CRITICAL}
  --api-url API_URL, -a API_URL
  --media-store MEDIA_STORE, -m MEDIA_STORE
```

### Configuration

Configuration is done via environment variables when running with Docker. These
can also be used when running without Docker, although using launch parameters
instead might be preferable in that case (see [here](#running-without-docker)).

+ `SYNAPSE_PURGE_MEDIA_STORE_PATH=/data/media_store`: the path to the Synapse
  `media_store` directory.
+ `SYNAPSE_PURGE_POSTGRES_CONNECTION_STRING=`:
  the PostgreSQL connection string for the Synapse database, e.g.,
  `host=localhost port=5432 user=synapse dbname=synapse password=password`.
+ `SYNAPSE_PURGE_SYNAPSE_API_URL=http://localhost:8008/`: the base URL of the
  Synapse API. __Trailing `/` required.__
+ `SYNAPSE_PURGE_SYNAPSE_AUTH_TOKEN=`: the access token of an admin user. Can
  be created via `curl -XPOST -d '{"type":"m.login.password", "user":"<userid>", "password":"<password>"}' "http://localhost:8008/_matrix/client/r0/login"`.
+ `SYNAPSE_PURGE_DELTA=86400`: the current date minus the provided value here
  (in seconds) is the date up to which the script will purge.
+ `SYNAPSE_PURGE_LOGGING_LEVEL=INFO`: the desired logging level. Has to be one
  of these: `TRACE`, `DEBUG`, `INFO`, `SUCCESS`, `WARNING`, `ERROR`, `CRITICAL`.
+ `SYNAPSE_PURGE_DOCKER_CRON_SCHEDULE=0 4 * * *`: the cron schedule for running
  with Docker using the `cron` command.

## Maintainer

[imtbl][maintainer]

## Contribute

You are welcome to help out!

[Open an issue][issues] or submit a pull request.

## License

[AGPLv3](LICENSE) © imtbl

[synapse]: https://github.com/matrix-org/synapse/
[postgresql]: https://www.postgresql.org/
[docker]: https://www.docker.com/
[docker-hub]: https://hub.docker.com/r/mtbl/synapse-purge/
[python]: https://www.python.org/
[poetry]: https://python-poetry.org/
[semantic-versioning]: https://semver.org/
[docker-compose]: https://docs.docker.com/compose/
[tz-database-time-zones]: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones

[docker-hub-badge]: https://img.shields.io/docker/cloud/automated/mtbl/synapse-purge.svg

[maintainer]: https://github.com/imtbl
[issues]: https://github.com/imtbl/synapse-purge/issues/new
