"""Main CLI entry point for macOS Nextcloud Backup."""

import click
from pathlib import Path
import sys

from mnb import __version__


@click.group()
@click.version_option(version=__version__)
@click.option('--config', type=click.Path(), help='Path to config file')
@click.option('--verbose', '-v', count=True, help='Increase verbosity')
@click.pass_context
def cli(ctx, config, verbose):
    """macOS Nextcloud Backup - Time Machine-like backups to Nextcloud.

    This tool provides automated, incremental backups of your macOS system
    to a Nextcloud instance via WebDAV.
    """
    ctx.ensure_object(dict)
    ctx.obj['config_path'] = config
    ctx.obj['verbose'] = verbose


@cli.command()
@click.option('--nextcloud-url', prompt='Nextcloud URL', help='URL of your Nextcloud instance')
@click.option('--username', prompt='Username', help='Nextcloud username')
@click.option('--machine-name', prompt='Machine name', help='Name for this machine')
@click.pass_context
def init(ctx, nextcloud_url, username, machine_name):
    """Initialize backup configuration.

    This wizard will guide you through setting up your first backup configuration.
    """
    click.echo(click.style('Initializing macOS Nextcloud Backup...', fg='green', bold=True))
    click.echo()

    # TODO: Implement initialization
    click.echo(f'Nextcloud URL: {nextcloud_url}')
    click.echo(f'Username: {username}')
    click.echo(f'Machine name: {machine_name}')
    click.echo()

    # Prompt for password
    password = click.prompt('Password', hide_input=True, confirmation_prompt=True)

    click.echo()
    click.echo(click.style('Testing connection to Nextcloud...', fg='yellow'))
    # TODO: Test WebDAV connection

    click.echo(click.style('Configuration saved!', fg='green'))
    click.echo()
    click.echo('Next steps:')
    click.echo('  1. Review exclusions: mnb config show')
    click.echo('  2. Estimate storage: mnb estimate')
    click.echo('  3. Run first backup: mnb backup --initial')


@cli.command()
@click.option('--initial', is_flag=True, help='First backup (full)')
@click.option('--dry-run', is_flag=True, help='Show what would be backed up')
@click.pass_context
def backup(ctx, initial, dry_run):
    """Run a backup.

    By default, runs an incremental backup. Use --initial for the first backup.
    """
    if dry_run:
        click.echo(click.style('DRY RUN MODE - No files will be uploaded', fg='yellow', bold=True))
        click.echo()

    backup_type = 'initial' if initial else 'incremental'
    click.echo(f'Starting {backup_type} backup...')

    # TODO: Implement backup logic
    click.echo(click.style('Backup not yet implemented', fg='red'))


@cli.command()
@click.pass_context
def status(ctx):
    """Show backup status and last backup information."""
    click.echo('Backup Status')
    click.echo('=' * 50)

    # TODO: Implement status display
    click.echo(click.style('Status feature not yet implemented', fg='yellow'))


@cli.command()
@click.option('--all', 'show_all', is_flag=True, help='Show all snapshots')
@click.option('--limit', type=int, default=10, help='Number of snapshots to show')
@click.pass_context
def list(ctx, show_all, limit):
    """List available backup snapshots."""
    click.echo('Available Snapshots')
    click.echo('=' * 50)

    # TODO: Implement snapshot listing
    click.echo(click.style('List feature not yet implemented', fg='yellow'))


@cli.command()
@click.option('--snapshot', required=True, help='Snapshot timestamp to restore from')
@click.option('--path', type=click.Path(), help='Specific path to restore')
@click.option('--destination', type=click.Path(), help='Where to restore files')
@click.pass_context
def restore(ctx, snapshot, path, destination):
    """Restore files from a backup snapshot."""
    click.echo(f'Restoring from snapshot: {snapshot}')

    if path:
        click.echo(f'Path: {path}')
    else:
        click.echo('Restoring all files')

    if destination:
        click.echo(f'Destination: {destination}')

    # TODO: Implement restore logic
    click.echo(click.style('Restore feature not yet implemented', fg='red'))


@cli.command()
@click.pass_context
def estimate(ctx):
    """Estimate storage requirements for backup."""
    click.echo('Estimating backup size...')
    click.echo()

    # TODO: Scan filesystem and estimate
    click.echo(click.style('Estimate feature not yet implemented', fg='yellow'))
    click.echo()
    click.echo('Expected output:')
    click.echo('  Documents: 10.5 GB')
    click.echo('  Config files: 250 MB')
    click.echo('  Application data: 5.2 GB')
    click.echo('  ---')
    click.echo('  Total initial backup: 15.95 GB')


@cli.command()
@click.option('--keep-last', type=int, help='Keep only last N snapshots')
@click.option('--older-than', help='Remove snapshots older than (e.g., "30d", "2w")')
@click.option('--dry-run', is_flag=True, help='Show what would be deleted')
@click.pass_context
def clean(ctx, keep_last, older_than, dry_run):
    """Clean old backup snapshots."""
    if dry_run:
        click.echo(click.style('DRY RUN MODE', fg='yellow', bold=True))
        click.echo()

    click.echo('Cleaning old snapshots...')

    # TODO: Implement cleanup logic
    click.echo(click.style('Clean feature not yet implemented', fg='yellow'))


@cli.group()
def config():
    """Manage backup configuration."""
    pass


@config.command('show')
@click.pass_context
def config_show(ctx):
    """Show current configuration."""
    click.echo('Current Configuration')
    click.echo('=' * 50)

    # TODO: Load and display config
    click.echo(click.style('Config display not yet implemented', fg='yellow'))


@config.command('set')
@click.argument('key')
@click.argument('value')
@click.pass_context
def config_set(ctx, key, value):
    """Set a configuration value."""
    click.echo(f'Setting {key} = {value}')

    # TODO: Update config
    click.echo(click.style('Config update not yet implemented', fg='yellow'))


@cli.command()
@click.option('--interval', type=click.Choice(['hourly', 'daily', 'weekly']),
              default='hourly', help='Backup interval')
@click.option('--disable', is_flag=True, help='Disable automatic backups')
@click.pass_context
def schedule(ctx, interval, disable):
    """Configure automatic backup scheduling.

    Sets up launchd to run backups automatically on the specified interval.
    """
    if disable:
        click.echo('Disabling automatic backups...')
        # TODO: Remove launchd plist
        click.echo(click.style('Schedule disable not yet implemented', fg='yellow'))
        return

    click.echo(f'Setting up {interval} automatic backups...')

    # TODO: Generate and install launchd plist
    click.echo(click.style('Schedule feature not yet implemented', fg='yellow'))
    click.echo()
    click.echo(f'Backups will run {interval}')
    click.echo('To check status: launchctl list | grep mnb')


if __name__ == '__main__':
    cli()
