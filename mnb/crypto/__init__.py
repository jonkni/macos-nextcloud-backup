"""Client-side encryption module for secure backups."""

from mnb.crypto.encryption import (
    generate_salt,
    generate_iv,
    derive_key,
    encrypt_data,
    decrypt_data,
)
from mnb.crypto.key_manager import KeyManager
from mnb.crypto.file_crypto import FileCrypto

__all__ = [
    'generate_salt',
    'generate_iv',
    'derive_key',
    'encrypt_data',
    'decrypt_data',
    'KeyManager',
    'FileCrypto',
]
