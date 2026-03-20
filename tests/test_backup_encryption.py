"""Integration tests for backup encryption."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

from mnb.core.backup_engine import BackupEngine
from mnb.config.manager import ConfigManager
from mnb.crypto.encryption import generate_salt, derive_key


@pytest.fixture
def temp_dir():
    """Provide temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_config(temp_dir):
    """Provide mocked config manager."""
    config = Mock(spec=ConfigManager)
    config.DEFAULT_CONFIG_DIR = temp_dir
    config.get_backup_folder.return_value = "backup/test-machine"
    config.get_include_paths.return_value = [temp_dir]
    config.get_exclude_patterns.return_value = []
    config.get.side_effect = lambda key, default=None: {
        'nextcloud.url': 'https://test.example.com',
        'nextcloud.username': 'test',
        'nextcloud.password': 'test',
        'nextcloud.webdav_path': '/remote.php/dav/files/test/',
        'backup.checksum': 'fast',
        'backup.parallel_uploads': 1,
        'encryption.enabled': False,
    }.get(key, default)
    return config


class TestEncryptionIntegration:
    """Integration tests for encryption in backup process."""

    @patch('mnb.core.backup_engine.WebDAVClient')
    @patch('mnb.core.backup_engine.MetadataDB')
    def test_backup_without_encryption(self, mock_db_class, mock_webdav_class, mock_config, temp_dir):
        """Test backup without encryption enabled."""
        # Setup mocks
        mock_webdav = MagicMock()
        mock_webdav_class.return_value = mock_webdav
        mock_webdav.test_connection.return_value = True
        mock_webdav.upload_file.return_value = True

        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.create_snapshot.return_value = 1
        mock_db.has_file_changed.return_value = True

        # Create test file
        test_file = temp_dir / "test.txt"
        test_file.write_text("unencrypted content")

        # Create backup engine
        engine = BackupEngine(mock_config)

        # Verify encryption is disabled
        assert not engine.encryption_enabled

        # Run backup
        result = engine.run_backup(initial=True, dry_run=False)

        # Verify file was uploaded without encryption
        # Check that upload_file was called (actual call verification depends on mock setup)
        assert result['status'] == 'completed'

    @patch('mnb.core.backup_engine.KeyManager')
    @patch('mnb.core.backup_engine.WebDAVClient')
    @patch('mnb.core.backup_engine.MetadataDB')
    def test_backup_with_encryption(self, mock_db_class, mock_webdav_class, mock_km_class, mock_config, temp_dir):
        """Test backup with encryption enabled."""
        # Enable encryption in config
        def get_with_encryption(key, default=None):
            values = {
                'nextcloud.url': 'https://test.example.com',
                'nextcloud.username': 'test',
                'nextcloud.password': 'test',
                'nextcloud.webdav_path': '/remote.php/dav/files/test/',
                'backup.checksum': 'fast',
                'backup.parallel_uploads': 1,
                'encryption.enabled': True,  # ENABLED
            }
            return values.get(key, default)

        mock_config.get.side_effect = get_with_encryption

        # Generate a real encryption key
        salt = generate_salt()
        encryption_key = derive_key("test_passphrase", salt)

        # Setup encryption key manager mock
        mock_km = MagicMock()
        mock_km_class.return_value = mock_km
        mock_km.is_encryption_enabled.return_value = True
        mock_km.get_encryption_key.return_value = encryption_key

        # Setup WebDAV mock
        mock_webdav = MagicMock()
        mock_webdav_class.return_value = mock_webdav
        mock_webdav.test_connection.return_value = True

        # Track uploaded files
        uploaded_files = []

        def mock_upload(local_path, remote_path):
            uploaded_files.append((str(local_path), remote_path))
            return True

        mock_webdav.upload_file.side_effect = mock_upload

        # Setup metadata DB mock
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.create_snapshot.return_value = 1
        mock_db.has_file_changed.return_value = True

        # Track added files
        added_files = []

        def mock_add_file(snapshot_id, file_info, remote_path, uploaded=False, encrypted=False):
            added_files.append({
                'snapshot_id': snapshot_id,
                'path': str(file_info.path),
                'remote_path': remote_path,
                'uploaded': uploaded,
                'encrypted': encrypted,
            })

        mock_db.add_file.side_effect = mock_add_file

        # Create test file
        test_file = temp_dir / "secret.txt"
        test_file.write_text("sensitive content that should be encrypted")

        # Create backup engine
        engine = BackupEngine(mock_config)

        # Verify encryption is enabled
        assert engine.encryption_enabled

        # Run backup
        result = engine.run_backup(initial=True, dry_run=False)

        # Verify backup completed
        assert result['status'] == 'completed'

        # Verify file was added to metadata with encryption flag
        assert len(added_files) > 0
        file_record = added_files[0]
        assert file_record['encrypted'] is True
        assert file_record['remote_path'].endswith('.enc')

        # Verify encrypted file was uploaded (not original)
        assert len(uploaded_files) > 0
        uploaded_path, remote_path = uploaded_files[0]
        # Uploaded file should be a temp file (not the original)
        assert uploaded_path != str(test_file)
        assert remote_path.endswith('.enc')


class TestEncryptedFileDetection:
    """Test detection of encrypted files in metadata."""

    def test_metadata_tracks_encryption_status(self, temp_dir):
        """Metadata should track whether files are encrypted."""
        from mnb.storage.metadata import MetadataDB
        from mnb.core.scanner import FileInfo

        # Create metadata DB
        db_path = temp_dir / "test.db"
        metadata = MetadataDB(db_path)

        # Create snapshot
        snapshot_id = metadata.create_snapshot("2026-03-20T10:00:00", "initial")

        # Create test file info
        test_file = temp_dir / "test.txt"
        test_file.write_text("content")

        file_info = FileInfo(
            path=test_file,
            size=7,
            mtime=test_file.stat().st_mtime,
            mode=test_file.stat().st_mode,
            checksum="abc123",
            is_dir=False
        )

        # Add encrypted file
        metadata.add_file(
            snapshot_id,
            file_info,
            "backup/test.txt.enc",
            uploaded=True,
            encrypted=True
        )

        # Retrieve file
        file_record = metadata.get_file_in_snapshot(snapshot_id, str(test_file))

        # Verify encryption flag is stored
        assert file_record is not None
        assert file_record['encrypted'] == 1  # SQLite stores boolean as int
        assert file_record['encryption_version'] == 1
        assert file_record['remote_path'] == "backup/test.txt.enc"
