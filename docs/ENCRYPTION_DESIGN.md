# Client-Side Encryption Design

**Status:** Design Phase
**Priority:** CRITICAL (Blocker for production use)
**Author:** Design collaboration
**Date:** 2026-03-19

## Overview

Implement client-side encryption to protect sensitive backup data before upload to Nextcloud. This is the #1 priority feature to make the backup tool production-ready.

## Problem Statement

Currently, files are uploaded to Nextcloud **unencrypted**, exposing sensitive data to:
- Nextcloud server administrators
- Anyone with server access
- Potential server compromises

Backups include highly sensitive data:
- SSH private keys (`~/.ssh/`)
- API tokens and credentials (`~/.config/`, `~/.aws/`)
- Application secrets
- Personal documents

**This makes the tool unsuitable for production use.**

## Requirements

### Functional Requirements

1. **Encrypt files before upload** - All file content encrypted client-side
2. **Transparent to Nextcloud** - Encrypted files stored as regular files
3. **Passphrase-based encryption** - User provides passphrase, derived to encryption key
4. **Metadata protection** - Consider encrypting filenames/paths
5. **Key management** - Secure storage of encryption key
6. **Restore capability** - Decrypt files during restore with correct passphrase
7. **Performance** - Minimal impact on backup/restore speed
8. **Backwards compatibility** - Support restoring old unencrypted backups

### Non-Functional Requirements

1. **Security** - Use industry-standard encryption (AES-256-GCM)
2. **Usability** - Simple setup, minimal user friction
3. **Reliability** - Encryption failures must not corrupt backups
4. **Auditability** - Clear logging of encryption operations
5. **Testability** - Comprehensive tests for encryption/decryption

## Design Decisions

### 1. Encryption Algorithm: AES-256-GCM

**Choice:** AES-256 in GCM (Galois/Counter Mode)

**Rationale:**
- Industry standard, NIST approved
- GCM provides authenticated encryption (detects tampering)
- Fast (hardware acceleration available)
- 256-bit key provides strong security

**Alternatives Considered:**
- ChaCha20-Poly1305: Good alternative, but AES-GCM more widely supported
- AES-CBC: Older mode, doesn't provide authentication

### 2. Key Derivation: PBKDF2-HMAC-SHA256

**Choice:** PBKDF2 with HMAC-SHA256, 600,000 iterations

**Rationale:**
- Standard key derivation function
- Slow enough to resist brute force
- 600,000 iterations meets OWASP 2023 recommendations
- Widely supported in Python (cryptography library)

**Alternatives Considered:**
- Argon2: Better resistance to GPU attacks, but less portable
- scrypt: Good, but PBKDF2 sufficient for our use case

### 3. File-Level Encryption

**Choice:** Encrypt each file individually with unique IV

**Rationale:**
- Parallelizable (can encrypt files concurrently)
- Failure in one file doesn't affect others
- Easier to implement incremental backups
- Each file gets unique IV (nonce) for security

**Alternatives Considered:**
- Archive-level encryption: Would require re-encrypting entire archive on changes
- Block-level encryption: More complex, less portable

### 4. Filename Encryption: Optional, Default Off

**Choice:** Keep filenames unencrypted by default, offer encryption as option

**Rationale:**
- **Default off:** Easier to browse backups in Nextcloud web interface
- **Optional:** Users with high security needs can enable
- **Tradeoff:** Filenames reveal some information, but content is protected

**Implementation:**
- Unencrypted mode: `file.txt` → `file.txt.enc`
- Encrypted mode: `file.txt` → `<hex-encoded-encrypted-name>.enc`

### 5. Metadata Storage

**Choice:** Store encryption metadata in file header

**Encrypted File Format:**
```
[Header: 256 bytes]
  - Magic bytes: "MNBENC01" (8 bytes)
  - Version: 1 (4 bytes)
  - Salt: Random 32 bytes (for key derivation)
  - IV/Nonce: Random 16 bytes (for AES-GCM)
  - Original filename length: 4 bytes
  - Original filename: Encrypted (variable, padded to 192 bytes)
  - Reserved: Padding to 256 bytes
[Encrypted Content]
  - File data encrypted with AES-256-GCM
  - Authentication tag appended (16 bytes)
```

**Rationale:**
- Self-contained: All info needed for decryption in the file
- Versioned: Can evolve format in future
- Each file has unique salt and IV

### 6. Key Storage: macOS Keychain

**Choice:** Store derived encryption key in macOS Keychain

**Rationale:**
- Already using Keychain for Nextcloud password
- Secure, OS-managed storage
- User doesn't need to enter passphrase for every backup

**First-time setup:**
1. User provides encryption passphrase
2. Key derived with PBKDF2 (slow, 600k iterations)
3. Derived key stored in Keychain
4. Salt stored in config file (not secret)

**Subsequent backups:**
1. Retrieve derived key from Keychain
2. Use directly (no re-derivation needed)

**Alternative:** Require passphrase each time
- More secure (no key storage)
- Less usable (blocks automation)
- Not chosen due to scheduling requirement

## Architecture

### New Components

```
mnb/
├── crypto/
│   ├── __init__.py
│   ├── encryption.py      # Core encryption/decryption
│   ├── key_manager.py     # Key derivation and storage
│   └── file_crypto.py     # File-level encryption wrapper
```

### Component Responsibilities

**crypto/encryption.py:**
- AES-256-GCM encryption/decryption primitives
- Key derivation (PBKDF2)
- IV/salt generation
- Authentication tag verification

**crypto/key_manager.py:**
- Store/retrieve encryption key from Keychain
- Generate salts
- Handle key derivation
- Config integration

**crypto/file_crypto.py:**
- Encrypt file with header format
- Decrypt file, verify authentication
- Handle filename encryption (optional)
- Stream large files efficiently

### Integration Points

**backup_engine.py:**
- Check if encryption enabled in config
- Encrypt files before upload
- Store `.enc` extension in metadata

**restore (future):**
- Detect encrypted files (`.enc` extension or header)
- Decrypt after download
- Verify authentication tag

**config/manager.py:**
- Add encryption configuration options
- Store salt in config file
- Encryption on/off flag

## Configuration

New config options in `~/.config/mnb/config.yml`:

```yaml
encryption:
  enabled: false                    # Enable/disable encryption
  algorithm: aes-256-gcm            # Encryption algorithm (future-proofing)
  key_derivation:
    method: pbkdf2-hmac-sha256      # Key derivation function
    iterations: 600000              # PBKDF2 iterations
    salt: <hex-encoded-salt>        # Salt for key derivation (not secret)
  encrypt_filenames: false          # Encrypt filenames (default: false)
```

## User Experience

### Initial Setup

```bash
# Enable encryption
mnb config set encryption.enabled true

# User prompted for passphrase
Enter encryption passphrase:
Confirm passphrase:

# Key derived and stored
✓ Encryption key derived and stored securely
✓ Encryption enabled

# Salt saved to config
# Derived key saved to Keychain
```

### Changing Passphrase

```bash
# Change encryption passphrase
mnb crypto change-passphrase

# Requires old passphrase
Current passphrase:
New passphrase:
Confirm new passphrase:

# Derives new key, stores in Keychain
✓ Encryption passphrase updated
```

### Disabling Encryption

```bash
# Warning: Future backups will be unencrypted
mnb config set encryption.enabled false

Warning: Future backups will be UNENCRYPTED
Existing encrypted backups remain encrypted
Continue? [y/N]: y

✓ Encryption disabled
```

### Restore (Future)

```bash
# Restore automatically detects encrypted files
mnb restore --snapshot <id> --path ~/Documents/file.txt

# If file is encrypted, prompts for passphrase
File is encrypted. Enter passphrase:

# Or retrieve from Keychain automatically
✓ Using stored encryption key
✓ File decrypted and restored
```

## Security Considerations

### Threats Mitigated

1. ✅ **Server compromise** - Encrypted files useless without passphrase
2. ✅ **Admin access** - Nextcloud admins cannot read file contents
3. ✅ **Backup theft** - Stolen backup files cannot be decrypted
4. ✅ **Man-in-the-middle** - Already using HTTPS; encryption adds defense in depth

### Remaining Threats

1. ⚠️ **Keychain compromise** - If macOS Keychain compromised, key exposed
   - Mitigation: OS-level security, user must secure their Mac
2. ⚠️ **Metadata leakage** - Filenames/sizes/timestamps visible (unless filename encryption enabled)
   - Mitigation: Optional filename encryption
3. ⚠️ **Passphrase weakness** - Weak passphrase vulnerable to brute force
   - Mitigation: Passphrase strength requirements, 600k PBKDF2 iterations
4. ⚠️ **Key in memory** - Key present in memory during backup
   - Mitigation: Memory cleared after use (Python limitations)

### Passphrase Requirements

**Enforce minimum security:**
- Minimum length: 12 characters
- Recommended: 16+ characters with mix of character types
- Suggest using passphrase (multiple words) vs password

**Validation:**
```python
def validate_passphrase(passphrase: str) -> tuple[bool, str]:
    if len(passphrase) < 12:
        return False, "Passphrase must be at least 12 characters"
    if len(passphrase) < 16:
        return True, "Warning: Consider using 16+ characters for better security"
    return True, "Passphrase accepted"
```

### Key Rotation

**Not implemented initially**, but design supports it:
- Change passphrase → derive new key → store in Keychain
- Old encrypted files remain encrypted with old key
- Future files encrypted with new key
- Metadata tracks which key was used (future enhancement)

## Implementation Plan

### Phase 1: Core Encryption (Week 1)

**Tasks:**
1. Create `crypto/` module structure
2. Implement `encryption.py`:
   - AES-256-GCM encryption/decryption functions
   - PBKDF2 key derivation
   - IV/salt generation
   - Unit tests
3. Implement `key_manager.py`:
   - Keychain integration
   - Salt management
   - Config integration
   - Unit tests
4. Implement `file_crypto.py`:
   - File header format
   - Encrypt/decrypt file functions
   - Stream large files efficiently
   - Unit tests

**Deliverables:**
- Working encryption/decryption library
- Comprehensive unit tests
- Documentation

### Phase 2: Backup Integration (Week 2)

**Tasks:**
1. Update `backup_engine.py`:
   - Check encryption config
   - Encrypt files before upload
   - Add `.enc` extension
   - Update metadata
2. Add `mnb crypto` CLI commands:
   - `mnb crypto enable` - Enable encryption, set passphrase
   - `mnb crypto disable` - Disable encryption
   - `mnb crypto change-passphrase` - Change passphrase
   - `mnb crypto status` - Show encryption status
3. Update documentation:
   - QUICKSTART.md - Encryption setup
   - README.md - Update security status
4. Integration tests

**Deliverables:**
- Encrypted backups working
- CLI commands functional
- Documentation updated

### Phase 3: Restore & Polish (Week 3)

**Tasks:**
1. Implement restore with decryption:
   - Detect encrypted files
   - Decrypt during restore
   - Verify authentication tags
2. Add optional filename encryption
3. Performance optimization:
   - Benchmark encryption overhead
   - Optimize for large files
4. Security audit:
   - Code review
   - Penetration testing setup
5. Update all docs to remove security warnings

**Deliverables:**
- Full encrypt/decrypt cycle working
- Production-ready encryption
- Remove "NOT PRODUCTION READY" warnings

## Testing Strategy

### Unit Tests

**crypto/encryption.py:**
- Test AES-256-GCM encryption/decryption
- Test key derivation with known vectors
- Test IV uniqueness
- Test authentication tag verification
- Test error cases (wrong key, corrupted data)

**crypto/key_manager.py:**
- Test Keychain storage/retrieval
- Test salt generation/storage
- Test config integration
- Mock Keychain for CI/CD

**crypto/file_crypto.py:**
- Test file encryption/decryption roundtrip
- Test large files (streaming)
- Test header format parsing
- Test filename encryption
- Test backward compatibility with unencrypted files

### Integration Tests

1. **Full backup with encryption:**
   - Enable encryption
   - Run backup
   - Verify files uploaded with `.enc` extension
   - Download and decrypt manually
   - Verify contents match original

2. **Restore with decryption:**
   - Encrypt and backup files
   - Delete local files
   - Restore from encrypted backup
   - Verify restored files match original

3. **Mixed encrypted/unencrypted:**
   - Backup some files unencrypted
   - Enable encryption
   - Backup more files (encrypted)
   - Restore both types
   - Verify both work correctly

4. **Passphrase change:**
   - Create encrypted backup
   - Change passphrase
   - Create another backup
   - Restore from both backups
   - Verify both decrypt correctly

### Security Tests

1. **Verify encryption strength:**
   - Encrypt known plaintext
   - Verify output is indistinguishable from random
   - Test IV uniqueness

2. **Authentication:**
   - Tamper with encrypted file
   - Verify decryption fails with authentication error

3. **Key derivation:**
   - Verify 600k iterations actually performed
   - Test different salts produce different keys

## Performance Considerations

### Encryption Overhead

**Expected impact:**
- AES-256-GCM: ~50-200 MB/s (software)
- Hardware AES: 500-2000 MB/s (if available)
- Overhead: ~5-20% for most backups (network is bottleneck)

**Optimization strategies:**
1. Use hardware AES if available (cryptography library handles this)
2. Encrypt files in parallel (already doing parallel uploads)
3. Stream large files (don't load entire file in memory)

### Memory Usage

**Considerations:**
- Don't load entire file for encryption
- Stream encryption: Read chunk → encrypt → upload
- Target: <100 MB memory overhead for encryption

**Implementation:**
```python
def encrypt_file_stream(input_path, output_path, key, chunk_size=1024*1024):
    """Encrypt file in chunks to limit memory usage."""
    encryptor = Cipher(
        algorithms.AES(key),
        modes.GCM(iv),
        backend=default_backend()
    ).encryptor()

    with open(input_path, 'rb') as fin:
        with open(output_path, 'wb') as fout:
            # Write header first
            fout.write(create_header(...))

            # Encrypt in chunks
            while chunk := fin.read(chunk_size):
                fout.write(encryptor.update(chunk))

            # Write final block and tag
            fout.write(encryptor.finalize())
            fout.write(encryptor.tag)
```

## Migration Path

### For Existing Users

**Users with existing unencrypted backups:**

1. **Enable encryption:**
   ```bash
   mnb crypto enable
   ```

2. **Continue backing up:**
   - New/changed files: Encrypted
   - Unchanged files: Reference old unencrypted versions

3. **Full re-backup (optional):**
   ```bash
   mnb backup --initial  # Re-upload everything encrypted
   mnb clean --keep-last 1  # Remove old unencrypted backups
   ```

**Automatic detection:**
- Metadata tracks whether file is encrypted
- Restore automatically detects encrypted vs unencrypted
- No user intervention needed

### Database Schema Update

Add to `files` table:
```sql
ALTER TABLE files ADD COLUMN encrypted BOOLEAN DEFAULT 0;
ALTER TABLE files ADD COLUMN encryption_version INTEGER DEFAULT NULL;
```

## Open Questions

1. **Filename encryption default?**
   - Option A: Default ON (max security, harder to browse)
   - Option B: Default OFF (easier to use, some metadata leakage)
   - **Recommendation:** Default OFF, document the tradeoff

2. **Key rotation strategy?**
   - Should we support re-encrypting old backups with new key?
   - Or just accept old backups use old key?
   - **Recommendation:** Accept old keys, don't auto-rotate (too complex)

3. **Compression before encryption?**
   - Encrypted data doesn't compress well
   - Compress before encrypt? Adds complexity
   - **Recommendation:** Skip compression initially, add if needed

4. **Verify encryption in CI/CD?**
   - Need test Nextcloud instance
   - Or mock encryption tests?
   - **Recommendation:** Unit tests in CI, manual integration tests

## Success Criteria

**Encryption is ready for production when:**

1. ✅ All files encrypted with AES-256-GCM
2. ✅ Passphrase-based key derivation working
3. ✅ Keys stored securely in Keychain
4. ✅ Encrypt/decrypt roundtrip successful
5. ✅ Authentication tags verified on decrypt
6. ✅ Performance acceptable (<20% overhead)
7. ✅ Comprehensive tests passing (unit + integration)
8. ✅ Documentation complete
9. ✅ Security review conducted
10. ✅ All "NOT PRODUCTION READY" warnings removed

## References

- [NIST AES-GCM Specification](https://csrc.nist.gov/publications/detail/sp/800-38d/final)
- [OWASP Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)
- [Python cryptography library](https://cryptography.io/)
- [PBKDF2 Recommendations](https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication800-132.pdf)

## Next Steps

1. Review this design document
2. Get feedback on design decisions
3. Create implementation tasks
4. Begin Phase 1 implementation
