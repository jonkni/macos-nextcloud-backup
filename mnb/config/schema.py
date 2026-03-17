"""Configuration schema definitions."""

from typing import Dict, Any


class ConfigSchema:
    """Schema validation for configuration."""

    REQUIRED_FIELDS = [
        'nextcloud.url',
        'nextcloud.username',
        'include_paths',
    ]

    VALID_INTERVALS = ['hourly', 'daily', 'weekly', 'manual']
    VALID_CHECKSUM_MODES = ['fast', 'full']
    VALID_LOG_LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR']
