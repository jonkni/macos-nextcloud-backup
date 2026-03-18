"""Main CLI entry point for macOS Nextcloud Backup."""

import click
from pathlib import Path
import sys
import logging
from datetime import datetime

from mnb import __version__
from mnb.config.manager import ConfigManager
from mnb.core.backup_engine import BackupEngine
from mnb.storage.webdav import WebDAVClient


def _load_config(config_path=None):
    """Load configuration or exit if not found."""
    config_mgr = ConfigManager(Path(config_path) if config_path else None)

    if not config_mgr.config_path.exists():
        click.echo(click.style('Error: Configuration not found', fg='red'))
        click.echo(f'Expected at: {config_mgr.config_path}')
        click.echo()
        click.echo('Initialize configuration with: mnb init')
        sys.exit(1)

    try:
        config_mgr.load()
    except Exception as e:
        click.echo(click.style(f'Error loading config: {e}', fg='red'))
        sys.exit(1)

    return config_mgr


def _setup_logging(verbose=0):
    """Setup logging based on verbosity."""
    level = logging.WARNING
    if verbose == 1:
        level = logging.INFO
    elif verbose >= 2:
        level = logging.DEBUG

    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def _log(message, **kwargs):
    """Output message with timestamp prefix.

    Args:
        message: Message to output
        **kwargs: Additional arguments passed to click.echo()
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    click.echo(f"{timestamp} {message}", **kwargs)


def _format_size(bytes_size):
    """Format bytes to human readable size."""
    if bytes_size is None:
        return "Unknown"
    if bytes_size == 0:
        return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} PB"


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
    _setup_logging(verbose)


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

    click.echo(f'Nextcloud URL: {nextcloud_url}')
    click.echo(f'Username: {username}')
    click.echo(f'Machine name: {machine_name}')
    click.echo()

    # Prompt for password with 2FA warning
    click.echo(click.style('Note:', fg='cyan') + ' If 2FA is enabled, use an app password (not your regular password)')
    click.echo('Create one at: Settings → Security → Devices & sessions')
    click.echo()
    password = click.prompt('Password (or app password)', hide_input=True, confirmation_prompt=True)

    click.echo()
    click.echo(click.style('Testing connection to Nextcloud...', fg='yellow'))

    # Test WebDAV connection
    try:
        webdav = WebDAVClient(
            base_url=nextcloud_url,
            username=username,
            password=password
        )

        if not webdav.test_connection():
            click.echo()
            click.echo(click.style('✗ Connection failed', fg='red', bold=True))
            click.echo()
            click.echo('Possible causes:')
            click.echo('  1. ' + click.style('Two-Factor Authentication (2FA) enabled', fg='yellow'))
            click.echo('     → You must use an app password, not your regular password')
            click.echo('     → Create one at: Settings → Security → Devices & sessions')
            click.echo()
            click.echo('  2. Incorrect URL, username, or password')
            click.echo('  3. Network connectivity issues')
            click.echo('  4. WebDAV not enabled on Nextcloud')
            click.echo()
            click.echo('For detailed setup instructions, see: QUICKSTART.md')
            sys.exit(1)

        click.echo(click.style('✓ Connection successful!', fg='green'))
    except Exception as e:
        click.echo()
        click.echo(click.style(f'✗ Error: {e}', fg='red'))
        click.echo()
        click.echo('If 2FA is enabled, you need an app password.')
        click.echo('See QUICKSTART.md for instructions.')
        sys.exit(1)

    # Create default configuration
    config_mgr = ConfigManager()
    default_config = ConfigManager.create_default_config(
        nextcloud_url=nextcloud_url,
        username=username,
        machine_name=machine_name
    )

    # Save configuration (this also saves password to keychain)
    default_config['nextcloud']['password'] = password
    config_mgr.save(default_config)

    click.echo()
    click.echo(click.style('Configuration saved!', fg='green'))
    click.echo(f'Config file: {config_mgr.config_path}')
    click.echo(f'Password stored in macOS Keychain')
    click.echo()
    click.echo('Next steps:')
    click.echo('  1. Review exclusions: mnb config show')
    click.echo('  2. Estimate storage: mnb estimate')
    click.echo('  3. Run first backup: mnb backup --initial')


@cli.command()
@click.option('--initial', is_flag=True, help='First backup (full)')
@click.option('--dry-run', is_flag=True, help='Show what would be backed up')
@click.option('--force', is_flag=True, help='Force backup even if another is running')
@click.pass_context
def backup(ctx, initial, dry_run, force):
    """Run a backup.

    By default, runs an incremental backup. Use --initial for the first backup.
    """
    from mnb.utils.lock import BackupLock
    from mnb.utils.network import check_nextcloud_connectivity

    if dry_run:
        click.echo(click.style('DRY RUN MODE - No files will be uploaded', fg='yellow', bold=True))
        click.echo()

    backup_type = 'initial' if initial else 'incremental'
    _log(f'Starting {backup_type} backup...')
    click.echo()

    # Check for existing backup (unless forced or dry-run)
    if not force and not dry_run:
        lock = BackupLock()
        if lock.is_locked():
            lock_info = lock.get_lock_info()
            click.echo(click.style('⚠ Another backup is already running', fg='yellow', bold=True))
            if lock_info:
                click.echo(f"PID: {lock_info['pid']}")
                click.echo(f"Command: {lock_info['cmdline']}")
            click.echo()
            click.echo('Wait for it to complete, or use --force to override')
            sys.exit(1)

    # Load configuration
    config = _load_config(ctx.obj.get('config_path'))

    # Check network connectivity (unless dry-run)
    if not dry_run:
        _log('Checking network connectivity...')
        connectivity = check_nextcloud_connectivity(
            config.get('nextcloud.url'),
            timeout=5
        )

        if not connectivity['network_available']:
            click.echo(click.style('✗ No network connection', fg='red'))
            click.echo()
            click.echo('Cannot run backup without network access.')
            click.echo('Connect to network and try again.')
            sys.exit(1)

        if not connectivity['nextcloud_reachable']:
            click.echo(click.style(f"✗ Cannot reach Nextcloud", fg='red'))
            click.echo(f"URL: {config.get('nextcloud.url')}")
            click.echo()
            click.echo('Possible causes:')
            click.echo('  - VPN required but not connected')
            click.echo('  - Nextcloud server is down')
            click.echo('  - Firewall blocking access')
            sys.exit(1)

        _log(click.style('✓ Network OK', fg='green'))

    # Create backup engine
    engine = BackupEngine(config)

    # Test connection first
    _log('Testing connection...')
    if not engine.test_connection():
        _log(click.style('Error: Could not connect to Nextcloud', fg='red'))
        sys.exit(1)

    _log(click.style('✓ Connected', fg='green'))
    click.echo()

    # Progress tracking
    from tqdm import tqdm
    pbar = None
    current_status = ""

    # Only show progress bars when running in an interactive terminal
    use_progress_bar = sys.stdout.isatty()

    def progress_callback(status, current, total):
        nonlocal pbar, current_status

        if status != current_status:
            if pbar:
                pbar.close()

            # Only log status changes that aren't per-file updates
            # (i.e., log "Scanning files..." but not "Uploading file123.py")
            if not status.startswith("Uploading "):
                _log(status)

            # Always show status in interactive mode
            if use_progress_bar:
                click.echo(status)

            current_status = status

            if total > 0 and use_progress_bar:
                pbar = tqdm(total=total, unit='file', file=sys.stdout)

        if pbar and total > 0:
            pbar.update(current - pbar.n)

    # Acquire lock (unless dry-run or forced)
    lock = None if (dry_run or force) else BackupLock()

    try:
        # Acquire lock for real backups
        if lock:
            lock.acquire()

        # Run backup
        result = engine.run_backup(
            initial=initial,
            dry_run=dry_run,
            progress_callback=progress_callback
        )

        if pbar:
            pbar.close()

        click.echo()
        _log(click.style('Backup completed successfully!', fg='green', bold=True))
        click.echo()
        _log(f"Snapshot ID: {result['snapshot_id']}")
        _log(f"Timestamp: {result['timestamp']}")
        _log(f"Files uploaded: {result['files_uploaded']}")
        _log(f"Files unchanged: {result['files_unchanged']}")
        _log(f"Total files: {result['total_files']}")
        _log(f"Uploaded size: {_format_size(result['uploaded_size'])}")
        _log(f"Total size: {_format_size(result['total_size'])}")

        if dry_run:
            click.echo()
            click.echo(click.style('This was a dry run - no files were uploaded', fg='yellow'))

    except Exception as e:
        if pbar:
            pbar.close()
        click.echo()
        _log(click.style(f'Backup failed: {e}', fg='red'))
        sys.exit(1)
    finally:
        # Release lock
        if lock:
            lock.release()


@cli.command()
@click.pass_context
def status(ctx):
    """Show backup status and last backup information."""
    click.echo('Backup Status')
    click.echo('=' * 50)
    click.echo()

    # Load configuration
    config = _load_config(ctx.obj.get('config_path'))

    # Create backup engine
    engine = BackupEngine(config)

    # Get statistics
    stats = engine.get_statistics()

    click.echo(f"Machine: {config.get_machine_name()}")
    click.echo(f"Nextcloud: {config.get('nextcloud.url')}")
    click.echo(f"Total snapshots: {stats['total_snapshots']}")
    click.echo()

    latest = stats.get('latest_snapshot')
    if latest:
        click.echo('Latest Backup:')
        click.echo(f"  Timestamp: {latest['timestamp']}")
        click.echo(f"  Type: {latest['type']}")
        click.echo(f"  Files: {latest['file_count']}")
        click.echo(f"  Size: {_format_size(latest['total_size'])}")
        click.echo(f"  Status: {latest['status']}")

        # Calculate time since backup
        from datetime import datetime
        try:
            backup_time = datetime.fromisoformat(latest['timestamp'])
            time_diff = datetime.now() - backup_time
            hours = int(time_diff.total_seconds() / 3600)
            click.echo(f"  Age: {hours} hours ago")
        except:
            pass
    else:
        click.echo(click.style('No backups found', fg='yellow'))
        click.echo()
        click.echo('Run your first backup with: mnb backup --initial')


@cli.command()
@click.option('--all', 'show_all', is_flag=True, help='Show all snapshots')
@click.option('--limit', type=int, default=10, help='Number of snapshots to show')
@click.pass_context
def list(ctx, show_all, limit):
    """List available backup snapshots."""
    click.echo('Available Snapshots')
    click.echo('=' * 50)
    click.echo()

    # Load configuration
    config = _load_config(ctx.obj.get('config_path'))

    # Create backup engine
    engine = BackupEngine(config)

    # Get snapshots
    if show_all:
        limit = 1000

    snapshots = engine.list_snapshots(limit=limit)

    if not snapshots:
        click.echo(click.style('No snapshots found', fg='yellow'))
        return

    # Display snapshots
    for snapshot in snapshots:
        status_color = 'green' if snapshot['status'] == 'completed' else 'red'
        click.echo(
            f"{click.style(snapshot['timestamp'], fg='cyan')} "
            f"[{click.style(snapshot['type'], fg='yellow')}] "
            f"- {snapshot['file_count']} files, "
            f"{_format_size(snapshot['total_size'])} "
            f"({click.style(snapshot['status'], fg=status_color)})"
        )

    click.echo()
    click.echo(f"Showing {len(snapshots)} snapshots")


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
    click.echo('This may take a few minutes...')
    click.echo()

    # Load configuration
    config = _load_config(ctx.obj.get('config_path'))

    # Create backup engine
    engine = BackupEngine(config)

    # Progress tracking
    from tqdm import tqdm
    pbar = tqdm(unit=' files', unit_scale=True)

    def progress_callback(files_scanned, total_size):
        pbar.update(files_scanned - pbar.n)
        pbar.set_postfix({'size': _format_size(total_size)})

    try:
        result = engine.estimate_backup_size(progress_callback)
        pbar.close()

        click.echo()
        click.echo(click.style('Estimation complete!', fg='green', bold=True))
        click.echo()
        click.echo(f"Total files: {result['file_count']:,}")
        click.echo(f"Total size: {_format_size(result['total_size'])}")
        click.echo()

        # Compare with Nextcloud quota
        total_gb = result['total_size'] / (1024 ** 3)
        click.echo('Storage recommendations:')
        click.echo(f"  Minimum: {total_gb:.1f} GB (initial backup only)")
        click.echo(f"  Recommended: {total_gb * 1.5:.1f} GB (with some growth)")
        click.echo(f"  Ideal: {total_gb * 2:.1f} GB (comfortable margins)")

        # Your Nextcloud storage
        click.echo()
        click.echo(f"Your Nextcloud: 100 GB")
        if total_gb < 30:
            click.echo(click.style('✓ Storage should be sufficient', fg='green'))
        elif total_gb < 50:
            click.echo(click.style('⚠ Storage may be tight - monitor closely', fg='yellow'))
        else:
            click.echo(click.style('⚠ May need more storage', fg='red'))

    except Exception as e:
        pbar.close()
        click.echo()
        click.echo(click.style(f'Estimation failed: {e}', fg='red'))
        sys.exit(1)


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
    click.echo()

    # Load configuration
    config = _load_config(ctx.obj.get('config_path'))

    # Create backup engine
    engine = BackupEngine(config)

    try:
        result = engine.clean_old_snapshots(
            keep_count=keep_last,
            dry_run=dry_run
        )

        click.echo(click.style(f"Deleted {result['deleted_count']} snapshots", fg='green'))
        click.echo(f"Kept {result['kept_count']} snapshots")

        if dry_run:
            click.echo()
            click.echo(click.style('This was a dry run - no snapshots were deleted', fg='yellow'))

    except Exception as e:
        click.echo(click.style(f'Clean failed: {e}', fg='red'))
        sys.exit(1)


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
    click.echo()

    # Load configuration
    config_mgr = _load_config(ctx.obj.get('config_path'))

    # Display configuration (pretty print)
    import yaml
    config_display = config_mgr.config.copy()

    # Don't show password
    if 'nextcloud' in config_display and 'password' in config_display['nextcloud']:
        config_display['nextcloud']['password'] = '****** (in Keychain)'

    click.echo(yaml.dump(config_display, default_flow_style=False, sort_keys=False))
    click.echo()
    click.echo(f"Config file: {config_mgr.config_path}")


@config.command('set')
@click.argument('key')
@click.argument('value')
@click.pass_context
def config_set(ctx, key, value):
    """Set a configuration value."""
    # Load configuration
    config_mgr = _load_config(ctx.obj.get('config_path'))

    # Set value
    try:
        # Try to parse as number or boolean
        if value.lower() == 'true':
            value = True
        elif value.lower() == 'false':
            value = False
        elif value.isdigit():
            value = int(value)
        elif value.replace('.', '', 1).isdigit():
            value = float(value)

        config_mgr.set(key, value)
        config_mgr.save()

        click.echo(click.style(f'✓ Set {key} = {value}', fg='green'))

    except Exception as e:
        click.echo(click.style(f'Error: {e}', fg='red'))
        sys.exit(1)


@cli.command()
@click.option('--interval', type=click.Choice(['hourly', 'daily', 'weekly']),
              default='hourly', help='Backup interval')
@click.option('--disable', is_flag=True, help='Disable automatic backups')
@click.option('--status', 'show_status', is_flag=True, help='Show scheduler status')
@click.pass_context
def schedule(ctx, interval, disable, show_status):
    """Configure automatic backup scheduling.

    Sets up launchd to run backups automatically on the specified interval.
    """
    from mnb.utils.scheduler import LaunchdScheduler

    scheduler = LaunchdScheduler()

    # Show status
    if show_status:
        status = scheduler.get_status()
        click.echo('Scheduler Status')
        click.echo('=' * 50)
        click.echo()

        if status['installed']:
            click.echo(click.style('✓ Automatic backups: ENABLED', fg='green'))
            click.echo(f"Running: {'Yes' if status['running'] else 'No'}")
            click.echo(f"Plist: {status['plist_path']}")
            click.echo()
            click.echo('Logs:')
            click.echo(f"  Output: ~/Library/Logs/mnb-backup.log")
            click.echo(f"  Errors: ~/Library/Logs/mnb-backup-error.log")
        else:
            click.echo(click.style('✗ Automatic backups: DISABLED', fg='yellow'))
            click.echo()
            click.echo('Enable with: mnb schedule --interval hourly')

        return

    # Disable scheduling
    if disable:
        click.echo('Disabling automatic backups...')

        if not scheduler.is_installed():
            click.echo(click.style('Automatic backups are not enabled', fg='yellow'))
            return

        try:
            scheduler.uninstall()
            click.echo(click.style('✓ Automatic backups disabled', fg='green'))
            click.echo()
            click.echo('Re-enable with: mnb schedule --interval hourly')
        except Exception as e:
            click.echo(click.style(f'Error: {e}', fg='red'))
            sys.exit(1)

        return

    # Enable scheduling
    click.echo(f'Setting up {interval} automatic backups...')
    click.echo()

    # Check if configuration exists
    config_path = Path.home() / '.config' / 'mnb' / 'config.yml'
    if not config_path.exists():
        click.echo(click.style('Error: Configuration not found', fg='red'))
        click.echo('Run "mnb init" first to set up your backup')
        sys.exit(1)

    try:
        # Install scheduler
        scheduler.install(interval)

        click.echo(click.style('✓ Automatic backups enabled!', fg='green', bold=True))
        click.echo()
        click.echo(f'Backups will run every {interval}')
        click.echo()
        click.echo('Details:')
        click.echo(f'  Interval: {interval}')
        click.echo(f'  Command: mnb backup')
        click.echo(f'  Logs: ~/Library/Logs/mnb-backup.log')
        click.echo()
        click.echo('Useful commands:')
        click.echo('  mnb schedule --status     # Check status')
        click.echo('  mnb schedule --disable    # Disable scheduling')
        click.echo('  tail -f ~/Library/Logs/mnb-backup.log  # Watch logs')
        click.echo('  launchctl list | grep mnb # Check launchd status')

    except Exception as e:
        click.echo(click.style(f'Error setting up scheduler: {e}', fg='red'))
        sys.exit(1)


if __name__ == '__main__':
    cli()
