"""Progress tracking utilities."""

from typing import Callable, Optional


class ProgressFileWrapper:
    """File wrapper that tracks read progress."""

    def __init__(self, file_obj, total_size: int,
                 callback: Callable[[int, int], None]):
        """Initialize progress wrapper.

        Args:
            file_obj: File object to wrap
            total_size: Total size of file in bytes
            callback: Callback function(bytes_read, total_size)
        """
        self.file_obj = file_obj
        self.total_size = total_size
        self.callback = callback
        self.bytes_read = 0

    def read(self, size: int = -1) -> bytes:
        """Read from file and update progress.

        Args:
            size: Number of bytes to read

        Returns:
            Bytes read
        """
        data = self.file_obj.read(size)
        self.bytes_read += len(data)
        self.callback(self.bytes_read, self.total_size)
        return data

    def __getattr__(self, name):
        """Delegate other attributes to wrapped file object."""
        return getattr(self.file_obj, name)
