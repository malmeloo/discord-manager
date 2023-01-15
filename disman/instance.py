import os
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from util import get_instances_dir
import json

if TYPE_CHECKING:
    from instanceman import InstanceManager


class DiscordEdition(Enum):
    STABLE = ('stable', 'Stable', 'discord', 'Discord')
    PTB = ('ptb', 'PTB', 'discordptb', 'DiscordPTB')
    CANARY = ('canary', 'Canary', 'discordcanary', 'DiscordCanary')

    def __new__(cls, code_name, friendly_name, conf_dir_name, executable):
        """Ensures that we can find the enums by their code names"""
        obj = object.__new__(cls)
        obj._value_ = code_name

        obj.code_name = code_name
        obj.friendly_name = friendly_name
        obj.conf_dir_name = conf_dir_name
        obj.executable = executable

        return obj


class DiscordInstance:
    def __init__(self, name: str, uuid: str, created_at: datetime):
        self._manager: Optional['InstanceManager'] = None

        self.name = name
        self._uuid = uuid
        self.created_at = created_at

    def _build_info(self) -> dict:
        target = os.path.join(self.app_dir, 'resources/build_info.json')
        try:
            with open(target, 'r') as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    @property
    def uuid(self):
        return self._uuid

    @property
    def manager(self):
        return self._manager

    @manager.setter
    def manager(self, man: 'InstanceManager'):
        self._manager = man

    @property
    def base_dir(self):
        return os.path.join(get_instances_dir(), self.uuid)

    @property
    def app_dir(self):
        return os.path.join(self.base_dir, 'app/')

    @property
    def data_dir(self):
        return os.path.join(self.base_dir, 'data/')

    @property
    def edition(self):
        try:
            return DiscordEdition(self._build_info().get('releaseChannel'))
        except ValueError:  # no build info found or unknown release
            return None

    @property
    def version(self):
        return self._build_info().get('version', None)

    ####################
    #  Helper methods  #
    ####################

    def delete(self):
        self._manager.delete(self)

    def start(self):
        self._manager.start(self)
