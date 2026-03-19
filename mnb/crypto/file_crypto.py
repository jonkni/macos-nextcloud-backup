"""File-level encryption with streaming support for large files."""

import struct
import logging
from pathlib import Path
from typing import Optional, BinaryIO

from mnb.crypto.encryption import (
    generate_iv,
    encrypt_data,
    decrypt_data,
    EncryptionError,
    DecryptionError,
    AuthenticationError,
)


# File format constants
MAGIC_BYTES = b'MNBENC01'  # 8 bytes - identifies encrypted files
VERSION = 1  # 4 bytes - format version
HEADER_SIZE = 256  # Total header size in bytes
ORIGINAL_FILENAME_MAX = 192  # Max bytes for encrypted filename in header
CHUNK_SIZE = 1024 * 1024  # 1 MB chunks for streaming


class FileCrypto:
    """Handles file encryption and decryption with header format."""

    def __init__(self):
        """Initialize file crypto handler."""
        self.logger = logging.getLogger(__name__)

    def encrypt_file(
        self,
        input_path: Path,
        output_path: Path,
        key: bytes,
        encrypt_filename: bool = False
    ) -> None:
        """Encrypt a file with header format.

        File format:
        [Header: 256 bytes]
          - Magic bytes: "MNBENC01" (8 bytes)
          - Version: 1 (4 bytes)
          - IV: Random 12 bytes
          - Reserved: Padding (232 bytes)
        [Encrypted Content]
          - File data encrypted with AES-256-GCM
          - Authentication tag included (16 bytes)

        Args:
            input_path: Path to file to encrypt
            output_path: Path for encrypted output
            key: 32-byte encryption key
            encrypt_filename: If True, encrypt filename in header (not implemented yet)

        Raises:
            EncryptionError: If encryption fails
        """
        try:
            # Read entire file (for now - will optimize for streaming later)
            with open(input_path, 'rb') as f:
                plaintext = f.read()

            # Generate IV
            iv = generate_iv()

            # Encrypt data
            _, ciphertext = encrypt_data(plaintext, key, iv)

            # Build header
            header = self._build_header(iv)

            # Write encrypted file
            with open(output_path, 'wb') as f:
                f.write(header)
                f.write(ciphertext)

            self.logger.debug(f"Encrypted {input_path} -> {output_path}")

        except EncryptionError:
            raise
        except Exception as e:
            raise EncryptionError(f"Failed to encrypt file {input_path}: {e}") from e

    def decrypt_file(
        self,
        input_path: Path,
        output_path: Path,
        key: bytes
    ) -> None:
        """Decrypt a file with header format.

        Args:
            input_path: Path to encrypted file
            output_path: Path for decrypted output
            key: 32-byte encryption key (must match encryption key)

        Raises:
            DecryptionError: If decryption fails
            AuthenticationError: If authentication tag verification fails
        """
        try:
            # Read encrypted file
            with open(input_path, 'rb') as f:
                # Read and parse header
                header_data = f.read(HEADER_SIZE)
                if len(header_data) < HEADER_SIZE:
                    raise DecryptionError(f"File too small (< {HEADER_SIZE} bytes)")

                iv = self._parse_header(header_data)

                # Read encrypted content
                ciphertext = f.read()

            # Decrypt data
            plaintext = decrypt_data(ciphertext, key, iv)

            # Write decrypted file
            with open(output_path, 'wb') as f:
                f.write(plaintext)

            self.logger.debug(f"Decrypted {input_path} -> {output_path}")

        except (DecryptionError, AuthenticationError):
            raise
        except Exception as e:
            raise DecryptionError(f"Failed to decrypt file {input_path}: {e}") from e

    def is_encrypted_file(self, file_path: Path) -> bool:
        """Check if a file is encrypted (has valid header).

        Args:
            file_path: Path to file to check

        Returns:
            True if file appears to be encrypted with our format
        """
        try:
            with open(file_path, 'rb') as f:
                magic = f.read(8)
                return magic == MAGIC_BYTES

        except Exception:
            return False

    def _build_header(self, iv: bytes) -> bytes:
        """Build file header.

        Format:
        - Magic bytes: 8 bytes
        - Version: 4 bytes (uint32)
        - IV: 12 bytes
        - Reserved: 232 bytes (padding for future use)

        Args:
            iv: 12-byte IV/nonce

        Returns:
            256-byte header
        """
        header = bytearray(HEADER_SIZE)

        # Magic bytes
        header[0:8] = MAGIC_BYTES

        # Version (uint32, little-endian)
        struct.pack_into('<I', header, 8, VERSION)

        # IV
        header[12:24] = iv

        # Reserved space (24:256) is already zeros

        return bytes(header)

    def _parse_header(self, header_data: bytes) -> bytes:
        """Parse file header.

        Args:
            header_data: 256-byte header

        Returns:
            12-byte IV

        Raises:
            DecryptionError: If header is invalid
        """
        if len(header_data) != HEADER_SIZE:
            raise DecryptionError(f"Invalid header size: {len(header_data)}")

        # Check magic bytes
        magic = header_data[0:8]
        if magic != MAGIC_BYTES:
            raise DecryptionError(
                f"Invalid magic bytes: {magic.hex()} (expected {MAGIC_BYTES.hex()})"
            )

        # Parse version
        version = struct.unpack('<I', header_data[8:12])[0]
        if version != VERSION:
            raise DecryptionError(
                f"Unsupported file version: {version} (current version: {VERSION})"
            )

        # Extract IV
        iv = header_data[12:24]

        return iv

    def encrypt_file_stream(
        self,
        input_file: BinaryIO,
        output_file: BinaryIO,
        key: bytes,
        chunk_size: int = CHUNK_SIZE
    ) -> None:
        """Encrypt file using streaming (for large files).

        Note: Not yet implemented - currently uses whole-file encryption.
        This is a placeholder for future optimization.

        Args:
            input_file: Input file handle (opened in 'rb' mode)
            output_file: Output file handle (opened in 'wb' mode)
            key: 32-byte encryption key
            chunk_size: Size of chunks to process (default: 1 MB)

        Raises:
            NotImplementedError: This is a placeholder for future implementation
        """
        raise NotImplementedError("Streaming encryption not yet implemented")

    def decrypt_file_stream(
        self,
        input_file: BinaryIO,
        output_file: BinaryIO,
        key: bytes,
        chunk_size: int = CHUNK_SIZE
    ) -> None:
        """Decrypt file using streaming (for large files).

        Note: Not yet implemented - currently uses whole-file decryption.
        This is a placeholder for future optimization.

        Args:
            input_file: Input file handle (opened in 'rb' mode)
            output_file: Output file handle (opened in 'wb' mode)
            key: 32-byte encryption key
            chunk_size: Size of chunks to process (default: 1 MB)

        Raises:
            NotImplementedError: This is a placeholder for future implementation
        """
        raise NotImplementedError("Streaming decryption not yet implemented")


def get_encrypted_filename(original_filename: str, encrypt_filename: bool = False) -> str:
    """Get the encrypted version of a filename.

    Args:
        original_filename: Original filename
        encrypt_filename: If True, encrypt the filename (not implemented yet)

    Returns:
        Encrypted filename with .enc extension

    Examples:
        get_encrypted_filename("file.txt") -> "file.txt.enc"
        get_encrypted_filename("file.txt", True) -> "<encrypted-hash>.enc" (future)
    """
    if encrypt_filename:
        # Future: Implement filename encryption
        # For now, just append .enc
        pass

    # Default: Keep filename readable, add .enc extension
    return f"{original_filename}.enc"


def is_encrypted_filename(filename: str) -> bool:
    """Check if filename appears to be encrypted.

    Args:
        filename: Filename to check

    Returns:
        True if filename ends with .enc
    """
    return filename.endswith('.enc')


def get_original_filename(encrypted_filename: str) -> str:
    """Get original filename from encrypted filename.

    Args:
        encrypted_filename: Encrypted filename (e.g., "file.txt.enc")

    Returns:
        Original filename (e.g., "file.txt")

    Examples:
        get_original_filename("file.txt.enc") -> "file.txt"
        get_original_filename("archive.tar.gz.enc") -> "archive.tar.gz"
    """
    if encrypted_filename.endswith('.enc'):
        return encrypted_filename[:-4]  # Remove .enc extension

    return encrypted_filename
