#!/usr/bin/env python3
"""
Clean up .config/mnb files from existing backups.

This script removes backup tool metadata files that were accidentally
backed up in snapshots 36-98 (~34 GB of wasted storage).
"""

import sqlite3
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from mnb.config.manager import ConfigManager
from mnb.core.backup_engine import BackupEngine


def main():
    print("Cleanup: Remove .config/mnb from existing backups")
    print("=" * 60)
    print()

    # Load config and create backup engine
    config = ConfigManager()
    config.load()  # Load configuration from file
    engine = BackupEngine(config)

    # Use existing connections
    db = engine.metadata
    webdav = engine.webdav

    # Find all .config/mnb files
    print("Finding .config/mnb files in backups...")
    with db._get_connection() as conn:
        cursor = conn.execute("""
            SELECT id, snapshot_id, path, remote_path, size, uploaded
            FROM files
            WHERE path LIKE '%/.config/mnb/%'
            ORDER BY snapshot_id, path
        """)

        files_to_clean = cursor.fetchall()

    if not files_to_clean:
        print("✓ No .config/mnb files found in backups")
        return

    total_size = sum(f['size'] for f in files_to_clean)
    snapshots = set(f['snapshot_id'] for f in files_to_clean)

    print(f"Found {len(files_to_clean)} files across {len(snapshots)} snapshots")
    print(f"Total size: {total_size / (1024**3):.2f} GB")
    print()

    # Show breakdown by file
    file_breakdown = {}
    for f in files_to_clean:
        filename = Path(f['path']).name
        if filename not in file_breakdown:
            file_breakdown[filename] = {'count': 0, 'size': 0}
        file_breakdown[filename]['count'] += 1
        file_breakdown[filename]['size'] += f['size']

    print("Breakdown by file:")
    for filename, stats in sorted(file_breakdown.items(), key=lambda x: x[1]['size'], reverse=True):
        print(f"  {filename:30s} - {stats['count']:3d} copies, {stats['size'] / (1024**3):6.2f} GB")
    print()

    # Confirm
    response = input(f"Delete these {len(files_to_clean)} files from Nextcloud and metadata? [y/N] ")
    if response.lower() != 'y':
        print("Cancelled.")
        return

    print()
    print("Cleaning up...")

    deleted_remote = 0
    deleted_db = 0
    errors = 0
    file_ids_to_delete = []

    for i, file_info in enumerate(files_to_clean, 1):
        print(f"[{i}/{len(files_to_clean)}] {Path(file_info['path']).name} (snapshot {file_info['snapshot_id']})", end=" ")

        # Delete from Nextcloud if uploaded
        if file_info['uploaded'] and file_info['remote_path']:
            try:
                success = webdav.delete(file_info['remote_path'])
                if success:
                    deleted_remote += 1
                    print("✓ deleted", end=" ")
                else:
                    print("⚠ not found", end=" ")
            except Exception as e:
                print(f"✗ error: {e}", end=" ")
                errors += 1
        else:
            print("- not uploaded", end=" ")

        # Mark for database deletion
        file_ids_to_delete.append(file_info['id'])
        print("✓ marked for removal")

    # Remove from database in batch
    print()
    print("Removing file records from database...")
    with db._get_connection() as conn:
        for file_id in file_ids_to_delete:
            conn.execute("DELETE FROM files WHERE id = ?", (file_id,))
            deleted_db += 1
        conn.commit()

    print()
    print("=" * 60)
    print(f"✓ Cleanup complete!")
    print(f"  Files deleted from Nextcloud: {deleted_remote}")
    print(f"  Records removed from database: {deleted_db}")
    print(f"  Errors: {errors}")
    print(f"  Storage saved: ~{total_size / (1024**3):.2f} GB")
    print()
    print("Next backup will no longer include .config/mnb files.")


if __name__ == '__main__':
    main()
