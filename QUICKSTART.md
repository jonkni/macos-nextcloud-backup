# Quick Start Guide

## 🔐 Security Features

**Production Ready - Client-Side Encryption Enabled**

This backup tool provides enterprise-grade security for your backups:

- ✅ **AES-256-GCM encryption** - Files encrypted before upload
- ✅ **Zero-knowledge backups** - Nextcloud administrators cannot access your files
- ✅ **Authenticated encryption** - Tampering detection built-in
- ✅ **Secure key storage** - Encryption keys stored in macOS Keychain

**Your sensitive data is protected:**
- SSH keys, credentials, and configuration files are encrypted before upload
- Authentication tags detect any file tampering or corruption
- Encryption keys never leave your Mac

**Setup encryption in 1 minute:**
```bash
mnb crypto enable
# Enter a strong passphrase when prompted
# Passphrase stored securely in macOS Keychain
```

---

## Installation

### Install from source

```bash
cd ~/repos/macos-nextcloud-backup
pip3 install -e .
```

This will install the `mnb` command-line tool.

## First-Time Setup

### 0. Create App Password (Required for 2FA)

**IMPORTANT**: If your Nextcloud has Two-Factor Authentication enabled (like share.educloud.no), you need an app password:

1. **Log in to Nextcloud** via web browser: https://share.educloud.no
2. Click your **profile icon** → **Personal Settings** (or **Settings**)
3. Go to **Security** section
4. Find **"Devices & sessions"** or **"App passwords"** section
5. Enter a name like **"MacBook Backup"**
6. Click **"Create new app password"** or **"Generate"**
7. **Copy the generated password** (format: `xxxxx-xxxxx-xxxxx-xxxxx-xxxxx`)
8. Keep this password ready for the next step

**Note**: This is NOT your regular Nextcloud password. You must use the app password for API/WebDAV access.

### 1. Initialize Configuration

Run the setup wizard:

```bash
mnb init
```

You'll be prompted for:
- Nextcloud URL: `https://share.educloud.no`
- Username: your Nextcloud username (e.g., `ec-jonkni`)
- Password: **USE THE APP PASSWORD** from step 0 above (stored securely in macOS Keychain)
- Machine name: a unique name for this MacBook (e.g., "MacBook-Air-Home")

The wizard will test the connection and create a configuration file at `~/.config/mnb/config.yml`.

### 2. Review Configuration

Check your settings:

```bash
mnb config show
```

Edit the config file if needed to adjust:
- Include/exclude paths
- Retention policy
- Upload settings

### 3. Estimate Backup Size

Before running your first backup, see how much space it will need:

```bash
mnb estimate
```

This will scan your filesystem and show:
- Total number of files
- Total size
- Storage recommendations

### 4. Enable Encryption (Strongly Recommended)

Set up client-side encryption to protect your sensitive data:

```bash
mnb crypto enable
```

You'll be prompted to create a passphrase:
- **Use a strong, unique passphrase** (12+ characters recommended)
- **Store it securely** (if lost, backups cannot be decrypted)
- Passphrase is stored in macOS Keychain for automatic encryption/decryption

Check encryption status:

```bash
mnb crypto status
```

### 5. Run First Backup

Run an initial (full) encrypted backup:

```bash
mnb backup --initial
```

Or test it first with a dry run (recommended):

```bash
mnb backup --initial --dry-run
```

The backup will:
- Scan all included paths
- Skip excluded patterns
- **Encrypt files** with AES-256-GCM (if encryption enabled)
- Upload encrypted files to Nextcloud with `.enc` extension
- Create a snapshot

**Note:** Files are encrypted **before** upload. Nextcloud administrators cannot access your data.

## Regular Use

### Run Incremental Backup

After the initial backup, subsequent backups are incremental:

```bash
mnb backup
```

This only uploads changed or new files.

### Check Status

View backup status and latest snapshot:

```bash
mnb status
```

### List Snapshots

See all backup snapshots:

```bash
mnb list
```

Or show more snapshots:

```bash
mnb list --limit 50
```

### Clean Old Backups

Remove old snapshots to save space:

```bash
mnb clean --keep-last 20
```

Or test first:

```bash
mnb clean --keep-last 20 --dry-run
```

### Delete Snapshots

Delete specific snapshots or all unencrypted snapshots:

```bash
# Delete all unencrypted snapshots (after enabling encryption)
mnb delete --unencrypted --dry-run  # Preview first
mnb delete --unencrypted            # Actually delete

# Delete specific snapshot by ID
mnb delete --snapshot-id 42

# Delete ALL snapshots (use with caution!)
mnb delete --all --dry-run  # Preview first
mnb delete --all -y         # Skip confirmation
```

**Use case:** After enabling encryption, you may want to delete old unencrypted snapshots to ensure all sensitive data is encrypted in Nextcloud.

## Customizing Your Backup

### Modify Include Paths

Edit `~/.config/mnb/config.yml` to change what gets backed up:

**Recommended paths to backup (encrypted):**
```yaml
include_paths:
  - ~/Documents/
  - ~/Desktop/
  - ~/Projects/
  - ~/.ssh/           # SSH keys (encrypted before upload)
  - ~/.config/        # Configuration files (encrypted)
  - ~/.aws/           # AWS credentials (encrypted)
  - ~/.gnupg/         # GPG keys (encrypted)
```

**Note:** With encryption enabled, all files are encrypted before upload, making it safe to backup sensitive directories like `~/.ssh/` and credentials.

### Add Exclusions

Add patterns to exclude specific files or directories:

```yaml
exclude_patterns:
  - "**/.git/"
  - "**/node_modules/"
  - "~/Downloads/"
  - "**/*.log"
```

### Adjust Retention Policy

Control how many backups to keep:

```yaml
backup:
  retain:
    hourly: 12   # Last 12 hours
    daily: 5     # Last 5 days
    weekly: 2    # Last 2 weeks
    monthly: 0   # No monthly backups
```

## Scheduling Automatic Backups

Enable automatic encrypted backups using launchd:

```bash
# Set up hourly backups
mnb schedule --interval hourly

# Or daily
mnb schedule --interval daily

# Check status
mnb schedule --status

# Disable
mnb schedule --disable
```

Logs are written to:
- `~/Library/Logs/mnb-backup.log`
- `~/Library/Logs/mnb-backup-error.log`

## Troubleshooting

### Connection Issues

If you can't connect to Nextcloud:

1. Check your URL is correct (should start with https://)
2. Verify username and password
3. Test manually: `mnb init` will test the connection

### Storage Issues

If you're running out of space on Nextcloud:

1. Check storage usage: `mnb status`
2. Clean old backups: `mnb clean --keep-last 10`
3. Add more exclusions to reduce backup size
4. Consider increasing Nextcloud storage quota

### Permission Errors

If you get permission errors:

1. Check that paths in `include_paths` are readable
2. Skip problem directories by adding them to `exclude_patterns`

## Advanced Usage

### Restore Files

Restore encrypted files (automatically decrypted):

```bash
# Restore specific file from a snapshot
mnb restore --snapshot-id 39 --path ~/Documents/secret.txt --destination /tmp/restored.txt

# Restore using latest snapshot
mnb restore --path ~/Documents/important.pdf --destination /tmp/important.pdf
```

**How it works:**
1. Downloads encrypted `.enc` file from Nextcloud
2. Decrypts using encryption key from macOS Keychain
3. Verifies authentication tag (detects tampering)
4. Writes decrypted file to destination

**Note:** Encryption passphrase must be available in Keychain for decryption to work.

### Multiple Machines

Each machine should have its own configuration with a unique `machine.name`.
All backups go to the same Nextcloud but in separate folders:

```
backup/
├── MacBook-Pro-Home/
├── MacBook-Air-Office/
└── MacBook-Pro-Work/
```

### Verbose Output

For debugging, use verbose mode:

```bash
mnb -v backup
mnb -vv backup  # Very verbose
```

## Configuration File Location

- Config: `~/.config/mnb/config.yml`
- Database: `~/.config/mnb/metadata.db`
- Logs: `~/Library/Logs/mnb.log`
- Password: macOS Keychain (service: macos-nextcloud-backup)

## Getting Help

```bash
mnb --help
mnb backup --help
mnb config --help
```
