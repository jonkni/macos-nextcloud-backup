"""Main backup engine."""

from pathlib import Path
from typing import Optional, Callable, Dict, Any, List
from datetime import datetime
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

from mnb.config.manager import ConfigManager
from mnb.storage.webdav import WebDAVClient
from mnb.storage.metadata import MetadataDB
from mnb.core.scanner import FileScanner, FileInfo


class BackupEngine:
    """Main backup engine that orchestrates the backup process."""

    def __init__(self, config: ConfigManager):
        """Initialize backup engine.

        Args:
            config: Configuration manager
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Initialize WebDAV client
        self.webdav = WebDAVClient(
            base_url=config.get('nextcloud.url'),
            username=config.get('nextcloud.username'),
            password=config.get('nextcloud.password'),
            webdav_path=config.get('nextcloud.webdav_path')
        )

        # Initialize metadata database
        db_path = config.DEFAULT_CONFIG_DIR / 'metadata.db'
        self.metadata = MetadataDB(db_path)

        # Initialize file scanner
        self.scanner = FileScanner(
            include_paths=config.get_include_paths(),
            exclude_patterns=config.get_exclude_patterns(),
            checksum_mode=config.get('backup.checksum', 'fast')
        )

        # Backup folder in Nextcloud
        self.backup_folder = config.get_backup_folder()

    def test_connection(self) -> bool:
        """Test connection to Nextcloud.

        Returns:
            True if connection successful
        """
        return self.webdav.test_connection()

    def run_backup(self, initial: bool = False,
                  dry_run: bool = False,
                  progress_callback: Optional[Callable[[str, int, int], None]] = None
                  ) -> Dict[str, Any]:
        """Run a backup.

        Args:
            initial: Whether this is an initial (full) backup
            dry_run: If True, don't actually upload files
            progress_callback: Optional callback(status, current, total)

        Returns:
            Dictionary with backup results
        """
        self.logger.info(f"Starting {'initial' if initial else 'incremental'} backup")

        # Create snapshot
        timestamp = datetime.now().isoformat()
        backup_type = 'initial' if initial else 'incremental'
        snapshot_id = self.metadata.create_snapshot(timestamp, backup_type)

        try:
            # Define snapshot folder path
            snapshot_folder = f"{self.backup_folder}/snapshots/{timestamp}"

            # Ensure backup folder exists (skip in dry-run)
            if not dry_run:
                self.webdav.makedirs(self.backup_folder)
                self.webdav.makedirs(snapshot_folder)

            # Scan files
            if progress_callback:
                progress_callback("Scanning files...", 0, 0)

            files_to_backup = []
            files_unchanged = []
            total_size = 0

            for file_info in self.scanner.scan():
                if file_info.is_dir:
                    continue

                # Check if file changed
                if not initial and not self.metadata.has_file_changed(
                    str(file_info.path), file_info
                ):
                    files_unchanged.append(file_info)
                    continue

                files_to_backup.append(file_info)
                total_size += file_info.size

            self.logger.info(
                f"Found {len(files_to_backup)} files to backup "
                f"({len(files_unchanged)} unchanged)"
            )

            # Pre-create all necessary directories in batch
            if not dry_run and files_to_backup:
                if progress_callback:
                    progress_callback("Creating directories...", 0, 0)

                # Collect all unique parent directories
                parent_dirs = set()
                for file_info in files_to_backup:
                    try:
                        rel_path = file_info.path.relative_to(Path.home())
                        remote_path = f"{snapshot_folder}/{rel_path}"
                    except ValueError:
                        remote_path = f"{snapshot_folder}{file_info.path}"

                    parent = '/'.join(remote_path.rstrip('/').split('/')[:-1])
                    if parent:
                        parent_dirs.add(parent)

                # Create all directories at once
                self.webdav.batch_create_dirs(list(parent_dirs))

            # Upload files (with parallel processing)
            uploaded_count = 0
            uploaded_size = 0
            upload_lock = Lock()

            # Get parallelism setting
            max_workers = self.config.get('backup.parallel_uploads', 3)

            def upload_single_file(file_info: FileInfo) -> tuple:
                """Upload a single file and return result."""
                # Determine remote path
                try:
                    rel_path = file_info.path.relative_to(Path.home())
                    remote_path = f"{snapshot_folder}/{rel_path}"
                except ValueError:
                    remote_path = f"{snapshot_folder}{file_info.path}"

                # Upload file
                if not dry_run:
                    success = self.webdav.upload_file(file_info.path, remote_path)
                else:
                    success = True  # Pretend it worked in dry run

                return file_info, remote_path, success

            # Use ThreadPoolExecutor for parallel uploads
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all upload tasks
                future_to_file = {
                    executor.submit(upload_single_file, file_info): file_info
                    for file_info in files_to_backup
                }

                # Process completed uploads
                for future in as_completed(future_to_file):
                    file_info, remote_path, success = future.result()

                    # Thread-safe progress update
                    with upload_lock:
                        if progress_callback:
                            progress_callback(
                                f"Uploading {file_info.path.name}",
                                uploaded_count,
                                len(files_to_backup)
                            )

                        # Record in metadata
                        self.metadata.add_file(
                            snapshot_id,
                            file_info,
                            remote_path,
                            uploaded=success
                        )

                        if success:
                            uploaded_count += 1
                            uploaded_size += file_info.size

            # Record unchanged files
            if not initial:
                for file_info in files_unchanged:
                    # Get previous remote path
                    latest = self.metadata.get_latest_snapshot()
                    if latest and latest['id'] != snapshot_id:
                        prev_file = self.metadata.get_file_in_snapshot(
                            latest['id'],
                            str(file_info.path)
                        )
                        if prev_file:
                            # Reference previous backup
                            self.metadata.add_file(
                                snapshot_id,
                                file_info,
                                prev_file['remote_path'],
                                uploaded=False
                            )

            # Complete snapshot
            total_files = len(files_to_backup) + len(files_unchanged)
            self.metadata.complete_snapshot(snapshot_id, total_files, total_size)

            result = {
                'snapshot_id': snapshot_id,
                'timestamp': timestamp,
                'type': backup_type,
                'files_uploaded': uploaded_count,
                'files_unchanged': len(files_unchanged),
                'total_files': total_files,
                'uploaded_size': uploaded_size,
                'total_size': total_size,
                'status': 'completed',
                'dry_run': dry_run,
            }

            self.logger.info(
                f"Backup completed: {uploaded_count} files uploaded, "
                f"{len(files_unchanged)} unchanged"
            )

            return result

        except Exception as e:
            self.logger.error(f"Backup failed: {e}")
            self.metadata.fail_snapshot(snapshot_id, str(e))
            raise

    def estimate_backup_size(self, progress_callback: Optional[Callable[[int, int], None]] = None
                           ) -> Dict[str, int]:
        """Estimate size of backup.

        Args:
            progress_callback: Optional callback(files_scanned, total_size)

        Returns:
            Dictionary with file_count and total_size
        """
        return self.scanner.estimate_size(progress_callback)

    def list_snapshots(self, limit: int = 10) -> list:
        """List backup snapshots.

        Args:
            limit: Maximum number of snapshots to return

        Returns:
            List of snapshot dictionaries
        """
        return self.metadata.list_snapshots(limit)

    def get_snapshot(self, snapshot_id: int) -> Optional[Dict[str, Any]]:
        """Get snapshot details.

        Args:
            snapshot_id: Snapshot ID

        Returns:
            Snapshot dictionary or None
        """
        return self.metadata.get_snapshot(snapshot_id)

    def restore_file(self, snapshot_id: int, file_path: str,
                    destination: Path,
                    progress_callback: Optional[Callable[[int, int], None]] = None
                    ) -> bool:
        """Restore a file from a snapshot.

        Args:
            snapshot_id: Snapshot ID to restore from
            file_path: Path of file to restore
            destination: Where to restore the file
            progress_callback: Optional callback(bytes_downloaded, total_size)

        Returns:
            True if successful
        """
        # Get file info from snapshot
        file_info = self.metadata.get_file_in_snapshot(snapshot_id, file_path)
        if not file_info:
            self.logger.error(f"File not found in snapshot: {file_path}")
            return False

        # Download from Nextcloud
        remote_path = file_info['remote_path']
        success = self.webdav.download_file(remote_path, destination, progress_callback)

        if success:
            self.logger.info(f"Restored {file_path} to {destination}")
        else:
            self.logger.error(f"Failed to restore {file_path}")

        return success

    def clean_old_snapshots(self, keep_count: Optional[int] = None,
                           dry_run: bool = False) -> Dict[str, Any]:
        """Clean old snapshots based on retention policy.

        Args:
            keep_count: Number of snapshots to keep (overrides config)
            dry_run: If True, don't actually delete

        Returns:
            Dictionary with cleanup results
        """
        if keep_count is None:
            # Calculate from retention policy
            retain = self.config.get('backup.retain', {})
            keep_count = (
                retain.get('hourly', 12) +
                retain.get('daily', 5) +
                retain.get('weekly', 2) +
                retain.get('monthly', 0)
            )

        snapshots = self.metadata.list_snapshots(limit=1000)
        snapshots_to_delete = snapshots[keep_count:]

        deleted_count = 0
        for snapshot in snapshots_to_delete:
            if not dry_run:
                # Delete from Nextcloud
                snapshot_folder = f"{self.backup_folder}/snapshots/{snapshot['timestamp']}"
                self.webdav.delete(snapshot_folder)

                # Delete from metadata
                self.metadata.delete_snapshot(snapshot['id'])

            deleted_count += 1

        self.logger.info(f"Cleaned {deleted_count} old snapshots")

        return {
            'deleted_count': deleted_count,
            'kept_count': len(snapshots) - deleted_count,
            'dry_run': dry_run,
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Get backup statistics.

        Returns:
            Dictionary with backup statistics
        """
        return self.metadata.get_statistics()
