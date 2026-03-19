"""Tests for file-level encryption."""

import pytest
import tempfile
from pathlib import Path

from mnb.crypto.file_crypto import (
    FileCrypto,
    get_encrypted_filename,
    is_encrypted_filename,
    get_original_filename,
    MAGIC_BYTES,
    HEADER_SIZE,
)
from mnb.crypto.encryption import derive_key, generate_salt, DecryptionError, AuthenticationError


@pytest.fixture
def file_crypto():
    """Provide FileCrypto instance."""
    return FileCrypto()


@pytest.fixture
def encryption_key():
    """Provide encryption key for testing."""
    return derive_key("test_passphrase", generate_salt())


@pytest.fixture
def temp_dir():
    """Provide temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestFileEncryption:
    """Tests for file encryption."""

    def test_encrypt_decrypt_small_file(self, file_crypto, encryption_key, temp_dir):
        """Encrypt and decrypt small file."""
        # Create test file
        original_file = temp_dir / "test.txt"
        original_content = b"This is a test file with some content."
        original_file.write_bytes(original_content)

        # Encrypt
        encrypted_file = temp_dir / "test.txt.enc"
        file_crypto.encrypt_file(original_file, encrypted_file, encryption_key)

        # Verify encrypted file exists and is different
        assert encrypted_file.exists()
        assert encrypted_file.read_bytes() != original_content

        # Decrypt
        decrypted_file = temp_dir / "test_decrypted.txt"
        file_crypto.decrypt_file(encrypted_file, decrypted_file, encryption_key)

        # Verify decrypted content matches original
        assert decrypted_file.read_bytes() == original_content

    def test_encrypt_decrypt_binary_file(self, file_crypto, encryption_key, temp_dir):
        """Encrypt and decrypt binary file."""
        # Create binary test file
        original_file = temp_dir / "binary.dat"
        original_content = bytes(range(256))  # All byte values 0-255
        original_file.write_bytes(original_content)

        # Encrypt and decrypt
        encrypted_file = temp_dir / "binary.dat.enc"
        decrypted_file = temp_dir / "binary_decrypted.dat"

        file_crypto.encrypt_file(original_file, encrypted_file, encryption_key)
        file_crypto.decrypt_file(encrypted_file, decrypted_file, encryption_key)

        # Verify
        assert decrypted_file.read_bytes() == original_content

    def test_encrypt_decrypt_large_file(self, file_crypto, encryption_key, temp_dir):
        """Encrypt and decrypt larger file (1 MB)."""
        # Create 1 MB file
        original_file = temp_dir / "large.bin"
        original_content = b"X" * (1024 * 1024)  # 1 MB of 'X'
        original_file.write_bytes(original_content)

        # Encrypt and decrypt
        encrypted_file = temp_dir / "large.bin.enc"
        decrypted_file = temp_dir / "large_decrypted.bin"

        file_crypto.encrypt_file(original_file, encrypted_file, encryption_key)
        file_crypto.decrypt_file(encrypted_file, decrypted_file, encryption_key)

        # Verify
        assert decrypted_file.read_bytes() == original_content

    def test_encrypted_file_has_header(self, file_crypto, encryption_key, temp_dir):
        """Encrypted file should have proper header."""
        original_file = temp_dir / "test.txt"
        original_file.write_bytes(b"content")

        encrypted_file = temp_dir / "test.txt.enc"
        file_crypto.encrypt_file(original_file, encrypted_file, encryption_key)

        # Read header
        with open(encrypted_file, 'rb') as f:
            header = f.read(HEADER_SIZE)

        # Check magic bytes
        assert header[:8] == MAGIC_BYTES

        # Check file is larger than header + original content
        original_size = original_file.stat().st_size
        encrypted_size = encrypted_file.stat().st_size
        # Header + content + authentication tag (16 bytes)
        assert encrypted_size >= HEADER_SIZE + original_size + 16

    def test_decrypt_with_wrong_key(self, file_crypto, temp_dir):
        """Decrypting with wrong key should raise AuthenticationError."""
        # Encrypt with key1
        key1 = derive_key("password1", generate_salt())
        original_file = temp_dir / "test.txt"
        original_file.write_bytes(b"secret data")

        encrypted_file = temp_dir / "test.txt.enc"
        file_crypto.encrypt_file(original_file, encrypted_file, key1)

        # Try to decrypt with key2
        key2 = derive_key("password2", generate_salt())
        decrypted_file = temp_dir / "test_decrypted.txt"

        with pytest.raises(AuthenticationError):
            file_crypto.decrypt_file(encrypted_file, decrypted_file, key2)

    def test_decrypt_tampered_file(self, file_crypto, encryption_key, temp_dir):
        """Decrypting tampered file should raise AuthenticationError."""
        # Create and encrypt file
        original_file = temp_dir / "test.txt"
        original_file.write_bytes(b"important data")

        encrypted_file = temp_dir / "test.txt.enc"
        file_crypto.encrypt_file(original_file, encrypted_file, encryption_key)

        # Tamper with encrypted file (modify a byte after the header)
        data = bytearray(encrypted_file.read_bytes())
        data[HEADER_SIZE + 10] ^= 0xFF  # Flip bits
        encrypted_file.write_bytes(bytes(data))

        # Try to decrypt
        decrypted_file = temp_dir / "test_decrypted.txt"

        with pytest.raises(AuthenticationError):
            file_crypto.decrypt_file(encrypted_file, decrypted_file, encryption_key)


class TestFileDetection:
    """Tests for encrypted file detection."""

    def test_is_encrypted_file_positive(self, file_crypto, encryption_key, temp_dir):
        """Should detect encrypted files."""
        original_file = temp_dir / "test.txt"
        original_file.write_bytes(b"content")

        encrypted_file = temp_dir / "test.txt.enc"
        file_crypto.encrypt_file(original_file, encrypted_file, encryption_key)

        assert file_crypto.is_encrypted_file(encrypted_file)

    def test_is_encrypted_file_negative(self, file_crypto, temp_dir):
        """Should not detect unencrypted files as encrypted."""
        plain_file = temp_dir / "plain.txt"
        plain_file.write_bytes(b"This is not encrypted")

        assert not file_crypto.is_encrypted_file(plain_file)

    def test_is_encrypted_file_wrong_magic(self, file_crypto, temp_dir):
        """File with wrong magic bytes should not be detected as encrypted."""
        fake_file = temp_dir / "fake.enc"
        fake_file.write_bytes(b"WRONGMAG" + b"0" * 248)

        assert not file_crypto.is_encrypted_file(fake_file)


class TestFilenameHandling:
    """Tests for encrypted filename handling."""

    def test_get_encrypted_filename_default(self):
        """Should append .enc extension by default."""
        assert get_encrypted_filename("file.txt") == "file.txt.enc"
        assert get_encrypted_filename("archive.tar.gz") == "archive.tar.gz.enc"

    def test_is_encrypted_filename(self):
        """Should detect .enc extension."""
        assert is_encrypted_filename("file.txt.enc")
        assert is_encrypted_filename("archive.tar.gz.enc")
        assert not is_encrypted_filename("file.txt")
        assert not is_encrypted_filename("file.enc.txt")  # .enc not at end

    def test_get_original_filename(self):
        """Should strip .enc extension."""
        assert get_original_filename("file.txt.enc") == "file.txt"
        assert get_original_filename("archive.tar.gz.enc") == "archive.tar.gz"
        assert get_original_filename("file.txt") == "file.txt"  # No .enc


class TestHeaderParsing:
    """Tests for header parsing."""

    def test_decrypt_file_too_small(self, file_crypto, encryption_key, temp_dir):
        """File smaller than header size should raise error."""
        small_file = temp_dir / "too_small.enc"
        small_file.write_bytes(b"short")

        decrypted_file = temp_dir / "out.txt"

        with pytest.raises(DecryptionError, match="too small"):
            file_crypto.decrypt_file(small_file, decrypted_file, encryption_key)

    def test_decrypt_invalid_magic(self, file_crypto, encryption_key, temp_dir):
        """File with invalid magic bytes should raise error."""
        invalid_file = temp_dir / "invalid.enc"
        # Create file with wrong magic bytes
        header = b"WRONGMAG" + b"\x00" * (HEADER_SIZE - 8)
        content = b"encrypted content here"
        invalid_file.write_bytes(header + content)

        decrypted_file = temp_dir / "out.txt"

        with pytest.raises(DecryptionError, match="Invalid magic bytes"):
            file_crypto.decrypt_file(invalid_file, decrypted_file, encryption_key)

    def test_decrypt_unsupported_version(self, file_crypto, encryption_key, temp_dir):
        """File with unsupported version should raise error."""
        # Create file with future version (999)
        import struct
        header = bytearray(HEADER_SIZE)
        header[0:8] = MAGIC_BYTES
        struct.pack_into('<I', header, 8, 999)  # Version 999

        future_file = temp_dir / "future.enc"
        future_file.write_bytes(bytes(header) + b"content")

        decrypted_file = temp_dir / "out.txt"

        with pytest.raises(DecryptionError, match="Unsupported file version"):
            file_crypto.decrypt_file(future_file, decrypted_file, encryption_key)


class TestEmptyAndSpecialFiles:
    """Tests for edge cases."""

    def test_encrypt_empty_file(self, file_crypto, encryption_key, temp_dir):
        """Should handle empty files."""
        empty_file = temp_dir / "empty.txt"
        empty_file.write_bytes(b"")

        encrypted_file = temp_dir / "empty.txt.enc"
        decrypted_file = temp_dir / "empty_decrypted.txt"

        file_crypto.encrypt_file(empty_file, encrypted_file, encryption_key)
        file_crypto.decrypt_file(encrypted_file, decrypted_file, encryption_key)

        assert decrypted_file.read_bytes() == b""

    def test_encrypt_single_byte_file(self, file_crypto, encryption_key, temp_dir):
        """Should handle single byte files."""
        tiny_file = temp_dir / "tiny.txt"
        tiny_file.write_bytes(b"X")

        encrypted_file = temp_dir / "tiny.txt.enc"
        decrypted_file = temp_dir / "tiny_decrypted.txt"

        file_crypto.encrypt_file(tiny_file, encrypted_file, encryption_key)
        file_crypto.decrypt_file(encrypted_file, decrypted_file, encryption_key)

        assert decrypted_file.read_bytes() == b"X"


class TestMultipleFilesUniqueness:
    """Tests for encrypting multiple files."""

    def test_same_content_different_ciphertext(self, file_crypto, encryption_key, temp_dir):
        """Encrypting same content twice should produce different encrypted files."""
        # Create two files with identical content
        file1 = temp_dir / "file1.txt"
        file2 = temp_dir / "file2.txt"
        content = b"identical content in both files"
        file1.write_bytes(content)
        file2.write_bytes(content)

        # Encrypt both
        enc1 = temp_dir / "file1.txt.enc"
        enc2 = temp_dir / "file2.txt.enc"
        file_crypto.encrypt_file(file1, enc1, encryption_key)
        file_crypto.encrypt_file(file2, enc2, encryption_key)

        # Encrypted files should be different (different IVs)
        assert enc1.read_bytes() != enc2.read_bytes()

        # But both should decrypt to same content
        dec1 = temp_dir / "dec1.txt"
        dec2 = temp_dir / "dec2.txt"
        file_crypto.decrypt_file(enc1, dec1, encryption_key)
        file_crypto.decrypt_file(enc2, dec2, encryption_key)

        assert dec1.read_bytes() == content
        assert dec2.read_bytes() == content
