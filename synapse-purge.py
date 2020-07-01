#!/usr/bin/env python

# synapse-purge
# Copyright (C) 2019-present  Chris Braun  https://github.com/cryzed
# Copyright (C) 2019-present  Michael Serajnik  https://mserajnik.dev

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import argparse
import enum
import json
import os
import sys
import time
import urllib.parse
from datetime import datetime, timedelta
from typing import Optional, Set, List, Dict

import postgres
import psycopg2
import requests
from loguru import logger

PURGE_HISTORY_API_ENDPOINT = "/_matrix/client/r0/admin/purge_history/{room}"
PURGE_HISTORY_STATUS_API_ENDPOINT = "/_matrix/client/r0/admin/purge_history_status/{id}"
PURGE_REMOTE_MEDIA_API_ENDPOINT = "/_matrix/client/r0/admin/purge_media_cache/"


class ExitCode(enum.IntEnum):
    Success = 0
    Failure = 1


class PurgeStatus(str, enum.Enum):
    Active = "active"
    Complete = "complete"
    Failed = "failed"


def get_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "postgres_connection_string",
        nargs="?",
        default=os.getenv("SYNAPSE_PURGE_POSTGRES_CONNECTION_STRING"),
    )
    parser.add_argument(
        "synapse_auth_token",
        nargs="?",
        default=os.getenv("SYNAPSE_PURGE_SYNAPSE_AUTH_TOKEN"),
    )
    parser.add_argument(
        "--delta",
        "-d",
        type=int,
        default=os.getenv("SYNAPSE_PURGE_DELTA", 60 * 60 * 24),
    )
    parser.add_argument(
        "--logging-level",
        "-l",
        choices={"TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"},
        default=os.getenv("SYNAPSE_PURGE_LOGGING_LEVEL", "INFO"),
    )
    parser.add_argument(
        "--api-url",
        "-a",
        default=os.getenv("SYNAPSE_PURGE_SYNAPSE_API_URL", "http://localhost:8008/"),
    )
    parser.add_argument(
        "--media-store",
        "-m",
        default=os.getenv("SYNAPSE_PURGE_MEDIA_STORE_PATH", "/data/media_store"),
    )
    return parser


def get_api_url(base_url: str, suffix: str) -> str:
    return urllib.parse.urljoin(base_url, suffix)


def get_delta_date(seconds: int) -> datetime:
    return datetime.utcnow() - timedelta(seconds=seconds)


def get_last_event_id(
    db: postgres.Postgres, room_id: str, before: datetime
) -> Optional[str]:
    return db.one(
        "SELECT event_id FROM events WHERE received_ts <= %(before)s AND room_id=%(room_id)s ORDER BY received_ts DESC LIMIT 1",
        before=int(before.timestamp() * 1000),
        room_id=room_id,
    )


def get_important_media_ids(db: postgres.Postgres) -> Set[str]:
    media_ids = set()

    for event in db.all("SELECT json FROM event_json"):
        data = json.loads(event)
        content = data["content"]

        if data["type"] == "m.room.member":
            avatar_url = content.get("avatar_url")
            if avatar_url:
                media_ids.add(avatar_url)
        elif data["type"] == "m.room.avatar":
            media_ids.add(content["url"])

    return set(urllib.parse.urlsplit(url).path[1:] for url in media_ids)


def get_local_media_record_ids(db: postgres.Postgres, before: datetime) -> List[str]:
    return db.all(
        "SELECT media_id FROM local_media_repository WHERE created_ts <= %(before)s",
        before=int(before.timestamp() * 1000),
    )


def get_room_record_ids(db: postgres.Postgres) -> List[str]:
    return db.all("SELECT room_id FROM rooms")


def delete_local_media_record(db: postgres.Postgres, media_id: str) -> None:
    db.run(
        "DELETE FROM local_media_repository WHERE media_id = %(media_id)s",
        media_id=media_id,
    )


def purge_history(
    session: requests.Session, api_url: str, room_id: str, event_id: str
) -> str:
    url = get_api_url(api_url, PURGE_HISTORY_API_ENDPOINT).format(room=room_id)
    payload = {"delete_local_events": True, "purge_up_to_event_id": event_id}
    return session.post(url, json=payload).json()["purge_id"]


def purge_history_status(
    session: requests.Session, api_url: str, purge_id: str
) -> PurgeStatus:
    url = get_api_url(api_url, PURGE_HISTORY_STATUS_API_ENDPOINT).format(id=purge_id)
    return PurgeStatus(session.get(url).json()["status"])


def purge_remote_media(
    session: requests.Session, api_url: str, before: datetime
) -> Dict:
    url = get_api_url(api_url, PURGE_REMOTE_MEDIA_API_ENDPOINT)
    return session.post(
        url, params={"before_ts": int(before.timestamp() * 1000)}
    ).json()


def get_local_media_paths(media_store_path: str, media_id: str) -> List[str]:
    paths = []
    for folder_name in "local_content", "local_thumbnails":
        path = os.path.join(
            media_store_path, folder_name, media_id[:2], media_id[2:4], media_id[4:]
        )
        paths.append(path)

    return paths


def wait_for_purge(
    session: requests.Session, api_url: str, purge_id: str, interval: float = 1
) -> PurgeStatus:
    while True:
        status = purge_history_status(session, api_url, purge_id)
        if status != PurgeStatus.Active:
            return status

        time.sleep(interval)


def main(arguments: argparse.Namespace) -> ExitCode:
    logger.remove()
    logger.add(sys.stderr, level=arguments.logging_level)
    logger.debug("Called with {!r}", arguments)

    if not (arguments.postgres_connection_string and arguments.synapse_auth_token):
        logger.error(
            "Postgres connection string and Synapse auth token can not be empty"
        )
        return ExitCode.Failure

    try:
        db = postgres.Postgres(arguments.postgres_connection_string)
    except (psycopg2.OperationalError, psycopg2.InternalError):
        logger.exception(
            "Connecting to database using {!r} failed:",
            arguments.postgres_connection_string,
        )
        return ExitCode.Failure

    session = requests.session()
    session.headers["Authorization"] = "Bearer " + arguments.synapse_auth_token

    before_date = get_delta_date(int(arguments.delta))
    before_date_string = before_date.isoformat(sep=" ", timespec="seconds")
    logger.info("Purging events up to: {} UTC", before_date_string)

    # Purge room history for all rooms
    rooms = get_room_record_ids(db)
    room_count = len(rooms)
    for index, room_id in enumerate(rooms, start=1):
        logger.info("({}/{}) Processing room: {!r}...", index, room_count, room_id)
        event_id = get_last_event_id(db, room_id, before_date)
        if event_id is None:
            logger.info(
                "No event ID before: {} UTC for room: {!r}, skipping",
                before_date_string,
                room_id,
            )
            continue

        logger.info(
            "Last event ID before: {} UTC for room {!r}: {!r}",
            before_date_string,
            room_id,
            event_id,
        )
        purge_id = purge_history(session, arguments.api_url, room_id, event_id)
        logger.info("Purging room: {!r} in progress: {!r}...", room_id, purge_id)
        result = wait_for_purge(session, arguments.api_url, purge_id)
        logger.info("Purged room: {!r} with status: {!r}", room_id, result)

    logger.info("Purging local media older than: {} UTC...", before_date_string)
    local_media = get_local_media_record_ids(db, before_date)
    important_files = get_important_media_ids(db)

    # Purge local media manually
    old_media = set(local_media) - important_files
    old_media_count = len(old_media)
    logger.info("{} media to be cleaned...", len(old_media))
    for index, media_id in enumerate(old_media, start=1):
        logger.info(
            "({}/{}) Processing media: {!r}...", index, old_media_count, media_id
        )
        paths = get_local_media_paths(arguments.media_store, media_id)
        for path in paths:
            if not os.path.isfile(path):
                logger.debug("{!r} could not be found or is not a file", path)
                continue
            os.remove(path)

        delete_local_media_record(db, media_id)

    # Purge remote media
    logger.info("Purging cached remote media older than: {} UTC...", before_date_string)
    result = purge_remote_media(session, arguments.api_url, before_date)
    logger.info("Purged cached remote media: {!r}", result)
    return ExitCode.Success


if __name__ == "__main__":
    parser = get_argument_parser()
    arguments = parser.parse_args()
    parser.exit(main(arguments))
