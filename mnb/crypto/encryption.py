"""Core encryption primitives using AES-256-GCM and PBKDF2."""

import os
import hashlib
from typing import Tuple

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend


# Constants
SALT_LENGTH = 32  # 256 bits
IV_LENGTH = 12  # 96 bits (recommended for GCM)
KEY_LENGTH = 32  # 256 bits for AES-256
PBKDF2_ITERATIONS = 600_000  # OWASP 2023 recommendation
TAG_LENGTH = 16  # 128 bits authentication tag


class EncryptionError(Exception):
    """Base exception for encryption errors."""
    pass


class DecryptionError(Exception):
    """Base exception for decryption errors."""
    pass


class AuthenticationError(DecryptionError):
    """Raised when authentication tag verification fails."""
    pass


def generate_salt() -> bytes:
    """Generate a random salt for key derivation.

    Returns:
        32-byte random salt
    """
    return os.urandom(SALT_LENGTH)


def generate_iv() -> bytes:
    """Generate a random IV (nonce) for AES-GCM.

    Returns:
        12-byte random IV
    """
    return os.urandom(IV_LENGTH)


def derive_key(passphrase: str, salt: bytes, iterations: int = PBKDF2_ITERATIONS) -> bytes:
    """Derive encryption key from passphrase using PBKDF2-HMAC-SHA256.

    Args:
        passphrase: User's passphrase
        salt: Random salt (32 bytes)
        iterations: Number of PBKDF2 iterations (default: 600,000)

    Returns:
        32-byte derived key suitable for AES-256

    Raises:
        EncryptionError: If key derivation fails
    """
    if not passphrase:
        raise EncryptionError("Passphrase cannot be empty")

    if len(salt) != SALT_LENGTH:
        raise EncryptionError(f"Salt must be {SALT_LENGTH} bytes, got {len(salt)}")

    if iterations < 100_000:
        raise EncryptionError(f"Iterations too low: {iterations} (minimum: 100,000)")

    try:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=KEY_LENGTH,
            salt=salt,
            iterations=iterations,
            backend=default_backend()
        )

        key = kdf.derive(passphrase.encode('utf-8'))
        return key

    except Exception as e:
        raise EncryptionError(f"Key derivation failed: {e}") from e


def encrypt_data(data: bytes, key: bytes, iv: bytes = None) -> Tuple[bytes, bytes]:
    """Encrypt data using AES-256-GCM.

    Args:
        data: Plaintext data to encrypt
        key: 32-byte encryption key
        iv: 12-byte IV/nonce (generated if not provided)

    Returns:
        Tuple of (iv, ciphertext_with_tag)
        The ciphertext includes the 16-byte authentication tag appended

    Raises:
        EncryptionError: If encryption fails
    """
    if len(key) != KEY_LENGTH:
        raise EncryptionError(f"Key must be {KEY_LENGTH} bytes, got {len(key)}")

    # Generate IV if not provided
    if iv is None:
        iv = generate_iv()

    if len(iv) != IV_LENGTH:
        raise EncryptionError(f"IV must be {IV_LENGTH} bytes, got {len(iv)}")

    try:
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(iv, data, None)  # No additional authenticated data

        return iv, ciphertext

    except Exception as e:
        raise EncryptionError(f"Encryption failed: {e}") from e


def decrypt_data(ciphertext: bytes, key: bytes, iv: bytes) -> bytes:
    """Decrypt data using AES-256-GCM and verify authentication tag.

    Args:
        ciphertext: Encrypted data with authentication tag appended
        key: 32-byte encryption key (must be same as encryption key)
        iv: 12-byte IV/nonce (must be same as encryption IV)

    Returns:
        Decrypted plaintext data

    Raises:
        AuthenticationError: If authentication tag verification fails (data tampered)
        DecryptionError: If decryption fails for other reasons
    """
    if len(key) != KEY_LENGTH:
        raise DecryptionError(f"Key must be {KEY_LENGTH} bytes, got {len(key)}")

    if len(iv) != IV_LENGTH:
        raise DecryptionError(f"IV must be {IV_LENGTH} bytes, got {len(iv)}")

    if len(ciphertext) < TAG_LENGTH:
        raise DecryptionError(f"Ciphertext too short (must be at least {TAG_LENGTH} bytes)")

    try:
        aesgcm = AESGCM(key)
        plaintext = aesgcm.decrypt(iv, ciphertext, None)

        return plaintext

    except Exception as e:
        # Cryptography library raises InvalidTag for authentication failures
        if "InvalidTag" in str(type(e).__name__):
            raise AuthenticationError(
                "Authentication tag verification failed - data may be corrupted or tampered"
            ) from e

        raise DecryptionError(f"Decryption failed: {e}") from e


def verify_key_strength(passphrase: str) -> Tuple[bool, str]:
    """Verify passphrase meets minimum security requirements.

    Args:
        passphrase: Passphrase to verify

    Returns:
        Tuple of (is_valid, message)
        is_valid: True if passphrase meets minimum requirements
        message: Description of validation result
    """
    if len(passphrase) < 12:
        return False, "Passphrase must be at least 12 characters"

    if len(passphrase) < 16:
        return True, "Warning: Consider using 16+ characters for better security"

    # Check for basic character variety (not enforced, just recommended)
    has_upper = any(c.isupper() for c in passphrase)
    has_lower = any(c.islower() for c in passphrase)
    has_digit = any(c.isdigit() for c in passphrase)
    has_special = any(not c.isalnum() for c in passphrase)

    variety_count = sum([has_upper, has_lower, has_digit, has_special])

    if variety_count < 2:
        return True, "Consider using a mix of character types for better security"

    return True, "Passphrase strength: Good"
