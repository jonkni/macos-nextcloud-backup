# Scheduled Backup FAQ

## ⚠️ Security Warning

**Before enabling scheduled backups, read this:**

Automatic backups mean automatic exposure of sensitive data. Files are uploaded **unencrypted** (client-side encryption not yet implemented). Scheduling hourly backups of directories containing SSH keys, credentials, or tokens creates **hourly uploads of sensitive data** without protection.

**See [SCHEDULING.md](SCHEDULING.md) for full security warning and recommended exclusions.**

---

## Common Questions About Automatic Backups

### 1. What if a backup takes longer than the interval?

**Answer:** The backup is protected by a **lock file** mechanism.

**How it works:**
- When a backup starts, it creates a lock file (`~/.config/mnb/backup.lock`)
- If another backup tries to start while one is running, it will:
  1. Check the lock file
  2. See that a backup is already in progress
  3. Exit gracefully with a message
  4. Not start a duplicate backup

**Example:**
```
# Hourly backups scheduled
# Backup starts at 10:00 and takes 2 hours
10:00 - Backup starts, lock acquired
11:00 - Scheduled backup checks lock, finds it locked, exits
12:00 - Original backup finishes, lock released
12:01 - Scheduled backup starts successfully
```

**Log output when duplicate prevented:**
```
⚠ Another backup is already running
PID: 12345
Command: /opt/homebrew/bin/mnb backup

Wait for it to complete, or use --force to override
```

**Force a backup anyway:**
```bash
mnb backup --force  # Ignores lock (use with caution)
```

### 2. What happens when the laptop is closed or turned off?

**Answer:** Backups **catch up** when the laptop wakes or boots.

**How it works:**
- The launchd plist has `RunAtLoad` set to `true`
- When your laptop wakes from sleep or boots:
  1. launchd loads the backup agent
  2. The agent immediately runs one backup (catch-up)
  3. Then continues on normal schedule

**Example:**
```
# Hourly backups scheduled

10:00 - Backup runs
11:00 - Backup runs
12:00 - You close laptop (sleep)
13:00 - (Laptop asleep, backup skipped)
14:00 - (Laptop asleep, backup skipped)
15:00 - (Laptop asleep, backup skipped)
15:30 - You open laptop (wake)
15:31 - Backup runs immediately (catch-up)
16:00 - Backup runs (back on schedule)
17:00 - Backup runs
```

**Important notes:**
- Only ONE catch-up backup runs on wake
- Missed backups are NOT queued up
- This prevents flooding the system with backups after long sleep

**If laptop is off for days:**
- You don't get 72 backups queued up
- You get 1 backup when you turn it on
- Then normal schedule resumes

### 3. What if network is unavailable?

**Answer:** Backup **checks network** before running and exits gracefully if offline.

**How it works:**
1. **Network connectivity check:**
   - Tries to connect to DNS (8.8.8.8:53)
   - Timeout: 5 seconds
   - If fails: Exit with message

2. **Nextcloud reachability check:**
   - Tries to connect to your Nextcloud URL
   - Timeout: 5 seconds
   - If fails: Exit with message

3. **If offline:**
   - No backup attempted
   - No errors logged
   - Next scheduled backup will try again

**Example - No network:**
```bash
$ mnb backup
Starting incremental backup...

Checking network connectivity...
✗ No network connection

Cannot run backup without network access.
Connect to network and try again.
```

**Example - Network but not Nextcloud:**
```bash
$ mnb backup
Starting incremental backup...

Checking network connectivity...
✗ Cannot reach Nextcloud
URL: https://share.educloud.no

Possible causes:
  - VPN required but not connected
  - Nextcloud server is down
  - Firewall blocking access
```

**Log output (~/Library/Logs/mnb-backup-error.log):**
```
2026-03-17 14:30:00 - Network check failed: No network connection
2026-03-17 15:30:00 - Network check failed: Cannot reach https://share.educloud.no
2026-03-17 16:30:00 - Network check passed, backup starting...
```

**Benefits:**
- ✅ No wasted CPU/battery trying to backup when offline
- ✅ Clean error messages in logs
- ✅ Automatic retry on next schedule
- ✅ No partial backups or corruption

## Summary Table

| Scenario | What Happens | User Action Required |
|----------|--------------|---------------------|
| **Backup takes > interval** | Next scheduled backup sees lock, exits | None - automatic |
| **Laptop closed/sleep** | Backup paused, resumes on wake | None - automatic |
| **Laptop off for days** | One catch-up backup on boot | None - automatic |
| **No network** | Backup exits, retries next schedule | Connect to network |
| **VPN required** | Backup exits if VPN not connected | Connect to VPN |
| **Nextcloud down** | Backup exits, retries later | Wait for Nextcloud |

## Best Practices

### For Laptops That Sleep Often

```bash
# Use daily backups instead of hourly
mnb schedule --disable
mnb schedule --interval daily

# Backup runs once per day when awake
```

### For Laptops Always On

```bash
# Hourly backups work great
mnb schedule --interval hourly

# Minimal missed backups
```

### For Intermittent Network

```bash
# Don't worry! Backups will retry
# Check logs occasionally:
tail -20 ~/Library/Logs/mnb-backup-error.log

# Look for pattern of network failures
```

### Monitor Lock Issues

```bash
# If backups seem stuck, check for stale lock:
ls -la ~/.config/mnb/backup.lock

# If exists and no backup running:
rm ~/.config/mnb/backup.lock

# Or force a backup:
mnb backup --force
```

## Troubleshooting

### Backup seems stuck

**Check if backup is actually running:**
```bash
ps aux | grep "mnb backup"
```

**Check lock file:**
```bash
cat ~/.config/mnb/backup.lock  # Shows PID
ps -p <PID>  # Check if process exists
```

**Remove stale lock:**
```bash
# If process doesn't exist
rm ~/.config/mnb/backup.lock
```

### Backups not running after wake

**Check scheduler status:**
```bash
mnb schedule --status
launchctl list | grep mnb
```

**Reload scheduler:**
```bash
mnb schedule --disable
mnb schedule --interval hourly
```

### Too many network failures

**Test network check manually:**
```bash
python3 -c "from mnb.utils.network import check_nextcloud_connectivity; print(check_nextcloud_connectivity('https://share.educloud.no'))"
```

**Check VPN requirements:**
- Does Nextcloud require VPN?
- Is VPN auto-connecting on wake?

## Implementation Details

### Lock File Location
```
~/.config/mnb/backup.lock
```

Contents: PID of running backup process

### Network Check Details

**Check 1: General connectivity**
- Tests: Connection to 8.8.8.8:53 (Google DNS)
- Timeout: 5 seconds
- Purpose: Detect if network interface is up

**Check 2: Nextcloud reachability**
- Tests: Connection to Nextcloud URL:port
- Timeout: 5 seconds
- Purpose: Detect if Nextcloud is accessible

### RunAtLoad Behavior

From Apple's launchd documentation:
> If RunAtLoad is set to true, the job will be run once at load time,
> in addition to running at the regular interval.

This means:
- Backup runs immediately when agent loads
- Agent loads on: login, wake from sleep, manual load
- Then continues on normal StartInterval schedule

## Advanced: Customize Behavior

### Disable Network Check

Edit your backup script wrapper (not recommended):
```bash
# Skip network check
export MNB_SKIP_NETWORK_CHECK=1
mnb backup
```

### Different Network Check Timeout

Currently hardcoded to 5 seconds. To change, edit:
```
mnb/cli/main.py
Line ~195: timeout=5
```

### Disable RunAtLoad

If you don't want catch-up backups:
```bash
# Edit plist
nano ~/Library/LaunchAgents/com.macos-nextcloud-backup.mnb.plist

# Change:
<key>RunAtLoad</key>
<true/>

# To:
<key>RunAtLoad</key>
<false/>

# Reload
launchctl unload ~/Library/LaunchAgents/com.macos-nextcloud-backup.mnb.plist
launchctl load ~/Library/LaunchAgents/com.macos-nextcloud-backup.mnb.plist
```

---

**Questions?** See [SCHEDULING.md](SCHEDULING.md) for more scheduling details.
