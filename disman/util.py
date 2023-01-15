import os
import typing
from datetime import datetime
from typing import Iterable

from babel.dates import format_timedelta

if typing.TYPE_CHECKING:
    from instance import DiscordEdition


###############
# Directories #
###############

def get_system_config_dir():
    directory = os.environ.get('XDG_CONFIG_HOME', None)
    if directory is None:
        directory = os.path.join('/home', os.environ.get('USER'), '.config')

    return directory


def get_config_dir():
    return os.path.join(get_system_config_dir(), 'discord-manager/')


def get_instances_dir():
    return os.path.join(get_config_dir(), 'instances/')


def get_original_discord_config_dir(edition: 'DiscordEdition'):
    return os.path.join(get_system_config_dir(), edition.conf_dir_name)


#################
# Miscellaneous #
#################

def utc_dt_to_relative_string(dt: datetime):
    delta = dt - datetime.utcnow()
    return format_timedelta(delta, granularity='second', add_direction=True)


def find_executable_path(edition: 'DiscordEdition', files: Iterable[str]):
    for file in files:
        if os.path.basename(file) == edition.executable:
            return file

    return None


def get_installed_discord_editions():
    from instance import DiscordEdition

    conf_dir = get_system_config_dir()
    editions = []

    for edition in DiscordEdition:
        edition_dir = os.path.join(conf_dir, edition.conf_dir_name)
        if os.path.isdir(edition_dir) and not os.path.islink(edition_dir):
            editions.append((edition, edition_dir))

    return editions
