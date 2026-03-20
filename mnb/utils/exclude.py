"""File exclusion pattern matching."""

import fnmatch
from pathlib import Path
from typing import List


class ExclusionMatcher:
    """Matches files against gitignore-style exclusion patterns."""

    def __init__(self, patterns: List[str], base_path: Path = None):
        """Initialize exclusion matcher.

        Args:
            patterns: List of gitignore-style patterns
            base_path: Base path for pattern matching
        """
        self.patterns = patterns
        self.base_path = base_path or Path.home()

    def should_exclude(self, path: Path) -> bool:
        """Check if a path should be excluded.

        Args:
            path: Path to check

        Returns:
            True if path matches any exclusion pattern
        """
        # Convert to absolute path if not already
        if not path.is_absolute():
            path = path.resolve()

        # Try to get relative path from base
        try:
            rel_path = path.relative_to(self.base_path)
        except ValueError:
            # Path is not under base_path, use as-is
            rel_path = path

        # Check against each pattern
        for pattern in self.patterns:
            if self._matches_pattern(path, rel_path, pattern):
                return True

        return False

    def _matches_pattern(self, abs_path: Path, rel_path: Path, pattern: str) -> bool:
        """Check if path matches a specific pattern.

        Args:
            abs_path: Absolute path
            rel_path: Relative path from base
            pattern: Exclusion pattern

        Returns:
            True if path matches pattern
        """
        # Expand home directory in pattern
        if pattern.startswith('~/'):
            pattern_path = Path(pattern).expanduser()
            try:
                # Check if path starts with pattern path
                abs_path.relative_to(pattern_path)
                return True
            except ValueError:
                return False

        # Handle ** patterns (match any level of directories)
        if '**' in pattern:
            # Remove ** and check if pattern appears anywhere in path
            # Example: **/venv/ should match any path containing /venv/
            pattern_clean = pattern.replace('**/', '').replace('**', '')

            # Check if pattern matches any suffix of the path
            path_str = str(rel_path)

            # For patterns like **/venv/, check if any part of path ends with venv/
            if pattern.endswith('/'):
                # It's a directory pattern - check if any directory in path matches
                dir_name = pattern_clean.rstrip('/')
                for part in rel_path.parts:
                    if fnmatch.fnmatch(part, dir_name):
                        return True
            else:
                # File pattern - check against path components
                for i in range(len(rel_path.parts)):
                    partial = '/'.join(rel_path.parts[i:])
                    if fnmatch.fnmatch(partial, pattern_clean):
                        return True

            return False

        # Handle directory patterns (ending with /)
        if pattern.endswith('/'):
            pattern_name = pattern.rstrip('/')

            # Check if any directory in path matches
            for part in rel_path.parts:
                if fnmatch.fnmatch(part, pattern_name):
                    return True

            return False

        # Handle simple filename patterns
        filename = abs_path.name
        if fnmatch.fnmatch(filename, pattern):
            return True

        # Handle path-based patterns
        path_str = str(rel_path)
        if fnmatch.fnmatch(path_str, pattern):
            return True

        return False

    def filter_paths(self, paths: List[Path]) -> List[Path]:
        """Filter list of paths, removing excluded ones.

        Args:
            paths: List of paths to filter

        Returns:
            List of non-excluded paths
        """
        return [p for p in paths if not self.should_exclude(p)]
