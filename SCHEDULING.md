# Automatic Backup Scheduling

This guide explains how to set up automatic backups using macOS launchd.

## ⚠️ CRITICAL SECURITY WARNING

**DO NOT enable automatic backups until you understand the security implications:**

- ❌ **Files uploaded UNENCRYPTED** - Client-side encryption not yet implemented
- ⚠️ **Hourly SSH key uploads** - Your private keys uploaded repeatedly without protection
- ⚠️ **Credentials exposed** - Config files, tokens, passwords readable by Nextcloud admins

**Before enabling scheduled backups:**

1. **Review your include/exclude paths** - Make sure sensitive directories are excluded
2. **Consider the risk** - Automatic backups mean automatic exposure of sensitive data
3. **Wait for encryption** - Best practice is to wait for Phase 4 encryption implementation

**Recommended: Exclude sensitive data from automatic backups**
```yaml
exclude_patterns:
  - ~/.ssh/              # SSH private keys
  - ~/.aws/              # AWS credentials
  - ~/.config/gh/        # GitHub tokens
  - ~/.gnupg/            # GPG keys
```

**Only enable automatic scheduling if:**
- You exclude all sensitive directories, OR
- You accept the risk of unencrypted backups, OR
- You're using for testing only with non-sensitive data

---

## Quick Start

### Enable Automatic Backups

```bash
# Hourly backups (recommended)
mnb schedule --interval hourly

# Daily backups
mnb schedule --interval daily

# Weekly backups
mnb schedule --interval weekly
```

### Check Status

```bash
mnb schedule --status
```

### Disable Automatic Backups

```bash
mnb schedule --disable
```

## How It Works

The scheduler uses **launchd** (macOS's built-in task scheduler) to run backups automatically in the background.

### What Happens:

1. **Installation**: Creates a launchd plist file at:
   ```
   ~/Library/LaunchAgents/com.macos-nextcloud-backup.mnb.plist
   ```

2. **Execution**: Runs `mnb backup` at the specified interval

3. **Logging**: Saves output to:
   - Success: `~/Library/Logs/mnb-backup.log`
   - Errors: `~/Library/Logs/mnb-backup-error.log`

4. **Background**: Runs with low priority (nice 10) so it doesn't slow down your Mac

## Intervals

| Interval | Frequency | Best For |
|----------|-----------|----------|
| `hourly` | Every hour | Active development, frequent changes |
| `daily` | Every 24 hours | General use, daily document edits |
| `weekly` | Every 7 days | Minimal changes, archival |

## Monitoring

### Check Scheduler Status

```bash
mnb schedule --status
```

Output:
```
✓ Automatic backups: ENABLED
Running: Yes
Plist: /Users/you/Library/LaunchAgents/com.macos-nextcloud-backup.mnb.plist

Logs:
  Output: ~/Library/Logs/mnb-backup.log
  Errors: ~/Library/Logs/mnb-backup-error.log
```

### View Logs

```bash
# Watch logs in real-time
tail -f ~/Library/Logs/mnb-backup.log

# View recent backups
tail -50 ~/Library/Logs/mnb-backup.log

# Check for errors
cat ~/Library/Logs/mnb-backup-error.log
```

### Check launchd Status

```bash
# See if agent is loaded
launchctl list | grep mnb

# View detailed info
launchctl list com.macos-nextcloud-backup.mnb
```

## Troubleshooting

### Backups Not Running

1. **Check if scheduler is installed:**
   ```bash
   mnb schedule --status
   ```

2. **Check if agent is loaded:**
   ```bash
   launchctl list | grep mnb
   ```

3. **Manually load agent:**
   ```bash
   launchctl load ~/Library/LaunchAgents/com.macos-nextcloud-backup.mnb.plist
   ```

4. **Check logs for errors:**
   ```bash
   cat ~/Library/Logs/mnb-backup-error.log
   ```

### Backups Failing

1. **Test manual backup:**
   ```bash
   mnb backup
   ```

2. **Check credentials:**
   - App password might have expired
   - Re-run: `mnb init`

3. **Check network:**
   - Must be online for backups
   - VPN might interfere

### Too Many Backups / Storage Full

1. **Clean old backups:**
   ```bash
   mnb clean --keep-last 20
   ```

2. **Change interval:**
   ```bash
   mnb schedule --disable
   mnb schedule --interval daily  # Instead of hourly
   ```

3. **Adjust retention policy:**
   Edit `~/.config/mnb/config.yml`:
   ```yaml
   backup:
     retain:
       hourly: 6   # Keep fewer hourly backups
       daily: 3
       weekly: 2
   ```

## When Backups Run

### Hourly Backups
- First run: Immediately after enabling (or at next hour mark)
- Subsequent runs: Every 3600 seconds (1 hour)
- Not tied to specific times (e.g., not at :00 each hour)

### Important Notes

- **Laptop must be awake** for backups to run
- **Network required** to upload to Nextcloud
- **First backup** takes longer (all files)
- **Incremental backups** are fast (only changed files)

## Best Practices

### For Active Development

```bash
# Hourly backups with short retention
mnb schedule --interval hourly

# Clean weekly to save space
# Add to calendar: mnb clean --keep-last 30
```

### For General Use

```bash
# Daily backups
mnb schedule --interval daily

# Keep 2 weeks of history
# Config: retain.daily = 14
```

### For Minimal Changes

```bash
# Weekly backups
mnb schedule --interval weekly

# Keep longer history
# Config: retain.weekly = 12 (3 months)
```

## Advanced Configuration

### Custom Intervals

If you need different intervals, edit the plist directly:

```bash
# Edit plist
nano ~/Library/LaunchAgents/com.macos-nextcloud-backup.mnb.plist

# Change StartInterval (in seconds):
# 1800 = 30 minutes
# 7200 = 2 hours
# 43200 = 12 hours

# Reload
launchctl unload ~/Library/LaunchAgents/com.macos-nextcloud-backup.mnb.plist
launchctl load ~/Library/LaunchAgents/com.macos-nextcloud-backup.mnb.plist
```

### Run at Specific Times

Instead of intervals, run at specific times:

```bash
# Edit plist, replace StartInterval with:
<key>StartCalendarInterval</key>
<dict>
    <key>Hour</key>
    <integer>2</integer>  <!-- 2 AM -->
    <key>Minute</key>
    <integer>0</integer>
</dict>
```

## Uninstalling

To completely remove automatic backups:

```bash
# Disable scheduling
mnb schedule --disable

# Verify removed
mnb schedule --status

# Remove logs (optional)
rm ~/Library/Logs/mnb-backup*.log
```

## FAQ

**Q: Is it safe to enable automatic backups?**
A: ⚠️ **Not yet** - Files are uploaded unencrypted. Wait for encryption implementation (Phase 4) or exclude sensitive directories. See security warning at top of this document.

**Q: Will backups run when my laptop is closed?**
A: No, launchd jobs pause when the laptop sleeps. Backups will resume when you open it.

**Q: Can I have different intervals on different MacBooks?**
A: Yes! Each Mac has its own scheduler configuration.

**Q: How much battery does this use?**
A: Minimal. The scheduler itself uses negligible battery. The backup process uses battery proportional to how much data needs uploading.

**Q: Can I run manual backups while scheduling is enabled?**
A: Yes! Manual backups (`mnb backup`) work independently of scheduled backups.

**Q: What happens if a backup is still running when the next one starts?**
A: The new backup will wait or fail gracefully. Usually not an issue since incremental backups are fast.

**Q: Should I use hourly backups?**
A: Only if you exclude sensitive data. Hourly backups mean hourly uploads of any changed files - including credentials if they're not excluded.

## Summary

```bash
# Setup (one time)
mnb schedule --interval hourly

# Monitor
mnb schedule --status
tail -f ~/Library/Logs/mnb-backup.log

# Maintain
mnb clean --keep-last 30  # Run weekly

# Disable
mnb schedule --disable
```

Your backups now run automatically! 🎉
