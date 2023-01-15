"""Functions to migrate data to newer config versions."""

import logging

from . import init

logging.getLogger(__name__)

LATEST = 1
MIGRATIONS = {
    0: (1, init.migrate)
}


class MigrationError(Exception):
    def __init__(self, src, target, msg):
        self.source = src
        self.target = target
        self.message = msg

        super().__init__(f'Error while migrating {src} -> {target}: {msg}')


def should_migrate(data: dict):
    if not data:  # probably no config
        return True

    try:
        version = int(data['_v'])
    except (KeyError, ValueError):
        raise MigrationError(None, None, 'Unknown config version')

    return version < LATEST


def migrate(data: dict, force=False, can_downgrade=False):
    try:
        cur_version = int(data['_v'])
    except (KeyError, ValueError):
        if force:  # no version, so force re-init of config file
            cur_version = 0
        else:
            raise MigrationError(None, None, 'Unknown config version')

    logging.info('Planning migration path')

    migrate_path = []
    v = cur_version
    while v < LATEST:
        next_migration = MIGRATIONS.get(v, None)
        if next_migration is None:
            raise MigrationError(v, LATEST, 'No migration exists')
        elif next_migration[0] == v:
            raise MigrationError(v, v, 'Cannot migrate to same version')
        elif next_migration[0] < v and not can_downgrade:
            raise MigrationError(v, next_migration[0],
                                 'Path will migrate to lower version but downgrades are not allowed')

        migrate_path.append(next_migration)
        v = next_migration[0]

    logging.info(f'Planned path: {cur_version} -> {" -> ".join(str(m[0]) for m in migrate_path)}')

    v = cur_version
    res = data
    for migration in migrate_path:
        logging.info(f'Applying migration: {v} -> {migration[0]}')
        res = migration[1](res)
        v = migration[0]

    return res
