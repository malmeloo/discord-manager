import shutil
import uuid
from datetime import datetime

from datastore import DataStore
from instance import DiscordInstance
from process import DiscordProcess, ProcessState


class InstanceManager:
    def __init__(self, ds: DataStore):
        self._ds = ds

    @property
    def instances(self):
        instances = self._ds.get_instances()
        for instance in instances:
            instance.manager = self

        return instances

    def create(self, name):
        instance = DiscordInstance(
            name=name,
            uuid=str(uuid.uuid4()),
            created_at=datetime.now()
        )
        instance.manager = self

        self._ds.save_instance(instance)

        return instance

    def delete(self, instance: DiscordInstance):
        try:
            shutil.rmtree(instance.base_dir)
        except FileNotFoundError:  # probably not initialized (yet), not an issue
            pass
        self._ds.delete_instance(instance.uuid)

    def find(self, query: str):
        exact_matches = []
        roughly_matches = []
        for instance in self.instances:
            if query.lower() == instance.name.lower() or query.lower() == instance.uuid:
                exact_matches.append(instance)
            elif query.lower() in instance.name.lower() or query.lower() in instance.uuid:
                roughly_matches.append(instance)

        # if we found exact matches then don't return the inexact ones
        return exact_matches or roughly_matches

    def start(self, instance: DiscordInstance):
        process = DiscordProcess(instance)
        process.start()

        return process
