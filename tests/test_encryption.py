"""Tests for core encryption primitives."""

import pytest
from mnb.crypto.encryption import (
    generate_salt,
    generate_iv,
    derive_key,
    encrypt_data,
    decrypt_data,
    verify_key_strength,
    EncryptionError,
    DecryptionError,
    AuthenticationError,
    SALT_LENGTH,
    IV_LENGTH,
    KEY_LENGTH,
)


class TestSaltGeneration:
    """Tests for salt generation."""

    def test_generate_salt_length(self):
        """Salt should be correct length."""
        salt = generate_salt()
        assert len(salt) == SALT_LENGTH

    def test_generate_salt_randomness(self):
        """Each salt should be unique."""
        salt1 = generate_salt()
        salt2 = generate_salt()
        assert salt1 != salt2

    def test_generate_salt_type(self):
        """Salt should be bytes."""
        salt = generate_salt()
        assert isinstance(salt, bytes)


class TestIVGeneration:
    """Tests for IV generation."""

    def test_generate_iv_length(self):
        """IV should be correct length."""
        iv = generate_iv()
        assert len(iv) == IV_LENGTH

    def test_generate_iv_randomness(self):
        """Each IV should be unique."""
        iv1 = generate_iv()
        iv2 = generate_iv()
        assert iv1 != iv2

    def test_generate_iv_type(self):
        """IV should be bytes."""
        iv = generate_iv()
        assert isinstance(iv, bytes)


class TestKeyDerivation:
    """Tests for PBKDF2 key derivation."""

    def test_derive_key_length(self):
        """Derived key should be 32 bytes (256 bits)."""
        salt = generate_salt()
        key = derive_key("test_passphrase", salt)
        assert len(key) == KEY_LENGTH

    def test_derive_key_deterministic(self):
        """Same passphrase and salt should produce same key."""
        salt = generate_salt()
        key1 = derive_key("test_passphrase", salt)
        key2 = derive_key("test_passphrase", salt)
        assert key1 == key2

    def test_derive_key_different_salt(self):
        """Different salt should produce different key."""
        salt1 = generate_salt()
        salt2 = generate_salt()
        key1 = derive_key("test_passphrase", salt1)
        key2 = derive_key("test_passphrase", salt2)
        assert key1 != key2

    def test_derive_key_different_passphrase(self):
        """Different passphrase should produce different key."""
        salt = generate_salt()
        key1 = derive_key("passphrase1", salt)
        key2 = derive_key("passphrase2", salt)
        assert key1 != key2

    def test_derive_key_empty_passphrase(self):
        """Empty passphrase should raise error."""
        salt = generate_salt()
        with pytest.raises(EncryptionError, match="Passphrase cannot be empty"):
            derive_key("", salt)

    def test_derive_key_wrong_salt_length(self):
        """Wrong salt length should raise error."""
        with pytest.raises(EncryptionError, match="Salt must be"):
            derive_key("test", b"short_salt")

    def test_derive_key_low_iterations(self):
        """Too few iterations should raise error."""
        salt = generate_salt()
        with pytest.raises(EncryptionError, match="Iterations too low"):
            derive_key("test", salt, iterations=1000)


class TestEncryption:
    """Tests for AES-256-GCM encryption."""

    def test_encrypt_decrypt_roundtrip(self):
        """Encrypt and decrypt should recover original data."""
        plaintext = b"Hello, World! This is a test message."
        salt = generate_salt()
        key = derive_key("test_passphrase", salt)

        iv, ciphertext = encrypt_data(plaintext, key)
        decrypted = decrypt_data(ciphertext, key, iv)

        assert decrypted == plaintext

    def test_encrypt_produces_different_output(self):
        """Encrypting same data twice should produce different ciphertext (different IV)."""
        plaintext = b"test data"
        salt = generate_salt()
        key = derive_key("passphrase", salt)

        iv1, ciphertext1 = encrypt_data(plaintext, key)
        iv2, ciphertext2 = encrypt_data(plaintext, key)

        # Different IVs
        assert iv1 != iv2
        # Different ciphertexts
        assert ciphertext1 != ciphertext2

    def test_encrypt_with_provided_iv(self):
        """Can provide specific IV for encryption."""
        plaintext = b"test"
        key = derive_key("pass", generate_salt())
        iv = generate_iv()

        returned_iv, ciphertext = encrypt_data(plaintext, key, iv)

        assert returned_iv == iv

    def test_encrypt_wrong_key_length(self):
        """Wrong key length should raise error."""
        with pytest.raises(EncryptionError, match="Key must be"):
            encrypt_data(b"data", b"short_key")

    def test_encrypt_wrong_iv_length(self):
        """Wrong IV length should raise error."""
        key = derive_key("pass", generate_salt())
        with pytest.raises(EncryptionError, match="IV must be"):
            encrypt_data(b"data", key, b"short_iv")


class TestDecryption:
    """Tests for AES-256-GCM decryption."""

    def test_decrypt_wrong_key(self):
        """Decrypting with wrong key should raise AuthenticationError."""
        plaintext = b"secret message"
        key1 = derive_key("password1", generate_salt())
        key2 = derive_key("password2", generate_salt())

        iv, ciphertext = encrypt_data(plaintext, key1)

        with pytest.raises(AuthenticationError, match="Authentication tag"):
            decrypt_data(ciphertext, key2, iv)

    def test_decrypt_tampered_ciphertext(self):
        """Decrypting tampered data should raise AuthenticationError."""
        plaintext = b"important data"
        key = derive_key("password", generate_salt())

        iv, ciphertext = encrypt_data(plaintext, key)

        # Tamper with ciphertext
        tampered = bytearray(ciphertext)
        tampered[0] ^= 0xFF  # Flip bits in first byte
        tampered_bytes = bytes(tampered)

        with pytest.raises(AuthenticationError):
            decrypt_data(tampered_bytes, key, iv)

    def test_decrypt_wrong_iv(self):
        """Decrypting with wrong IV should raise AuthenticationError."""
        plaintext = b"data"
        key = derive_key("pass", generate_salt())

        iv1, ciphertext = encrypt_data(plaintext, key)
        iv2 = generate_iv()

        with pytest.raises(AuthenticationError):
            decrypt_data(ciphertext, key, iv2)

    def test_decrypt_wrong_key_length(self):
        """Wrong key length should raise DecryptionError."""
        with pytest.raises(DecryptionError, match="Key must be"):
            decrypt_data(b"data", b"short", generate_iv())

    def test_decrypt_wrong_iv_length(self):
        """Wrong IV length should raise DecryptionError."""
        key = derive_key("pass", generate_salt())
        with pytest.raises(DecryptionError, match="IV must be"):
            decrypt_data(b"data" * 10, key, b"short")

    def test_decrypt_too_short_ciphertext(self):
        """Too short ciphertext should raise DecryptionError."""
        key = derive_key("pass", generate_salt())
        iv = generate_iv()
        with pytest.raises(DecryptionError, match="too short"):
            decrypt_data(b"short", key, iv)


class TestPassphraseStrength:
    """Tests for passphrase strength verification."""

    def test_too_short_passphrase(self):
        """Passphrase < 12 characters should fail."""
        is_valid, message = verify_key_strength("short")
        assert not is_valid
        assert "12 characters" in message

    def test_minimum_length_passphrase(self):
        """Passphrase exactly 12 characters should pass."""
        is_valid, message = verify_key_strength("123456789012")
        assert is_valid

    def test_weak_but_acceptable(self):
        """12-15 char passphrase should warn but accept."""
        is_valid, message = verify_key_strength("12345678901234")
        assert is_valid
        assert "16+" in message

    def test_good_passphrase(self):
        """16+ character passphrase with variety should be good."""
        is_valid, message = verify_key_strength("MyGoodPassphrase123!")
        assert is_valid
        assert "Good" in message or "Warning" not in message

    def test_long_but_low_variety(self):
        """Long passphrase with low variety gets suggestion."""
        is_valid, message = verify_key_strength("aaaaaaaaaaaaaaaa")
        assert is_valid
        # Should suggest variety, but still accept

    def test_passphrase_variety_detection(self):
        """Should detect character variety."""
        # Mix of upper, lower, digit, special
        is_valid1, msg1 = verify_key_strength("Abc123!@#$%^")
        assert is_valid1

        # Only lowercase
        is_valid2, msg2 = verify_key_strength("abcdefghijklmn")
        assert is_valid2


class TestEncryptionIntegration:
    """Integration tests for full encryption workflow."""

    def test_full_workflow(self):
        """Test complete encryption workflow."""
        # User provides passphrase
        passphrase = "MySecurePassphrase123!"

        # Verify passphrase
        is_valid, message = verify_key_strength(passphrase)
        assert is_valid

        # Generate salt (done once, stored in config)
        salt = generate_salt()

        # Derive key (slow operation, result stored in Keychain)
        key = derive_key(passphrase, salt)

        # Encrypt some data
        original_data = b"Sensitive backup data: SSH keys, credentials, etc."
        iv, ciphertext = encrypt_data(original_data, key)

        # Store ciphertext (this would go to Nextcloud)
        # Later, retrieve and decrypt
        decrypted_data = decrypt_data(ciphertext, key, iv)

        assert decrypted_data == original_data

    def test_multiple_files_unique_ivs(self):
        """Each file should get unique IV."""
        key = derive_key("password", generate_salt())
        data = b"file content"

        ivs = []
        for _ in range(10):
            iv, _ = encrypt_data(data, key)
            ivs.append(iv)

        # All IVs should be unique
        assert len(set(ivs)) == len(ivs)
