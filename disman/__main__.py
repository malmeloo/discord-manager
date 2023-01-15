#!/usr/bin/env python3

import logging
from typing import Optional

import click

import updater
from datastore import DataStore
from instance import DiscordInstance, DiscordEdition
from instanceman import InstanceManager
import util

# prepare datastore + managers
ds = DataStore()
ds.open()
instance_man = InstanceManager(ds)


def _instance_search(query: str) -> Optional[DiscordInstance]:
    if len(query) < 3:
        click.echo('Error: query must be 3 or more characters long')
        raise click.Abort()

    click.echo(f'Searching for instances matching "{query}"\n')
    matches = instance_man.find(query)
    if not matches:
        click.echo('No matches found! Try being less specific.')
        raise click.Abort()
    elif len(matches) == 1:
        return matches[0]
    else:
        click.echo('Found more than one match:')
        for match in matches:
            click.echo(f'  - {match.name} ({match.uuid})')
        raise click.Abort()


def _parse_edition(edition: str):
    try:
        return DiscordEdition(edition.lower())
    except ValueError:
        click.echo(f'Error: "{edition}" is an invalid Discord edition. Options are "stable," "ptb" or "canary"')
        raise click.Abort()


@click.group()
@click.option('-v', '--verbose', is_flag=True)
def cli(verbose: bool):
    if verbose:
        logging.basicConfig(
            level=logging.DEBUG
        )
        logging.info('Enabled verbose logging')
    else:
        logging.basicConfig(
            level=logging.WARNING
        )


@cli.command(name='create')
@click.argument('name')
def create_instance(name: str):
    if len(name) < 3:
        click.echo('Error: instance name must be 3 or more characters long')
        return

    instance = instance_man.create(name)

    click.echo(f'New instance created: {instance.name}')
    click.echo(f'  - UUID:        {instance.uuid}')
    click.echo(f'  - Created at:  {instance.created_at}')
    click.echo('\nDon\'t forget to initialize this instance using the "upgrade" command.')


@cli.command(name='delete')
@click.argument('query')
@click.option('-y', '--yes', is_flag=True)
def delete_instance(query: str, yes=False):
    instance = _instance_search(query)

    click.echo(f'Deleting {instance.name} ({instance.uuid})')
    if not yes:
        click.confirm('Continue?', abort=True)
    instance.delete()


@cli.command(name='list')
def list_instances():
    instances = instance_man.instances

    for instance in instances:
        edition = instance.edition
        if edition is not None:
            edition = edition.friendly_name or 'Unknown'
        version = instance.version or 'Unknown'

        click.echo(f'Instance: {instance.name}')
        click.echo(f'  - Edition:     {edition}')
        click.echo(f'  - Version:     {version}')
        click.echo(f'  - Created at:  {util.utc_dt_to_relative_string(instance.created_at)}\n')

    click.echo(f'Total instances: {len(instances)}')


@cli.command(name='upgrade')
@click.argument('query')
@click.option('-e', '--edition')
@click.option('-y', '--yes', is_flag=True)
@click.option('--force-cross-upgrade', is_flag=True)
def upgrade_instance(query: str, edition, yes=False, force_cross_upgrade=False):
    instance = _instance_search(query)

    installed_edition = instance.edition
    if edition is None:
        # no preference, so try to resolve automatically
        # use installed edition if available, otherwise fall back to stable
        chosen_edition = installed_edition or DiscordEdition.STABLE
    else:
        # attempt to resolve wanted edition
        chosen_edition = _parse_edition(edition)

        if installed_edition and chosen_edition != installed_edition:  # this could really fuck up your installation
            if not force_cross_upgrade:
                click.echo(f'Error: user wants to upgrade to {chosen_edition.friendly_name} '
                           f'but {installed_edition.friendly_name} is installed!')
                return
            else:
                click.echo(f'WARNING: Cross-upgrading from {installed_edition.friendly_name} '
                           f'to {chosen_edition.friendly_name}. This is NOT recommended.\n')

    latest_version = updater.get_version(chosen_edition)
    click.echo(f'Upgrading "{instance.name}" to v{latest_version} - {chosen_edition.friendly_name}')
    if not yes:
        click.confirm('Continue?', abort=True)
        click.echo()

    downloader = updater.download_instance(chosen_edition, latest_version)

    update_file = None
    with click.progressbar(length=0, label=f'Downloading Discord - {chosen_edition.friendly_name}') as bar:
        for report in downloader:
            bar.length = report.total
            bar.update(report.current - bar.pos)

            if report.done:
                update_file = report.file

    if update_file is None:
        click.echo('Download failed!')
        return

    click.echo('Installing...')
    updater.install_update(instance, chosen_edition, update_file)
    click.echo('Done!')


@cli.command(name='start')
@click.argument('query')
def upgrade_instance(query: str):
    instance = _instance_search(query)
    if instance.edition is None:
        click.echo('Error: could not detect instance edition!')
        click.echo('You need to upgrade new instances after creating them.')

        return

    instance.start()


@cli.command(name='migrate')
@click.option('-y', '--yes', is_flag=True)
@click.argument('edition', required=False)
def migrate(edition: str, yes=False):
    installed_editions = util.get_installed_discord_editions()

    if edition is None:
        click.echo('Error: missing edition argument.\n')
        click.echo('These editions are currently installed:')
        for e in installed_editions:
            click.echo(f'- {e[0].friendly_name}')
        return

    # find path of edition to migrate, and also check whether the edition is currently installed
    chosen_edition = _parse_edition(edition)
    to_migrate = None
    for ins_edition in installed_editions:
        if chosen_edition == ins_edition[0]:
            to_migrate = ins_edition
            break
    if to_migrate is None:
        click.echo(f'Error: Discord {chosen_edition.friendly_name} '
                   f'is not currently installed, or no config dir exists.')
        return

    click.echo(f'Migrating currently installed Discord {chosen_edition.friendly_name}')
    if not yes:
        click.confirm('Continue?', abort=True)


if __name__ == '__main__':
    cli()
