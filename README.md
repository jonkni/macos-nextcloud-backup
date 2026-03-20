# macOS Nextcloud Backup

Time Machine-like incremental backup solution for macOS to Nextcloud with client-side encryption.

## 🔐 Security Features

**Production Ready - Full Client-Side Encryption**

This backup tool provides enterprise-grade security for your backups:

- ✅ **AES-256-GCM encryption** - Files encrypted before upload
- ✅ **Authenticated encryption** - Tampering detection with cryptographic verification
- ✅ **Secure key derivation** - PBKDF2-HMAC-SHA256 (600,000 iterations)
- ✅ **macOS Keychain integration** - Encryption keys stored securely, never on disk
- ✅ **Zero-knowledge backup** - Nextcloud administrators cannot access your files

**Your sensitive data is protected:**
- SSH keys, credentials, and configuration files encrypted before upload
- Authentication tags detect any file tampering or corruption
- Encryption keys never leave your Mac (stored in macOS Keychain)

## Overview

This tool provides automated, incremental backups of your macOS system to a Nextcloud instance via WebDAV. It's designed for users who want:
- Time Machine-style backup functionality
- Remote storage on Nextcloud instead of local drives
- Selective backup with smart exclusions
- Minimal storage footprint with deduplication

## Features

### Core Functionality
- **Client-Side Encryption**: AES-256-GCM authenticated encryption with PBKDF2 key derivation
  - Files encrypted before upload (zero-knowledge backups)
  - Tampering detection with authentication tags
  - Encryption keys stored securely in macOS Keychain
  - Automatic decryption during restore
- **Incremental Backups**: Only changed files are uploaded, similar to Time Machine
- **High Performance**: Optimized WebDAV with connection pooling, parallel uploads, and caching (2-5x faster)
- **Metadata-Based Deduplication**: Unchanged files referenced (not re-uploaded) to save space
- **Smart Exclusions**: Automatically exclude:
  - iCloud-synced folders (Photos, Desktop, Documents if synced)
  - Downloads folder
  - Git repositories (.git directories)
  - Build artifacts (node_modules, target, dist, etc.)
  - System cache and temporary files
  - Large media files already backed up elsewhere
- **Scheduled Backups**: Automatic hourly/daily/weekly backups via launchd
- **Multiple Machine Support**: Manage backups for all your MacBooks
- **Resumable Backups**: Automatic retry on network failures

### Interface
- **CLI Tool**: Command-line interface for scripting and automation
- **GUI Application**: macOS menu bar app for quick status, backups, and restore
- **Web Dashboard** (planned): View backup status from any device

## Architecture

### Components

1. **Backup Engine** (Python)
   - File scanning and change detection
   - WebDAV client for Nextcloud
   - Incremental snapshot management
   - Exclude pattern matching

2. **Configuration Manager**
   - YAML-based configuration
   - Per-machine settings
   - Custom include/exclude rules

3. **Scheduler**
   - launchd integration for macOS
   - Configurable backup intervals
   - Smart retry logic

4. **Storage Manager**
   - Snapshot versioning
   - Storage quota management
   - Automatic cleanup of old backups

### Backup Structure

```
nextcloud://backup/
├── machine1/
│   ├── snapshots/
│   │   ├── 2026-03-17T10:00:00/
│   │   ├── 2026-03-17T11:00:00/
│   │   └── latest -> 2026-03-17T11:00:00
│   ├── metadata/
│   │   └── file_index.db
│   └── config.yml
├── machine2/
└── machine3/
```

## Storage Requirements

### Typical MacBook Backup (Estimated)

For a developer's MacBook with selective backup:

| Category | Size |
|----------|------|
| Documents & Projects | 10-20 GB |
| Configuration Files | 100-500 MB |
| Application Data | 5-10 GB |
| System Preferences | 50-100 MB |
| **Initial Backup** | **15-30 GB** |
| **Incremental (daily)** | **500 MB - 2 GB** |

### For 3 MacBooks with 100 GB Nextcloud

- **Initial**: 45-90 GB (3x 15-30 GB)
- **After 1 week**: 55-100 GB
- **Recommendation**: 100 GB is tight, 200-300 GB recommended for comfort

**Note**: With aggressive exclusions and deduplication, 100 GB may work if you:
- Keep only 2-3 weeks of history
- Exclude all media files
- Monitor and clean old snapshots regularly

## Installation

### Prerequisites
- macOS 11.0 or later
- Python 3.9+
- Nextcloud instance with WebDAV access
- Storage quota: 50+ GB per machine
- **App password** from Nextcloud (required if 2FA is enabled)

### Important: Two-Factor Authentication

If your Nextcloud has 2FA enabled (like share.educloud.no):

1. Log in to Nextcloud web interface
2. Go to **Settings** → **Security** → **Devices & sessions**
3. Create a new **app password** with a name like "MacBook Backup"
4. Copy the generated password (format: `xxxxx-xxxxx-xxxxx-xxxxx-xxxxx`)
5. Use this app password (not your regular password) when running `mnb init`

See [QUICKSTART.md](QUICKSTART.md) for detailed instructions.

### Quick Start

```bash
# Install from source
git clone https://github.com/YOUR_USERNAME/macos-nextcloud-backup.git
cd macos-nextcloud-backup
pip install -e .

# Configure (will prompt for Nextcloud credentials)
mnb init

# Enable encryption (strongly recommended)
mnb crypto enable
# You'll be prompted to create a strong passphrase
# Passphrase stored securely in macOS Keychain

# Run first encrypted backup
mnb backup --initial

# Enable automatic backups
mnb schedule --interval hourly
```

**Security Best Practices:**
- Enable encryption before your first backup (`mnb crypto enable`)
- Use a strong, unique passphrase for encryption
- Backup your encryption passphrase securely (if lost, backups cannot be decrypted)
- See [ENCRYPTION_DESIGN.md](docs/ENCRYPTION_DESIGN.md) for technical details

## Configuration

Example `~/.config/mnb/config.yml`:

```yaml
nextcloud:
  url: https://share.educloud.no
  username: your-username
  # Password stored in macOS Keychain

backup:
  interval: hourly
  retain:
    hourly: 24  # Keep last 24 hourly backups
    daily: 7    # Keep 7 daily backups
    weekly: 4   # Keep 4 weekly backups
    monthly: 3  # Keep 3 monthly backups

exclude_patterns:
  - "**/.git/"
  - "**/node_modules/"
  - "**/venv/"
  - "**/__pycache__/"
  - "~/Downloads/"
  - "~/Library/Mobile Documents/"  # iCloud Drive
  - "~/Pictures/Photos Library.photoslibrary/"  # Photos
  - "**/*.log"
  - "**/target/"
  - "**/dist/"
  - "**/build/"

include_paths:
  - "~/Documents/"
  - "~/Desktop/"
  - "~/.ssh/"
  - "~/.config/"
  - "~/.zshrc"
  - "~/.gitconfig"
  - "/Library/Preferences/"
```

## Usage

### Basic Commands

```bash
# Initialize configuration
mnb init

# Run manual backup
mnb backup

# Check backup status
mnb status

# List snapshots
mnb list

# Restore from backup (automatically decrypts if encrypted)
mnb restore --snapshot-id 39 --path ~/Documents/secret.txt --destination /tmp/restored.txt

# Estimate storage usage
mnb estimate

# Clean old snapshots
mnb clean --keep-last 10

# Set up automatic backups
mnb schedule --interval hourly

# Check scheduler status
mnb schedule --status

# Disable automatic backups
mnb schedule --disable

# Launch GUI (menu bar app)
mnb-gui
```

See [SCHEDULING.md](SCHEDULING.md) for detailed scheduling documentation.
See [GUI.md](GUI.md) for GUI features and usage.

## Development Status & Roadmap

### Phase 1: Core Functionality ✅ COMPLETE
- [x] Project setup
- [x] WebDAV client implementation (optimized with connection pooling, parallel uploads)
- [x] File scanning and change detection
- [x] Incremental backup engine
- [x] Basic CLI interface

### Phase 2: Scheduling & Automation ✅ COMPLETE
- [x] launchd integration
- [x] Automatic backup scheduling (hourly/daily/weekly)
- [x] Notification system (webhook support for Google Chat, Zabbix)
- [x] Error handling and retry logic

### Phase 3: GUI Application ✅ COMPLETE
- [x] macOS menu bar app (rumps-based)
- [x] Backup status display
- [x] Manual backup trigger
- [x] Settings interface
- [x] Schedule management

### Phase 4: Security & Advanced Features ✅ COMPLETE

**Encryption Implementation:**
- [x] **Client-side encryption (AES-256-GCM)** ✅ COMPLETE
  - Files encrypted before upload with authenticated encryption
  - PBKDF2-HMAC-SHA256 key derivation (600,000 iterations)
  - macOS Keychain integration for secure key storage
  - Authentication tags detect tampering and corruption
  - Automatic decryption during restore
- [x] **CLI encryption management**
  - `mnb crypto enable` - Set up encryption with passphrase
  - `mnb crypto status` - View encryption configuration
  - `mnb crypto disable` - Disable encryption
  - `mnb crypto change-passphrase` - Update passphrase

**Other Features:**
- [x] Bandwidth throttling
- [x] Parallel uploads (configurable workers)
- [x] Snapshot deletion (unencrypted cleanup, migration support)
- [ ] Backup verification (verify uploaded file integrity)
- [ ] Multiple Nextcloud instance support
- [ ] Web dashboard

**Project Status: ✅ Production Ready**

## Performance

### Optimized WebDAV Implementation

Our WebDAV client is highly optimized for speed and reliability:

- **Connection Pooling**: Reuses HTTP connections (10 pools, 20 max connections)
- **Parallel Uploads**: Concurrent file uploads (configurable, default: 3 workers)
- **Directory Caching**: Eliminates redundant directory existence checks
- **Automatic Retries**: 3 retries with exponential backoff for transient failures
- **Batch Operations**: Pre-creates all directories before uploading

### Performance Benchmarks

Tested with 2,136 files (5.43 GB) to share.educloud.no:

| Method | Time | Speedup |
|--------|------|---------|
| Original WebDAV | ~30-60 min | 1x (baseline) |
| **Optimized WebDAV** | **~10-20 min** | **2-5x faster** |

### Alternative APIs Investigated

We investigated TSD File API as a potential alternative:
- ✅ Faster upload speeds
- ✅ Resumable uploads
- ❌ **Files NOT in Nextcloud storage** (separate TSD storage)
- ❌ Not accessible via share.educloud.no
- **Conclusion**: Not suitable for Nextcloud backups

See [TSD_API_TEST_RESULTS.md](TSD_API_TEST_RESULTS.md) for detailed findings.

## Technical Details

### Technologies
- **Language**: Python 3.9+
- **Encryption**: AES-256-GCM (cryptography library), PBKDF2-HMAC-SHA256
- **WebDAV Protocol**: Optimized requests with connection pooling
- **CLI**: Click framework
- **GUI**: Rumps (macOS menu bar app)
- **Scheduling**: launchd
- **Config**: YAML
- **Storage**: SQLite for metadata
- **Credentials**: macOS Keychain (passwords and encryption keys)

### Design Principles
- **Incremental**: Only backup what changed
- **Efficient**: Minimize network usage and storage (2-5x faster than naive WebDAV)
- **Resilient**: Handle network failures gracefully with automatic retries
- **Transparent**: Clear logging and status reporting
- **Secure**: AES-256-GCM encryption, credentials in Keychain, zero-knowledge backups
- **Well-Tested**: Functional core tested with real Nextcloud instances (Educloud)

## Contributing

Contributions welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- Inspired by Time Machine and rsync.net
- Built for the Nextcloud community
