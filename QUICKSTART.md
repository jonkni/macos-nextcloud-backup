# Quick Start Guide

## ⚠️ SECURITY WARNING - Read Before Setup

**Current Status: Testing/Development Only - Not Production Ready**

This backup tool does **NOT yet have client-side encryption**. Files are uploaded to Nextcloud **unencrypted**:

- ❌ **SSH keys uploaded unencrypted** - Your private keys readable by Nextcloud admins
- ❌ **Credentials exposed** - Config files with tokens, passwords, API keys unprotected
- ❌ **Sensitive data at risk** - Any confidential files accessible to server administrators

**BEFORE running backups:**

1. **For Testing:** Exclude sensitive directories (see below)
2. **For Production:** Wait for encryption implementation (Phase 4)
3. **Risk Accepted:** Understand Nextcloud admins can read your files

**Recommended exclusions for testing:**
```yaml
exclude_patterns:
  - ~/.ssh/              # SSH keys
  - ~/.aws/              # AWS credentials
  - ~/.config/gh/        # GitHub CLI tokens
  - ~/.gnupg/            # GPG keys
  - ~/Documents/sensitive/  # Your sensitive documents
```

Only proceed if you understand the security implications.

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

### 4. Run First Backup

⚠️ **Remember:** Files uploaded **unencrypted**. Only use for testing with non-sensitive data.

Run an initial (full) backup:

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
- Upload files to Nextcloud **without encryption**
- Create a snapshot

**Before running:** Review your include/exclude paths to ensure no sensitive data is backed up.

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

## Customizing Your Backup

### Modify Include Paths

Edit `~/.config/mnb/config.yml` to change what gets backed up:

⚠️ **Security Note:** Until encryption is implemented, avoid backing up:
- `~/.ssh/` - SSH private keys
- `~/.config/` - May contain tokens/credentials
- `~/.aws/`, `~/.gnupg/` - Credentials and keys

**Safe for testing (non-sensitive data):**
```yaml
include_paths:
  - ~/Documents/
  - ~/Desktop/
  - ~/Projects/
  # COMMENTED OUT until encryption available:
  # - ~/.ssh/        # ⚠️ Contains private keys
  # - ~/.config/     # ⚠️ May contain credentials
```

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

⚠️ **Only schedule if you accept the security risk** (unencrypted uploads)

Enable automatic backups using launchd:

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

(Coming soon)

```bash
mnb restore --snapshot <timestamp> --path ~/Documents/file.txt
```

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
