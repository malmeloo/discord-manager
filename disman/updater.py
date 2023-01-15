import io
import logging
import os
import tarfile
from dataclasses import dataclass

import httpx

import util
from instance import DiscordInstance, DiscordEdition

logging.getLogger(__name__)

API_ENDPOINT = 'https://discord.com/api'
DL_ENDPOINTS = {
    DiscordEdition.STABLE: 'https://dl.discordapp.net/apps/{plat}/{v}/discord-{v}.tar.gz',
    DiscordEdition.PTB: 'https://dl-ptb.discordapp.net/apps/{plat}/{v}/discord-ptb-{v}.tar.gz',
    DiscordEdition.CANARY: 'https://dl-canary.discordapp.net/apps/{plat}/{v}/discord-canary-{v}.tar.gz'
}

client = httpx.Client()


@dataclass()
class DownloadStatusReport:
    current: int  # in bytes
    total: int  # in bytes
    file: io.BytesIO
    done: bool


class UpdateError(Exception):
    pass


def get_version(edition=DiscordEdition.STABLE) -> str:
    """
    Gets the latest Discord version according to Discord's servers.
    We do this by pretending as if we're running version 0.0.0 so Discord
    will serve us the latest client version.

    :return: version as str
    """
    logging.info('Getting latest client version')
    r = client.get(f'{API_ENDPOINT}/updates/{edition.code_name}', params={
        'platform': 'linux',
        'version': '0.0.0'
    })
    if r.status_code != 200:
        raise UpdateError(f'Unexpected response while checking for latest version: {r}')

    try:
        data = r.json()
        return data['name']
    except httpx.DecodingError:
        raise UpdateError(f'Could not parse API response: {r.text}')
    except KeyError:
        raise UpdateError(f'Could not find version in API response: {r.text}')


def download_instance(edition: DiscordEdition, version=None):
    url = DL_ENDPOINTS.get(edition, None)
    if url is None:
        raise UpdateError(f'Could not find download URL for edition: {edition}')
    url = url.format(plat='linux', v=version)

    # use latest version if not specified
    if version is None:
        version = get_version()

    # download tarball
    logging.info(f'Downloading archive: {url}')
    buf = io.BytesIO()
    downloaded = 0

    with client.stream('GET', url) as r:
        if r.status_code == 404:
            raise UpdateError(f'Could not find version on server: {edition}-{version}')
        elif r.status_code != 200:
            raise UpdateError(f'Unknown HTTP error while fetching client tarball: {r.status_code}')

        total_size = int(r.headers['Content-Length'])
        for data in r.iter_bytes():
            buf.write(data)
            downloaded += len(data)
            yield DownloadStatusReport(downloaded, total_size, buf, False)

    buf.seek(0)
    yield DownloadStatusReport(downloaded, total_size, buf, True)


def install_update(instance: 'DiscordInstance', edition: DiscordEdition, update_file: io.BytesIO):
    logging.info(f'Installing Discord to {instance.app_dir}')
    os.makedirs(instance.app_dir, exist_ok=True)

    with tarfile.open(fileobj=update_file, mode='r:gz') as archive:
        members = archive.getmembers()
        executable = util.find_executable_path(edition, (m.path for m in members if m.isfile()))
        common_path = os.path.dirname(executable)

        for member in members:
            if not member.isfile():  # we only need the files
                continue

            # calculate dest directory and create required dirs
            dest = os.path.join(
                instance.app_dir,
                os.path.relpath(member.path, common_path)
            )
            os.makedirs(os.path.dirname(dest), exist_ok=True)

            # extract member to dest and set permissions
            file = archive.extractfile(member)
            with open(dest, 'wb+') as target:
                target.write(file.read())
            os.chmod(dest, member.mode)
