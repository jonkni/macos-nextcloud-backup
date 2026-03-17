# Quick Start Guide

## Installation

### Install from source

```bash
cd ~/repos/macos-nextcloud-backup
pip3 install -e .
```

This will install the `mnb` command-line tool.

## First-Time Setup

### 1. Initialize Configuration

Run the setup wizard:

```bash
mnb init
```

You'll be prompted for:
- Nextcloud URL: `https://share.educloud.no`
- Username: your Nextcloud username
- Password: your Nextcloud password (stored securely in macOS Keychain)
- Machine name: a unique name for this MacBook (e.g., "MacBook-Pro-Home")

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

Run an initial (full) backup:

```bash
mnb backup --initial
```

Or test it first with a dry run:

```bash
mnb backup --initial --dry-run
```

The backup will:
- Scan all included paths
- Skip excluded patterns
- Upload files to Nextcloud
- Create a snapshot

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

```yaml
include_paths:
  - ~/Documents/
  - ~/Desktop/
  - ~/Projects/
  - ~/.ssh/
  - ~/.config/
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

(Coming soon - will use launchd for hourly/daily backups)

```bash
mnb schedule --interval hourly
```

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
