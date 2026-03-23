"""Configuration manager for macOS Nextcloud Backup."""

import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import yaml
import keyring

from mnb.config.schema import ConfigSchema


class ConfigManager:
    """Manages configuration for macOS Nextcloud Backup."""

    DEFAULT_CONFIG_DIR = Path.home() / ".config" / "mnb"
    DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.yml"
    KEYRING_SERVICE = "macos-nextcloud-backup"

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize configuration manager.

        Args:
            config_path: Path to config file. If None, uses default location.
        """
        self.config_path = config_path or self.DEFAULT_CONFIG_FILE
        self.config: Dict[str, Any] = {}

    def load(self) -> Dict[str, Any]:
        """Load configuration from file.

        Returns:
            Configuration dictionary

        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If config file is invalid
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f) or {}

        # Load password from keychain
        username = self.config.get('nextcloud', {}).get('username')
        if username:
            password = self.get_password(username)
            if not self.config.get('nextcloud'):
                self.config['nextcloud'] = {}
            self.config['nextcloud']['password'] = password

        return self.config

    def save(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Save configuration to file.

        Args:
            config: Configuration to save. If None, saves current config.
        """
        if config is not None:
            self.config = config

        # Don't save password to file
        config_to_save = self.config.copy()
        if 'nextcloud' in config_to_save and 'password' in config_to_save['nextcloud']:
            password = config_to_save['nextcloud'].pop('password')
            username = config_to_save['nextcloud'].get('username')
            if username and password:
                self.set_password(username, password)

        # Ensure directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Write config
        with open(self.config_path, 'w') as f:
            yaml.dump(config_to_save, f, default_flow_style=False, sort_keys=False)

    def get(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value by dot-separated path.

        Args:
            key_path: Dot-separated path (e.g., 'nextcloud.url')
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        keys = key_path.split('.')
        value = self.config

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return default
            else:
                return default

        return value

    def set(self, key_path: str, value: Any) -> None:
        """Set configuration value by dot-separated path.

        Args:
            key_path: Dot-separated path (e.g., 'nextcloud.url')
            value: Value to set
        """
        keys = key_path.split('.')
        config = self.config

        # Navigate to the parent dictionary
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]

        # Set the value
        config[keys[-1]] = value

    def get_password(self, username: str) -> Optional[str]:
        """Get password from macOS Keychain.

        Args:
            username: Nextcloud username

        Returns:
            Password if found, None otherwise
        """
        try:
            return keyring.get_password(self.KEYRING_SERVICE, username)
        except Exception:
            return None

    def set_password(self, username: str, password: str) -> None:
        """Store password in macOS Keychain.

        Args:
            username: Nextcloud username
            password: Password to store
        """
        keyring.set_password(self.KEYRING_SERVICE, username, password)

    def delete_password(self, username: str) -> None:
        """Delete password from macOS Keychain.

        Args:
            username: Nextcloud username
        """
        try:
            keyring.delete_password(self.KEYRING_SERVICE, username)
        except Exception:
            pass

    def get_include_paths(self) -> List[Path]:
        """Get list of paths to include in backup.

        Returns:
            List of resolved paths
        """
        paths = self.get('include_paths', [])
        return [Path(p).expanduser() for p in paths]

    def get_exclude_patterns(self) -> List[str]:
        """Get list of exclude patterns.

        Returns:
            List of gitignore-style patterns
        """
        return self.get('exclude_patterns', [])

    def get_machine_name(self) -> str:
        """Get machine name for backups.

        Returns:
            Machine name
        """
        machine_name = self.get('machine.name')
        if not machine_name:
            import socket
            machine_name = socket.gethostname()
        return machine_name

    def get_backup_folder(self) -> str:
        """Get backup folder path in Nextcloud.

        Returns:
            Backup folder path
        """
        machine_name = self.get_machine_name()
        backup_root = self.get('nextcloud.backup_folder', 'backup')
        return f"{backup_root}/{machine_name}"

    def validate(self) -> List[str]:
        """Validate configuration.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Check required fields
        if not self.get('nextcloud.url'):
            errors.append("nextcloud.url is required")

        if not self.get('nextcloud.username'):
            errors.append("nextcloud.username is required")

        if not self.get_include_paths():
            errors.append("include_paths cannot be empty")

        # Check URL format
        url = self.get('nextcloud.url')
        if url and not (url.startswith('http://') or url.startswith('https://')):
            errors.append("nextcloud.url must start with http:// or https://")

        return errors

    @classmethod
    def create_default_config(cls, nextcloud_url: str, username: str,
                             machine_name: Optional[str] = None) -> Dict[str, Any]:
        """Create default configuration.

        Args:
            nextcloud_url: Nextcloud instance URL
            username: Nextcloud username
            machine_name: Machine name (auto-detected if None)

        Returns:
            Default configuration dictionary
        """
        import socket

        if not machine_name:
            machine_name = socket.gethostname().split('.')[0]

        return {
            'nextcloud': {
                'url': nextcloud_url.rstrip('/'),
                'username': username,
                'webdav_path': f'/remote.php/dav/files/{username}/',
                'backup_folder': 'backup',
            },
            'machine': {
                'name': machine_name,
                'hostname': socket.gethostname(),
            },
            'backup': {
                'interval': 'hourly',
                'retain': {
                    'hourly': 12,
                    'daily': 5,
                    'weekly': 2,
                    'monthly': 0,
                },
                'max_upload_speed': 0,
                'chunk_size': 10,
                'parallel_uploads': 3,
                'checksum': 'fast',
            },
            'include_paths': [
                '~/Documents/',
                '~/Desktop/',
                '~/.ssh/',
                '~/.config/',
                '~/.zshrc',
                '~/.bashrc',
                '~/.gitconfig',
            ],
            'exclude_patterns': [
                '**/.git/',
                '**/.svn/',
                '**/node_modules/',
                '**/venv/',
                '**/.venv/',
                '**/env/',
                '**/__pycache__/',
                '**/target/',
                '**/dist/',
                '**/build/',
                '**/.DS_Store',
                '~/Library/Mobile Documents/',
                '~/Pictures/Photos Library.photoslibrary/',
                '~/Downloads/',
                '~/Library/Caches/',
                '~/Library/Logs/',
                '**/*.log',
                '**/.cache/',
                '~/.config/mnb/',  # Exclude backup tool's own metadata
            ],
            'notifications': {
                'enabled': True,
                'on_success': False,
                'on_error': True,
            },
            'logging': {
                'level': 'INFO',
                'file': '~/Library/Logs/mnb.log',
                'max_size': 10,
                'backup_count': 5,
            },
        }
