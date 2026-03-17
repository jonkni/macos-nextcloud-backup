"""WebDAV client for Nextcloud integration."""

import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
import requests
from requests.auth import HTTPBasicAuth
from urllib.parse import urljoin, quote


class WebDAVClient:
    """WebDAV client for Nextcloud operations."""

    def __init__(self, base_url: str, username: str, password: str,
                 webdav_path: str = None):
        """Initialize WebDAV client.

        Args:
            base_url: Nextcloud base URL (e.g., https://cloud.example.com)
            username: Nextcloud username
            password: Nextcloud password
            webdav_path: WebDAV path (default: /remote.php/dav/files/{username}/)
        """
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password

        if webdav_path is None:
            webdav_path = f'/remote.php/dav/files/{username}/'

        self.webdav_path = webdav_path
        self.webdav_url = urljoin(self.base_url, webdav_path)
        self.auth = HTTPBasicAuth(username, password)
        self.session = requests.Session()
        self.session.auth = self.auth

    def _get_url(self, remote_path: str) -> str:
        """Get full WebDAV URL for a remote path.

        Args:
            remote_path: Remote path relative to webdav root

        Returns:
            Full WebDAV URL
        """
        # Remove leading slash if present
        remote_path = remote_path.lstrip('/')
        # URL encode the path
        encoded_path = '/'.join(quote(part, safe='') for part in remote_path.split('/'))
        return urljoin(self.webdav_url, encoded_path)

    def test_connection(self) -> bool:
        """Test connection to Nextcloud.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            response = self.session.request('PROPFIND', self.webdav_url,
                                           headers={'Depth': '0'},
                                           timeout=10)
            return response.status_code in [200, 207]
        except Exception:
            return False

    def exists(self, remote_path: str) -> bool:
        """Check if a remote path exists.

        Args:
            remote_path: Remote path to check

        Returns:
            True if path exists, False otherwise
        """
        try:
            url = self._get_url(remote_path)
            response = self.session.request('PROPFIND', url,
                                           headers={'Depth': '0'},
                                           timeout=10)
            return response.status_code in [200, 207]
        except Exception:
            return False

    def mkdir(self, remote_path: str) -> bool:
        """Create a directory on Nextcloud.

        Args:
            remote_path: Remote directory path

        Returns:
            True if successful, False otherwise
        """
        try:
            url = self._get_url(remote_path)
            response = self.session.request('MKCOL', url, timeout=10)
            return response.status_code in [201, 405]  # 405 means already exists
        except Exception:
            return False

    def makedirs(self, remote_path: str) -> bool:
        """Create directory and all parent directories.

        Args:
            remote_path: Remote directory path

        Returns:
            True if successful, False otherwise
        """
        parts = remote_path.strip('/').split('/')
        current_path = ''

        for part in parts:
            current_path = f"{current_path}/{part}" if current_path else part
            if not self.exists(current_path):
                if not self.mkdir(current_path):
                    return False

        return True

    def upload_file(self, local_path: Path, remote_path: str,
                   progress_callback: Optional[callable] = None) -> bool:
        """Upload a file to Nextcloud.

        Args:
            local_path: Local file path
            remote_path: Remote file path
            progress_callback: Optional callback for progress updates

        Returns:
            True if successful, False otherwise
        """
        try:
            url = self._get_url(remote_path)

            # Ensure parent directory exists
            parent = '/'.join(remote_path.rstrip('/').split('/')[:-1])
            if parent and not self.exists(parent):
                self.makedirs(parent)

            # Upload file
            file_size = local_path.stat().st_size

            with open(local_path, 'rb') as f:
                if progress_callback:
                    # Wrap file object for progress tracking
                    from mnb.utils.progress import ProgressFileWrapper
                    f = ProgressFileWrapper(f, file_size, progress_callback)

                response = self.session.put(url, data=f, timeout=300)

            return response.status_code in [200, 201, 204]

        except Exception as e:
            print(f"Upload failed: {e}")
            return False

    def download_file(self, remote_path: str, local_path: Path,
                     progress_callback: Optional[callable] = None) -> bool:
        """Download a file from Nextcloud.

        Args:
            remote_path: Remote file path
            local_path: Local file path
            progress_callback: Optional callback for progress updates

        Returns:
            True if successful, False otherwise
        """
        try:
            url = self._get_url(remote_path)

            # Ensure local parent directory exists
            local_path.parent.mkdir(parents=True, exist_ok=True)

            # Download file
            response = self.session.get(url, stream=True, timeout=60)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback:
                            progress_callback(downloaded, total_size)

            return True

        except Exception as e:
            print(f"Download failed: {e}")
            return False

    def list_directory(self, remote_path: str) -> List[Dict[str, Any]]:
        """List contents of a directory.

        Args:
            remote_path: Remote directory path

        Returns:
            List of file/directory information dictionaries
        """
        try:
            url = self._get_url(remote_path)

            response = self.session.request(
                'PROPFIND',
                url,
                headers={'Depth': '1'},
                timeout=30
            )

            if response.status_code not in [200, 207]:
                return []

            # Parse WebDAV response (simplified - would need proper XML parsing)
            # For now, return empty list - full implementation would parse XML
            items = []

            # TODO: Parse XML response properly using xml.etree.ElementTree
            # This is a placeholder that returns basic structure

            return items

        except Exception:
            return []

    def delete(self, remote_path: str) -> bool:
        """Delete a file or directory.

        Args:
            remote_path: Remote path to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            url = self._get_url(remote_path)
            response = self.session.delete(url, timeout=30)
            return response.status_code in [200, 204, 404]  # 404 means already gone
        except Exception:
            return False

    def get_file_info(self, remote_path: str) -> Optional[Dict[str, Any]]:
        """Get information about a file.

        Args:
            remote_path: Remote file path

        Returns:
            Dictionary with file info or None if not found
        """
        try:
            url = self._get_url(remote_path)

            response = self.session.request(
                'PROPFIND',
                url,
                headers={'Depth': '0'},
                timeout=10
            )

            if response.status_code not in [200, 207]:
                return None

            # TODO: Parse XML response properly
            # For now, return basic info
            return {
                'path': remote_path,
                'exists': True,
            }

        except Exception:
            return None

    def get_quota_info(self) -> Optional[Dict[str, int]]:
        """Get quota information.

        Returns:
            Dictionary with 'used' and 'available' bytes, or None if unavailable
        """
        try:
            # Query quota via WebDAV PROPFIND
            response = self.session.request(
                'PROPFIND',
                self.webdav_url,
                headers={'Depth': '0'},
                data='''<?xml version="1.0"?>
                <d:propfind xmlns:d="DAV:">
                    <d:prop>
                        <d:quota-available-bytes/>
                        <d:quota-used-bytes/>
                    </d:prop>
                </d:propfind>''',
                timeout=10
            )

            if response.status_code not in [200, 207]:
                return None

            # TODO: Parse XML response properly to extract quota
            # For now, return None - would need proper XML parsing

            return None

        except Exception:
            return None
