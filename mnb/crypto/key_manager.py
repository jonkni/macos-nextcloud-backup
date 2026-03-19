"""Encryption key management with macOS Keychain integration."""

import logging
from typing import Optional
import keyring

from mnb.crypto.encryption import (
    generate_salt,
    derive_key,
    verify_key_strength,
    EncryptionError,
    PBKDF2_ITERATIONS,
)


# Keychain service name for encryption key
KEYCHAIN_SERVICE = "macos-nextcloud-backup-encryption"
KEYCHAIN_USERNAME = "encryption-key"


class KeyManager:
    """Manages encryption keys with Keychain storage and config integration."""

    def __init__(self, config_manager=None):
        """Initialize key manager.

        Args:
            config_manager: ConfigManager instance for storing salt
        """
        self.config = config_manager
        self.logger = logging.getLogger(__name__)

    def is_encryption_enabled(self) -> bool:
        """Check if encryption is enabled in configuration.

        Returns:
            True if encryption is enabled
        """
        if not self.config:
            return False

        return self.config.get('encryption.enabled', False)

    def get_salt(self) -> Optional[bytes]:
        """Get salt from configuration.

        Returns:
            Salt bytes if found, None otherwise
        """
        if not self.config:
            return None

        salt_hex = self.config.get('encryption.key_derivation.salt')
        if not salt_hex:
            return None

        try:
            return bytes.fromhex(salt_hex)
        except ValueError as e:
            self.logger.error(f"Invalid salt in config: {e}")
            return None

    def set_salt(self, salt: bytes) -> None:
        """Store salt in configuration.

        Args:
            salt: Salt bytes to store

        Raises:
            EncryptionError: If salt storage fails
        """
        if not self.config:
            raise EncryptionError("No config manager available")

        try:
            salt_hex = salt.hex()
            self.config.set('encryption.key_derivation.salt', salt_hex)
            self.config.save()

        except Exception as e:
            raise EncryptionError(f"Failed to store salt: {e}") from e

    def get_key(self) -> Optional[bytes]:
        """Retrieve encryption key from Keychain.

        Returns:
            32-byte encryption key if found, None otherwise
        """
        try:
            key_hex = keyring.get_password(KEYCHAIN_SERVICE, KEYCHAIN_USERNAME)
            if not key_hex:
                return None

            return bytes.fromhex(key_hex)

        except Exception as e:
            self.logger.error(f"Failed to retrieve key from Keychain: {e}")
            return None

    def set_key(self, key: bytes) -> None:
        """Store encryption key in Keychain.

        Args:
            key: 32-byte encryption key to store

        Raises:
            EncryptionError: If key storage fails
        """
        if len(key) != 32:
            raise EncryptionError(f"Key must be 32 bytes, got {len(key)}")

        try:
            key_hex = key.hex()
            keyring.set_password(KEYCHAIN_SERVICE, KEYCHAIN_USERNAME, key_hex)

        except Exception as e:
            raise EncryptionError(f"Failed to store key in Keychain: {e}") from e

    def delete_key(self) -> None:
        """Delete encryption key from Keychain.

        Raises:
            EncryptionError: If key deletion fails
        """
        try:
            keyring.delete_password(KEYCHAIN_SERVICE, KEYCHAIN_USERNAME)

        except keyring.errors.PasswordDeleteError:
            # Key doesn't exist - that's fine
            pass
        except Exception as e:
            raise EncryptionError(f"Failed to delete key from Keychain: {e}") from e

    def setup_encryption(self, passphrase: str) -> None:
        """Set up encryption with a new passphrase.

        This will:
        1. Verify passphrase strength
        2. Generate a new salt
        3. Derive encryption key from passphrase
        4. Store salt in config
        5. Store key in Keychain
        6. Enable encryption in config

        Args:
            passphrase: User's passphrase

        Raises:
            EncryptionError: If setup fails or passphrase is too weak
        """
        # Verify passphrase strength
        is_valid, message = verify_key_strength(passphrase)
        if not is_valid:
            raise EncryptionError(message)

        # Log warning if passphrase is weak (but allow it)
        if "Warning" in message or "Consider" in message:
            self.logger.warning(message)

        # Generate new salt
        salt = generate_salt()

        # Derive key from passphrase
        self.logger.info("Deriving encryption key (this may take a few seconds)...")
        key = derive_key(passphrase, salt, iterations=PBKDF2_ITERATIONS)

        # Store salt in config
        self.set_salt(salt)

        # Store key in Keychain
        self.set_key(key)

        # Enable encryption in config
        if self.config:
            self.config.set('encryption.enabled', True)
            self.config.set('encryption.algorithm', 'aes-256-gcm')
            self.config.set('encryption.key_derivation.method', 'pbkdf2-hmac-sha256')
            self.config.set('encryption.key_derivation.iterations', PBKDF2_ITERATIONS)
            self.config.set('encryption.encrypt_filenames', False)  # Default: filenames visible
            self.config.save()

        self.logger.info("Encryption setup complete")

    def change_passphrase(self, old_passphrase: str, new_passphrase: str) -> None:
        """Change encryption passphrase.

        This will:
        1. Verify old passphrase is correct
        2. Verify new passphrase strength
        3. Generate new salt
        4. Derive new key
        5. Update config and Keychain

        Args:
            old_passphrase: Current passphrase (for verification)
            new_passphrase: New passphrase

        Raises:
            EncryptionError: If passphrase change fails or old passphrase is incorrect
        """
        # Verify old passphrase is correct
        old_salt = self.get_salt()
        if not old_salt:
            raise EncryptionError("No encryption configured")

        old_key = derive_key(old_passphrase, old_salt)
        stored_key = self.get_key()

        if not stored_key or old_key != stored_key:
            raise EncryptionError("Current passphrase is incorrect")

        # Verify new passphrase strength
        is_valid, message = verify_key_strength(new_passphrase)
        if not is_valid:
            raise EncryptionError(message)

        if "Warning" in message or "Consider" in message:
            self.logger.warning(message)

        # Generate new salt and derive new key
        new_salt = generate_salt()
        self.logger.info("Deriving new encryption key (this may take a few seconds)...")
        new_key = derive_key(new_passphrase, new_salt)

        # Update config and Keychain
        self.set_salt(new_salt)
        self.set_key(new_key)

        self.logger.info("Passphrase changed successfully")

    def disable_encryption(self) -> None:
        """Disable encryption.

        This will:
        1. Set encryption.enabled = false in config
        2. Keep salt and key in case user wants to re-enable
        3. Future backups will be unencrypted

        Note: Existing encrypted backups remain encrypted
        """
        if self.config:
            self.config.set('encryption.enabled', False)
            self.config.save()

        self.logger.info("Encryption disabled (existing encrypted backups remain encrypted)")

    def get_encryption_key(self) -> Optional[bytes]:
        """Get the current encryption key for backup operations.

        Returns:
            32-byte encryption key if encryption is enabled and configured, None otherwise

        Raises:
            EncryptionError: If encryption is enabled but key is not available
        """
        if not self.is_encryption_enabled():
            return None

        key = self.get_key()
        if not key:
            raise EncryptionError(
                "Encryption is enabled but no key found. Run 'mnb crypto enable' first."
            )

        return key

    def verify_passphrase(self, passphrase: str) -> bool:
        """Verify if passphrase is correct.

        Args:
            passphrase: Passphrase to verify

        Returns:
            True if passphrase is correct, False otherwise
        """
        salt = self.get_salt()
        if not salt:
            return False

        try:
            test_key = derive_key(passphrase, salt)
            stored_key = self.get_key()

            return test_key == stored_key

        except Exception:
            return False
