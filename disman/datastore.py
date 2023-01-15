import json
import logging
import os
from datetime import datetime

import migrations
import util
from instance import DiscordInstance

logging.getLogger(__name__)


def _get_default_path():
    return os.path.join(util.get_config_dir(), 'config.json')


class DataStore:
    def __init__(self, path=None):
        self._path = path or _get_default_path()

        self._data = {}

    def save(self):
        logging.debug('Saving datastore to disk')
        with open(self._path, 'w+') as file:
            json.dump(self._data, file)

    def open(self):
        os.makedirs(os.path.dirname(self._path), exist_ok=True)

        try:
            with open(self._path, 'r') as file:
                data = json.load(file)

            if migrations.should_migrate(data):
                data = migrations.migrate(data)
        except FileNotFoundError:
            logging.info('Creating config file')
            data = migrations.migrate({}, force=True)

        self._data = data
        self.save()

    ##############################
    #  Discord instance methods  #
    ##############################

    def get_instances(self) -> list[DiscordInstance]:
        logging.info('Getting instances')
        try:
            instances_data = self._data['instances'].values()
        except KeyError:
            logging.warning('Instances not found in config file')
            return []

        instances = [
            DiscordInstance(
                name=ins_data['name'],
                uuid=ins_data['uuid'],
                created_at=datetime.utcfromtimestamp(ins_data['created_at'])
            )
            for ins_data in instances_data
        ]
        return sorted(instances, key=lambda i: i.created_at)

    def save_instance(self, instance: DiscordInstance):
        logging.info('Saving instance to datastore')

        instances = self._data.get('instances', {})
        instances[instance.uuid] = {
            'name': instance.name,
            'uuid': instance.uuid,
            'created_at': instance.created_at.timestamp()
        }
        self._data['instances'] = instances

        self.save()

    def delete_instance(self, uuid):
        try:
            del self._data['instances'][uuid]
        except KeyError:
            logging.error(f'Could not delete instance (not found): {uuid}')
            raise RuntimeError(f'Instance "{uuid}" not found')

        self.save()
