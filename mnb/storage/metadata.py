"""Metadata database for tracking backups."""

import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from contextlib import contextmanager

from mnb.core.scanner import FileInfo


class MetadataDB:
    """SQLite database for backup metadata."""

    def __init__(self, db_path: Path):
        """Initialize metadata database.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Snapshots table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    type TEXT NOT NULL,
                    file_count INTEGER,
                    total_size INTEGER,
                    status TEXT DEFAULT 'in_progress',
                    error_message TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    completed_at TEXT
                )
            ''')

            # Files table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    snapshot_id INTEGER NOT NULL,
                    path TEXT NOT NULL,
                    size INTEGER NOT NULL,
                    mtime REAL NOT NULL,
                    mode INTEGER NOT NULL,
                    checksum TEXT,
                    remote_path TEXT,
                    uploaded BOOLEAN DEFAULT 0,
                    FOREIGN KEY (snapshot_id) REFERENCES snapshots(id),
                    UNIQUE(snapshot_id, path)
                )
            ''')

            # Index for faster lookups
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_files_snapshot
                ON files(snapshot_id)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_files_path
                ON files(path)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_snapshots_timestamp
                ON snapshots(timestamp)
            ''')

            conn.commit()

    @contextmanager
    def _get_connection(self):
        """Get database connection context manager."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def create_snapshot(self, timestamp: str, backup_type: str = 'incremental'
                       ) -> int:
        """Create a new snapshot.

        Args:
            timestamp: Snapshot timestamp (ISO format)
            backup_type: 'initial' or 'incremental'

        Returns:
            Snapshot ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO snapshots (timestamp, type, status)
                VALUES (?, ?, 'in_progress')
            ''', (timestamp, backup_type))
            conn.commit()
            return cursor.lastrowid

    def complete_snapshot(self, snapshot_id: int, file_count: int,
                         total_size: int) -> None:
        """Mark snapshot as completed.

        Args:
            snapshot_id: Snapshot ID
            file_count: Number of files in snapshot
            total_size: Total size in bytes
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE snapshots
                SET status = 'completed',
                    file_count = ?,
                    total_size = ?,
                    completed_at = ?
                WHERE id = ?
            ''', (file_count, total_size, datetime.now().isoformat(), snapshot_id))
            conn.commit()

    def fail_snapshot(self, snapshot_id: int, error_message: str) -> None:
        """Mark snapshot as failed.

        Args:
            snapshot_id: Snapshot ID
            error_message: Error description
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE snapshots
                SET status = 'failed',
                    error_message = ?,
                    completed_at = ?
                WHERE id = ?
            ''', (error_message, datetime.now().isoformat(), snapshot_id))
            conn.commit()

    def add_file(self, snapshot_id: int, file_info: FileInfo,
                remote_path: str, uploaded: bool = False) -> None:
        """Add file to snapshot.

        Args:
            snapshot_id: Snapshot ID
            file_info: File information
            remote_path: Remote path in backup
            uploaded: Whether file was uploaded
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO files
                (snapshot_id, path, size, mtime, mode, checksum, remote_path, uploaded)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                snapshot_id,
                str(file_info.path),
                file_info.size,
                file_info.mtime,
                file_info.mode,
                file_info.checksum,
                remote_path,
                uploaded
            ))
            conn.commit()

    def get_latest_snapshot(self) -> Optional[Dict[str, Any]]:
        """Get most recent completed snapshot.

        Returns:
            Snapshot information or None if no snapshots
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM snapshots
                WHERE status = 'completed'
                ORDER BY timestamp DESC
                LIMIT 1
            ''')
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_snapshot(self, snapshot_id: int) -> Optional[Dict[str, Any]]:
        """Get snapshot by ID.

        Args:
            snapshot_id: Snapshot ID

        Returns:
            Snapshot information or None if not found
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM snapshots WHERE id = ?', (snapshot_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def list_snapshots(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List snapshots ordered by timestamp.

        Args:
            limit: Maximum number of snapshots to return

        Returns:
            List of snapshot dictionaries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM snapshots
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_file_in_snapshot(self, snapshot_id: int, path: str
                            ) -> Optional[Dict[str, Any]]:
        """Get file information from snapshot.

        Args:
            snapshot_id: Snapshot ID
            path: File path

        Returns:
            File information or None if not found
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM files
                WHERE snapshot_id = ? AND path = ?
            ''', (snapshot_id, path))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_files_in_snapshot(self, snapshot_id: int) -> List[Dict[str, Any]]:
        """Get all files in a snapshot.

        Args:
            snapshot_id: Snapshot ID

        Returns:
            List of file dictionaries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM files
                WHERE snapshot_id = ?
                ORDER BY path
            ''', (snapshot_id,))
            return [dict(row) for row in cursor.fetchall()]

    def has_file_changed(self, path: str, current_info: FileInfo) -> bool:
        """Check if file has changed since last backup.

        Args:
            path: File path
            current_info: Current file information

        Returns:
            True if file has changed, doesn't exist in last backup, or failed to upload
        """
        latest_snapshot = self.get_latest_snapshot()
        if not latest_snapshot:
            return True  # No previous backup

        previous_file = self.get_file_in_snapshot(latest_snapshot['id'], path)
        if not previous_file:
            return True  # File didn't exist in previous backup

        # Check if previous upload failed - need to retry
        if not previous_file['uploaded']:
            return True  # Previous upload failed, retry this file

        # Compare checksums
        if current_info.checksum != previous_file['checksum']:
            return True

        # Compare size and mtime as fallback
        if (current_info.size != previous_file['size'] or
            current_info.mtime != previous_file['mtime']):
            return True

        return False

    def delete_snapshot(self, snapshot_id: int) -> None:
        """Delete a snapshot and its files.

        Args:
            snapshot_id: Snapshot ID to delete
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM files WHERE snapshot_id = ?', (snapshot_id,))
            cursor.execute('DELETE FROM snapshots WHERE id = ?', (snapshot_id,))
            conn.commit()

    def get_statistics(self) -> Dict[str, Any]:
        """Get backup statistics.

        Returns:
            Dictionary with backup statistics
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Total snapshots
            cursor.execute('SELECT COUNT(*) as count FROM snapshots WHERE status = "completed"')
            total_snapshots = cursor.fetchone()['count']

            # Latest snapshot info
            latest = self.get_latest_snapshot()

            # Total size of latest backup
            total_size = latest['total_size'] if latest else 0

            return {
                'total_snapshots': total_snapshots,
                'latest_snapshot': latest,
                'total_size': total_size,
            }
