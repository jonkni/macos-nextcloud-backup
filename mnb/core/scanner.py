"""File system scanner for backup."""

import os
import hashlib
from pathlib import Path
from typing import List, Dict, Iterator, Optional, Callable
from dataclasses import dataclass
from datetime import datetime

from mnb.utils.exclude import ExclusionMatcher


@dataclass
class FileInfo:
    """Information about a file."""

    path: Path
    size: int
    mtime: float
    mode: int
    is_dir: bool
    checksum: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'path': str(self.path),
            'size': self.size,
            'mtime': self.mtime,
            'mode': self.mode,
            'is_dir': self.is_dir,
            'checksum': self.checksum,
        }

    @classmethod
    def from_path(cls, path: Path, calculate_checksum: bool = False,
                  checksum_mode: str = 'fast') -> 'FileInfo':
        """Create FileInfo from a path.

        Args:
            path: Path to file or directory
            calculate_checksum: Whether to calculate file checksum
            checksum_mode: 'fast' (size+mtime) or 'full' (SHA256)

        Returns:
            FileInfo instance
        """
        stat = path.stat()

        checksum = None
        if calculate_checksum and not path.is_dir():
            if checksum_mode == 'fast':
                # Fast checksum: combine size and mtime
                checksum = f"fast:{stat.st_size}:{stat.st_mtime}"
            elif checksum_mode == 'full':
                # Full checksum: SHA256 of file contents
                checksum = cls._calculate_sha256(path)

        return cls(
            path=path,
            size=stat.st_size,
            mtime=stat.st_mtime,
            mode=stat.st_mode,
            is_dir=path.is_dir(),
            checksum=checksum,
        )

    @staticmethod
    def _calculate_sha256(path: Path) -> str:
        """Calculate SHA256 checksum of a file.

        Args:
            path: Path to file

        Returns:
            Hex digest of SHA256 checksum
        """
        sha256_hash = hashlib.sha256()
        with open(path, 'rb') as f:
            # Read in chunks to handle large files
            for byte_block in iter(lambda: f.read(65536), b""):
                sha256_hash.update(byte_block)
        return f"sha256:{sha256_hash.hexdigest()}"


class FileScanner:
    """Scans filesystem for files to backup."""

    def __init__(self, include_paths: List[Path], exclude_patterns: List[str],
                 checksum_mode: str = 'fast'):
        """Initialize file scanner.

        Args:
            include_paths: List of paths to scan
            exclude_patterns: List of exclusion patterns
            checksum_mode: 'fast' or 'full'
        """
        self.include_paths = include_paths
        self.exclude_patterns = exclude_patterns
        self.checksum_mode = checksum_mode
        self.matcher = ExclusionMatcher(exclude_patterns)

    def scan(self, progress_callback: Optional[Callable[[int, str], None]] = None
            ) -> Iterator[FileInfo]:
        """Scan filesystem and yield file information.

        Args:
            progress_callback: Optional callback(file_count, current_path)

        Yields:
            FileInfo for each non-excluded file
        """
        file_count = 0

        for include_path in self.include_paths:
            if not include_path.exists():
                continue

            if include_path.is_file():
                # Single file
                if not self.matcher.should_exclude(include_path):
                    yield FileInfo.from_path(include_path, True, self.checksum_mode)
                    file_count += 1
                    if progress_callback:
                        progress_callback(file_count, str(include_path))
            else:
                # Directory - walk recursively
                for root, dirs, files in os.walk(include_path, followlinks=False):
                    root_path = Path(root)

                    # Filter directories in-place to skip excluded dirs
                    dirs[:] = [
                        d for d in dirs
                        if not self.matcher.should_exclude(root_path / d)
                    ]

                    # Process files
                    for filename in files:
                        file_path = root_path / filename

                        # Skip excluded files
                        if self.matcher.should_exclude(file_path):
                            continue

                        # Skip if we can't access the file
                        try:
                            info = FileInfo.from_path(file_path, True, self.checksum_mode)
                            yield info

                            file_count += 1
                            if progress_callback:
                                progress_callback(file_count, str(file_path))

                        except (OSError, PermissionError):
                            # Skip files we can't read
                            continue

    def estimate_size(self, progress_callback: Optional[Callable[[int, int], None]] = None
                     ) -> Dict[str, int]:
        """Estimate total size of files to backup.

        Args:
            progress_callback: Optional callback(files_scanned, total_size)

        Returns:
            Dictionary with 'file_count' and 'total_size'
        """
        file_count = 0
        total_size = 0

        for file_info in self.scan():
            if not file_info.is_dir:
                file_count += 1
                total_size += file_info.size

                if progress_callback:
                    progress_callback(file_count, total_size)

        return {
            'file_count': file_count,
            'total_size': total_size,
        }

    def scan_to_list(self, progress_callback: Optional[Callable[[int, str], None]] = None
                    ) -> List[FileInfo]:
        """Scan and return list of all files.

        Args:
            progress_callback: Optional callback(file_count, current_path)

        Returns:
            List of FileInfo objects
        """
        return list(self.scan(progress_callback))
