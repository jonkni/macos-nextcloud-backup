"""macOS menu bar application for backup management."""

import rumps
import subprocess
import threading
from pathlib import Path
from datetime import datetime

from mnb.config.manager import ConfigManager
from mnb.storage.metadata import MetadataDB


class BackupMenuBar(rumps.App):
    """macOS menu bar application for backup management."""

    def __init__(self):
        """Initialize menu bar app."""
        super(BackupMenuBar, self).__init__(
            "MNB",
            icon=self._get_icon_path(),
            quit_button='Quit'
        )

        # Load config and metadata
        self.config = None
        self.metadata = None
        self._load_config()

        # Build menu
        self.menu = [
            rumps.MenuItem('Status', callback=self.show_status),
            None,  # Separator
            rumps.MenuItem('Run Backup Now', callback=self.run_backup),
            rumps.MenuItem('View Snapshots', callback=self.view_snapshots),
            rumps.MenuItem('Restore Files...', callback=self.restore_files),
            None,
            rumps.MenuItem('View Logs', callback=self.view_logs),
            rumps.MenuItem('Preferences...', callback=self.show_preferences),
            None,
            rumps.MenuItem('Schedule: Loading...', callback=None),
        ]

        # Update status periodically
        self.update_status()

    def _get_icon_path(self):
        """Get path to menu bar icon."""
        # For now, use system icon
        # TODO: Create custom icon
        return None

    def _load_config(self):
        """Load configuration and metadata."""
        try:
            self.config = ConfigManager()
            if self.config.config_path.exists():
                self.config.load()

            db_path = Path.home() / '.config' / 'mnb' / 'metadata.db'
            if db_path.exists():
                self.metadata = MetadataDB(db_path)
        except Exception as e:
            print(f"Error loading config: {e}")

    def _run_command(self, args):
        """Run mnb command in background.

        Args:
            args: List of command arguments
        """
        try:
            subprocess.Popen(['mnb'] + args)
        except Exception as e:
            rumps.alert(
                title='Error',
                message=f'Failed to run command: {e}',
                ok='OK'
            )

    def _get_scheduler_status(self):
        """Get current scheduler status."""
        try:
            from mnb.utils.scheduler import LaunchdScheduler
            scheduler = LaunchdScheduler()
            return scheduler.get_status()
        except Exception:
            return {'installed': False, 'running': False}

    def update_status(self):
        """Update menu bar status."""
        # Update scheduler menu item
        scheduler_status = self._get_scheduler_status()

        for item in self.menu.values():
            if item and item.title.startswith('Schedule:'):
                if scheduler_status['installed']:
                    item.title = '✓ Schedule: Enabled'
                    item.set_callback(self.toggle_schedule)
                else:
                    item.title = '✗ Schedule: Disabled'
                    item.set_callback(self.toggle_schedule)
                break

        # Update icon based on last backup
        if self.metadata:
            try:
                latest = self.metadata.get_latest_snapshot()
                if latest:
                    # Could change icon color based on backup age
                    pass
            except Exception:
                pass

    @rumps.clicked('Status')
    def show_status(self, _):
        """Show backup status."""
        if not self.metadata:
            rumps.alert(
                title='No Backups',
                message='No backup configuration found. Run "mnb init" first.',
                ok='OK'
            )
            return

        try:
            stats = self.metadata.get_statistics()
            latest = stats.get('latest_snapshot')

            if not latest:
                rumps.alert(
                    title='No Backups',
                    message='No backups have been completed yet.',
                    ok='OK'
                )
                return

            # Format last backup time
            timestamp = datetime.fromisoformat(latest['timestamp'])
            time_ago = datetime.now() - timestamp
            hours = int(time_ago.total_seconds() / 3600)

            message = f"""Last Backup:
• Time: {timestamp.strftime('%Y-%m-%d %H:%M')} ({hours}h ago)
• Type: {latest['type']}
• Files: {latest['file_count']:,}
• Size: {self._format_size(latest['total_size'])}
• Status: {latest['status']}

Total Snapshots: {stats['total_snapshots']}"""

            rumps.alert(
                title='Backup Status',
                message=message,
                ok='OK'
            )

        except Exception as e:
            rumps.alert(
                title='Error',
                message=f'Failed to get status: {e}',
                ok='OK'
            )

    @rumps.clicked('Run Backup Now')
    def run_backup(self, _):
        """Run manual backup."""
        if rumps.alert(
            title='Run Backup',
            message='Start a backup now?\n\nThis may take several minutes.',
            ok='Run Backup',
            cancel='Cancel'
        ):
            rumps.notification(
                title='Backup Started',
                subtitle='Running backup...',
                message='Check logs for progress'
            )
            self._run_command(['backup'])

    @rumps.clicked('View Snapshots')
    def view_snapshots(self, _):
        """View list of snapshots."""
        if not self.metadata:
            rumps.alert(
                title='No Backups',
                message='No backup configuration found.',
                ok='OK'
            )
            return

        try:
            snapshots = self.metadata.list_snapshots(limit=10)

            if not snapshots:
                rumps.alert(
                    title='No Snapshots',
                    message='No backup snapshots found.',
                    ok='OK'
                )
                return

            # Build snapshot list
            snapshot_text = "Recent Snapshots:\n\n"
            for snap in snapshots[:5]:
                timestamp = datetime.fromisoformat(snap['timestamp'])
                size = self._format_size(snap['total_size'] or 0)
                snapshot_text += f"• {timestamp.strftime('%Y-%m-%d %H:%M')} - {snap['file_count']:,} files ({size})\n"

            snapshot_text += f"\nTotal: {len(snapshots)} snapshots"

            rumps.alert(
                title='Recent Snapshots',
                message=snapshot_text,
                ok='OK'
            )

        except Exception as e:
            rumps.alert(
                title='Error',
                message=f'Failed to list snapshots: {e}',
                ok='OK'
            )

    @rumps.clicked('Restore Files...')
    def restore_files(self, _):
        """Restore files from backup."""
        # TODO: Implement file browser for restore
        rumps.alert(
            title='Restore Files',
            message='File restore is coming soon!\n\nFor now, use the command line:\n\nmnb restore --snapshot <timestamp> --path <path>',
            ok='OK'
        )

    @rumps.clicked('View Logs')
    def view_logs(self, _):
        """Open log files."""
        log_path = Path.home() / 'Library' / 'Logs' / 'mnb-backup.log'

        if log_path.exists():
            # Open in Console.app
            subprocess.run(['open', '-a', 'Console', str(log_path)])
        else:
            rumps.alert(
                title='No Logs',
                message='No backup logs found yet.',
                ok='OK'
            )

    @rumps.clicked('Preferences...')
    def show_preferences(self, _):
        """Show preferences."""
        if not self.config or not self.config.config_path.exists():
            rumps.alert(
                title='No Configuration',
                message='No configuration found. Run "mnb init" first.',
                ok='OK'
            )
            return

        # Open config file in default editor
        subprocess.run(['open', '-t', str(self.config.config_path)])

    def toggle_schedule(self, sender):
        """Toggle automatic scheduling."""
        scheduler_status = self._get_scheduler_status()

        if scheduler_status['installed']:
            # Disable
            if rumps.alert(
                title='Disable Automatic Backups',
                message='Stop running automatic backups?',
                ok='Disable',
                cancel='Cancel'
            ):
                self._run_command(['schedule', '--disable'])
                sender.title = '✗ Schedule: Disabled'
                rumps.notification(
                    title='Schedule Disabled',
                    subtitle='Automatic backups stopped',
                    message='Use "Run Backup Now" for manual backups'
                )
        else:
            # Enable
            intervals = ['Hourly', 'Daily', 'Weekly']
            window = rumps.Window(
                title='Enable Automatic Backups',
                message='Choose backup interval:',
                default_text='hourly',
                ok='Enable',
                cancel='Cancel',
                dimensions=(280, 20)
            )
            window.add_button('Hourly')
            window.add_button('Daily')
            window.add_button('Weekly')

            response = window.run()
            if response.clicked:
                interval = response.text.lower()
                self._run_command(['schedule', '--interval', interval])
                sender.title = '✓ Schedule: Enabled'
                rumps.notification(
                    title='Schedule Enabled',
                    subtitle=f'{interval.capitalize()} automatic backups',
                    message='Backups will run automatically'
                )

    @staticmethod
    def _format_size(bytes_size):
        """Format bytes to human readable size."""
        if bytes_size is None or bytes_size == 0:
            return "0 B"
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.1f} PB"


def main():
    """Main entry point for GUI app."""
    BackupMenuBar().run()


if __name__ == '__main__':
    main()
