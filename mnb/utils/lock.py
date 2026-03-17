"""Lock file management to prevent concurrent backups."""

import os
import time
import psutil
from pathlib import Path
from typing import Optional


class BackupLock:
    """Manages lock file to prevent concurrent backup processes."""

    def __init__(self, lock_dir: Optional[Path] = None):
        """Initialize lock manager.

        Args:
            lock_dir: Directory for lock file (default: ~/.config/mnb/)
        """
        if lock_dir is None:
            lock_dir = Path.home() / '.config' / 'mnb'

        lock_dir.mkdir(parents=True, exist_ok=True)
        self.lock_file = lock_dir / 'backup.lock'

    def acquire(self, timeout: int = 0) -> bool:
        """Acquire lock for backup.

        Args:
            timeout: Seconds to wait for lock (0 = don't wait)

        Returns:
            True if lock acquired, False otherwise
        """
        start_time = time.time()

        while True:
            # Check if lock file exists
            if not self.lock_file.exists():
                # Create lock file with our PID
                self._create_lock()
                return True

            # Lock file exists - check if process is still running
            if self._is_stale_lock():
                # Old lock from dead process - remove it
                self._remove_lock()
                continue

            # Lock is held by running process
            if timeout == 0:
                return False

            # Wait and retry
            if time.time() - start_time >= timeout:
                return False

            time.sleep(1)

    def release(self) -> None:
        """Release the lock."""
        self._remove_lock()

    def is_locked(self) -> bool:
        """Check if backup is currently locked.

        Returns:
            True if another backup is running
        """
        if not self.lock_file.exists():
            return False

        return not self._is_stale_lock()

    def get_lock_info(self) -> Optional[dict]:
        """Get information about current lock.

        Returns:
            Dictionary with lock info or None if not locked
        """
        if not self.lock_file.exists():
            return None

        try:
            with open(self.lock_file, 'r') as f:
                pid = int(f.read().strip())

            # Check if process exists
            if not psutil.pid_exists(pid):
                return None

            try:
                process = psutil.Process(pid)
                return {
                    'pid': pid,
                    'created': process.create_time(),
                    'cmdline': ' '.join(process.cmdline()),
                }
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                return None

        except (ValueError, IOError):
            return None

    def _create_lock(self) -> None:
        """Create lock file with current PID."""
        pid = os.getpid()
        with open(self.lock_file, 'w') as f:
            f.write(str(pid))

    def _remove_lock(self) -> None:
        """Remove lock file."""
        try:
            self.lock_file.unlink()
        except FileNotFoundError:
            pass

    def _is_stale_lock(self) -> bool:
        """Check if lock file is stale (process no longer exists).

        Returns:
            True if lock is stale
        """
        try:
            with open(self.lock_file, 'r') as f:
                pid = int(f.read().strip())

            # Check if process still exists
            return not psutil.pid_exists(pid)

        except (ValueError, IOError):
            # Can't read lock file - assume stale
            return True

    def __enter__(self):
        """Context manager entry."""
        if not self.acquire():
            raise RuntimeError("Could not acquire backup lock - another backup is running")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.release()
