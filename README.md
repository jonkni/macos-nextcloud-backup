# macOS Nextcloud Backup

Time Machine-like incremental backup solution for macOS to Nextcloud.

## Overview

This tool provides automated, incremental backups of your macOS system to a Nextcloud instance via WebDAV. It's designed for users who want:
- Time Machine-style backup functionality
- Remote storage on Nextcloud instead of local drives
- Selective backup with smart exclusions
- Minimal storage footprint with deduplication

## Features

### Core Functionality
- **Incremental Backups**: Only changed files are uploaded, similar to Time Machine
- **Deduplication**: Hard-linking for unchanged files to save space
- **Smart Exclusions**: Automatically exclude:
  - iCloud-synced folders (Photos, Desktop, Documents if synced)
  - Downloads folder
  - Git repositories (.git directories)
  - Build artifacts (node_modules, target, dist, etc.)
  - System cache and temporary files
  - Large media files already backed up elsewhere
- **Scheduled Backups**: Hourly automated backups via launchd
- **Multiple Machine Support**: Manage backups for all your MacBooks

### Interface
- **CLI Tool**: Command-line interface for scripting and automation
- **GUI Application** (planned): macOS menu bar app for monitoring and control
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

# Run first backup
mnb backup --initial

# Enable automatic backups (coming soon)
mnb schedule --interval hourly
```

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

# Restore from backup
mnb restore --snapshot 2026-03-17T10:00:00 --path ~/Documents

# Estimate storage usage
mnb estimate

# Clean old snapshots
mnb clean --keep-last 10
```

## Development Roadmap

### Phase 1: Core Functionality (Week 1-2)
- [x] Project setup
- [ ] WebDAV client implementation
- [ ] File scanning and change detection
- [ ] Incremental backup engine
- [ ] Basic CLI interface

### Phase 2: Scheduling & Automation (Week 3)
- [ ] launchd integration
- [ ] Automatic backup scheduling
- [ ] Notification system
- [ ] Error handling and retry logic

### Phase 3: GUI Application (Week 4-5)
- [ ] macOS menu bar app
- [ ] Backup status display
- [ ] Manual backup trigger
- [ ] Settings interface

### Phase 4: Advanced Features (Week 6+)
- [ ] Backup encryption
- [ ] Bandwidth throttling
- [ ] Backup verification
- [ ] Multiple Nextcloud instance support
- [ ] Web dashboard

## Technical Details

### Technologies
- **Language**: Python 3.9+
- **WebDAV**: webdavclient3 or requests
- **CLI**: Click framework
- **GUI**: PyObjC or Rumps (macOS menu bar)
- **Scheduling**: launchd
- **Config**: YAML
- **Storage**: SQLite for metadata

### Design Principles
- **Incremental**: Only backup what changed
- **Efficient**: Minimize network usage and storage
- **Resilient**: Handle network failures gracefully
- **Transparent**: Clear logging and status reporting
- **Secure**: Credentials in Keychain, optional encryption

## Contributing

Contributions welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- Inspired by Time Machine and rsync.net
- Built for the Nextcloud community
