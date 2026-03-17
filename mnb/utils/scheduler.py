"""Scheduler for automatic backups using launchd on macOS."""

import os
import shutil
from pathlib import Path
from typing import Optional


class LaunchdScheduler:
    """Manages launchd-based scheduling for automatic backups."""

    LABEL = "com.macos-nextcloud-backup.mnb"
    PLIST_FILENAME = f"{LABEL}.plist"

    def __init__(self):
        """Initialize scheduler."""
        self.user_agents_dir = Path.home() / "Library" / "LaunchAgents"
        self.plist_path = self.user_agents_dir / self.PLIST_FILENAME

    def get_interval_seconds(self, interval: str) -> int:
        """Convert interval name to seconds.

        Args:
            interval: 'hourly', 'daily', or 'weekly'

        Returns:
            Number of seconds
        """
        intervals = {
            'hourly': 3600,  # 1 hour
            'daily': 86400,  # 24 hours
            'weekly': 604800,  # 7 days
        }
        return intervals.get(interval, 3600)

    def generate_plist(self, interval: str = 'hourly',
                      mnb_path: Optional[str] = None) -> str:
        """Generate launchd plist XML.

        Args:
            interval: Backup interval ('hourly', 'daily', 'weekly')
            mnb_path: Path to mnb executable (auto-detected if None)

        Returns:
            XML content for plist file
        """
        if mnb_path is None:
            mnb_path = shutil.which('mnb')
            if not mnb_path:
                raise RuntimeError("Could not find mnb executable")

        interval_seconds = self.get_interval_seconds(interval)

        # Get user's home directory for log files
        home_dir = str(Path.home())
        log_dir = f"{home_dir}/Library/Logs"

        plist = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{self.LABEL}</string>

    <key>ProgramArguments</key>
    <array>
        <string>{mnb_path}</string>
        <string>backup</string>
    </array>

    <key>StartInterval</key>
    <integer>{interval_seconds}</integer>

    <key>RunAtLoad</key>
    <false/>

    <key>StandardOutPath</key>
    <string>{log_dir}/mnb-backup.log</string>

    <key>StandardErrorPath</key>
    <string>{log_dir}/mnb-backup-error.log</string>

    <key>ProcessType</key>
    <string>Background</string>

    <key>Nice</key>
    <integer>10</integer>
</dict>
</plist>
'''
        return plist

    def install(self, interval: str = 'hourly') -> bool:
        """Install scheduled backup.

        Args:
            interval: Backup interval

        Returns:
            True if successful
        """
        # Create LaunchAgents directory if it doesn't exist
        self.user_agents_dir.mkdir(parents=True, exist_ok=True)

        # Generate plist
        plist_content = self.generate_plist(interval)

        # Write plist file
        with open(self.plist_path, 'w') as f:
            f.write(plist_content)

        # Load the agent
        os.system(f"launchctl load {self.plist_path}")

        return True

    def uninstall(self) -> bool:
        """Uninstall scheduled backup.

        Returns:
            True if successful
        """
        if not self.plist_path.exists():
            return True  # Already uninstalled

        # Unload the agent
        os.system(f"launchctl unload {self.plist_path}")

        # Remove plist file
        self.plist_path.unlink()

        return True

    def is_installed(self) -> bool:
        """Check if scheduled backup is installed.

        Returns:
            True if installed
        """
        return self.plist_path.exists()

    def get_status(self) -> dict:
        """Get scheduler status.

        Returns:
            Dictionary with status information
        """
        if not self.is_installed():
            return {
                'installed': False,
                'running': False,
            }

        # Check if loaded in launchctl
        result = os.popen(f"launchctl list | grep {self.LABEL}").read()
        running = bool(result.strip())

        return {
            'installed': True,
            'running': running,
            'plist_path': str(self.plist_path),
        }

    def start(self) -> bool:
        """Start the scheduled backup (load agent).

        Returns:
            True if successful
        """
        if not self.is_installed():
            return False

        os.system(f"launchctl load {self.plist_path}")
        return True

    def stop(self) -> bool:
        """Stop the scheduled backup (unload agent).

        Returns:
            True if successful
        """
        if not self.is_installed():
            return True

        os.system(f"launchctl unload {self.plist_path}")
        return True
