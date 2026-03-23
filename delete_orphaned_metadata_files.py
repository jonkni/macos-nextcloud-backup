#!/usr/bin/env python3
"""
Delete orphaned .config/mnb files from Nextcloud.

These files were already removed from the database, but still exist
on Nextcloud, wasting ~32 GB of storage.
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from mnb.config.manager import ConfigManager
from mnb.core.backup_engine import BackupEngine


def main():
    print("Delete Orphaned Metadata Files from Nextcloud")
    print("=" * 60)
    print()

    # Load config
    config = ConfigManager()
    config.load()
    engine = BackupEngine(config)
    webdav = engine.webdav

    # Known snapshot IDs that had .config/mnb files
    snapshot_ids = range(36, 99)  # Snapshots 36-98

    machine_name = config.get('machine.name')
    backup_folder = config.get('nextcloud.backup_folder', 'backup')

    files_to_delete = []

    # Build list of files to delete
    print("Building list of files to delete...")
    for snapshot_id in snapshot_ids:
        # Get snapshot timestamp from database
        with engine.metadata._get_connection() as conn:
            cursor = conn.execute(
                "SELECT timestamp FROM snapshots WHERE id = ?",
                (snapshot_id,)
            )
            result = cursor.fetchone()

        if not result:
            continue

        timestamp = result['timestamp']
        snapshot_path = f"{backup_folder}/{machine_name}/snapshots/{timestamp}"

        # Files that were backed up
        mnb_files = [
            f"{snapshot_path}/.config/mnb/metadata.db.enc",
            f"{snapshot_path}/.config/mnb/config.yml.enc",
            f"{snapshot_path}/.config/mnb/config.yml.backup.enc",
            f"{snapshot_path}/.config/mnb/backup.lock.enc",
        ]

        files_to_delete.extend(mnb_files)

    print(f"Found {len(files_to_delete)} potential files to delete")
    print(f"Estimated storage: ~32 GB")
    print()

    # Confirm
    response = input(f"Delete these {len(files_to_delete)} files from Nextcloud? [y/N] ")
    if response.lower() != 'y':
        print("Cancelled.")
        return

    print()
    print("Deleting files from Nextcloud...")

    deleted = 0
    not_found = 0
    errors = 0

    for i, remote_path in enumerate(files_to_delete, 1):
        filename = Path(remote_path).name
        snapshot_id = remote_path.split('/snapshots/')[1].split('/')[0] if '/snapshots/' in remote_path else '?'

        print(f"[{i}/{len(files_to_delete)}] {filename} (snapshot {snapshot_id[:19]})", end=" ")

        try:
            success = webdav.delete(remote_path)
            if success:
                deleted += 1
                print("✓ deleted")
            else:
                not_found += 1
                print("⚠ not found")
        except Exception as e:
            errors += 1
            print(f"✗ error: {e}")

    print()
    print("=" * 60)
    print(f"✓ Cleanup complete!")
    print(f"  Files deleted: {deleted}")
    print(f"  Not found: {not_found}")
    print(f"  Errors: {errors}")
    print(f"  Estimated storage freed: ~32 GB")


if __name__ == '__main__':
    main()
