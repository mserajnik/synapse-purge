# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

+ Made it so missing `purge_id` fields do not cause synapse-purge to error and
  exit
+ Made it so `m.room.avatar` events with missing `url` fields do not cause
  synapse-purge to error and exit

## [2.0.0] - 2020-07-01

### Changed

+ Added media thumbnail purging
+ Clarified that the printed timestamps are UTC

## [1.5.0] - 2020-01-29

### Added

+ Added the ability to install dependencies using Poetry
+ Added automatic code formatting using Black

## [1.4.1] - 2020-01-12

### Fixed

+ Fixed the usage of `USER_ID` instead of `GROUP_ID` in Docker image builds

## [1.4.0] - 2020-01-12

### Removed

+ Removed the ability to define custom UID and GID for the Docker container at
  container creation due to several issues arising from that

## [1.3.0] - 2020-01-12

### Changed

+ Changed the default Docker container behavior to only run synapse-purge once
  instead of starting a cron job

## [1.2.0] - 2020-01-07

### Added

+ Added the ability to define custom UID and GID for the Docker container at
  container creation

### Changed

+ Updated dependencies

## [1.1.0] - 2019-12-07

### Changed

+ Old user and room avatars are now excluded from getting purged due to issues
  with the latest ones getting removed as well

## 1.0.0 - 2019-11-04

### Added

+ Initial release

[Unreleased]: https://github.com/imtbl/synapse-purge/compare/2.0.0...develop
[2.0.0]: https://github.com/imtbl/synapse-purge/compare/1.5.0...2.0.0
[1.5.0]: https://github.com/imtbl/synapse-purge/compare/1.4.1...1.5.0
[1.4.1]: https://github.com/imtbl/synapse-purge/compare/1.4.0...1.4.1
[1.4.0]: https://github.com/imtbl/synapse-purge/compare/1.3.0...1.4.0
[1.3.0]: https://github.com/imtbl/synapse-purge/compare/1.2.0...1.3.0
[1.2.0]: https://github.com/imtbl/synapse-purge/compare/1.1.0...1.2.0
[1.1.0]: https://github.com/imtbl/synapse-purge/compare/1.0.0...1.1.0
