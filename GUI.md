# macOS Menu Bar GUI

A native macOS menu bar application for managing your backups.

## Features

### 📊 Quick Status
- View last backup time and status
- See total snapshots
- Check file count and size
- All from the menu bar

### 🔄 Manual Backup
- Trigger backup with one click
- Get notifications when backup starts
- Monitor progress via logs

### 📋 View Snapshots
- List recent backup snapshots
- See timestamps, file counts, sizes
- Quick overview of backup history

### 🔧 Manage Schedule
- Enable/disable automatic backups
- Choose interval (hourly, daily, weekly)
- Toggle with one click

### 📝 View Logs
- Quick access to backup logs
- Opens in Console.app
- Monitor backup progress

### ⚙️ Preferences
- Edit configuration file
- Opens in default text editor
- Quick access to settings

## Installation

### Install Dependencies

```bash
pip3 install rumps
```

Or reinstall the package:

```bash
cd ~/repos/macos-nextcloud-backup
pip3 install -e .
```

### Launch GUI

**Option 1:** Using the entry point (requires reinstall):
```bash
# Reinstall package to get mnb-gui command
cd ~/repos/macos-nextcloud-backup
pip3 install -e .

# Then launch
mnb-gui
```

**Option 2:** Direct launch (works without reinstall):
```bash
cd ~/repos/macos-nextcloud-backup
python3 launch-gui.py
```

**Auto-start:** Add to macOS login items for automatic launch at login.

## Usage

### First Launch

1. **Initialize configuration first:**
   ```bash
   mnb init
   ```

2. **Launch GUI:**
   ```bash
   mnb-gui
   ```

3. **Look for "MNB" in menu bar** (top-right corner)

### Menu Items

```
MNB
├── Status                    # Show backup status
├── ─────────────────
├── Run Backup Now           # Manual backup
├── View Snapshots           # List recent backups
├── Restore Files...         # Restore from backup (coming soon)
├── ─────────────────
├── View Logs               # Open logs in Console
├── Preferences...          # Edit config file
├── ─────────────────
├── ✓ Schedule: Enabled     # Toggle auto-backups
└── Quit
```

### Status Dialog

Click "Status" to see:

```
Last Backup:
• Time: 2026-03-17 14:30 (2h ago)
• Type: incremental
• Files: 47,111
• Size: 5.43 GB
• Status: completed

Total Snapshots: 12
```

### Run Backup

1. Click "Run Backup Now"
2. Confirm dialog: "Start a backup now?"
3. Notification: "Backup Started"
4. Check logs for progress

### View Snapshots

Shows last 5 snapshots:

```
Recent Snapshots:

• 2026-03-17 14:30 - 47,111 files (5.4 GB)
• 2026-03-17 10:30 - 47,050 files (5.4 GB)
• 2026-03-16 14:30 - 46,980 files (5.3 GB)
• 2026-03-16 10:30 - 46,920 files (5.3 GB)
• 2026-03-15 14:30 - 46,850 files (5.3 GB)

Total: 12 snapshots
```

### Toggle Schedule

Click "Schedule: Disabled" to enable:
1. Dialog appears: "Enable Automatic Backups"
2. Choose interval: hourly, daily, weekly
3. Click "Enable"
4. Notification: "Schedule Enabled"

Click "Schedule: Enabled" to disable:
1. Confirm: "Stop running automatic backups?"
2. Click "Disable"
3. Notification: "Schedule Disabled"

## Auto-Start on Login

### Option 1: macOS Settings

1. Open **System Settings**
2. Go to **General** → **Login Items**
3. Click **+** button
4. Navigate to: `/opt/homebrew/bin/mnb-gui`
5. Add it to login items

### Option 2: Launch Agent (Better)

Create auto-start plist:

```bash
cat > ~/Library/LaunchAgents/com.macos-nextcloud-backup.gui.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.macos-nextcloud-backup.gui</string>
    <key>ProgramArguments</key>
    <array>
        <string>/opt/homebrew/bin/mnb-gui</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
</dict>
</plist>
EOF

# Load it
launchctl load ~/Library/LaunchAgents/com.macos-nextcloud-backup.gui.plist
```

### Option 3: AppleScript App

Create Application in Script Editor:

```applescript
do shell script "/opt/homebrew/bin/mnb-gui"
```

Save as: `MNB Backup.app`

Add to Login Items.

## Design Philosophy: GUI for Monitoring, CLI for Power Features

The GUI is intentionally **focused on monitoring and quick actions**. Complex operations like browsing snapshots and restoring files are better served by the CLI, which offers:

- More powerful filtering and search
- Scriptable operations
- Better for handling large file lists
- Familiar interface for advanced users

### What Stays in GUI (Monitoring)
- ✅ Quick status checks
- ✅ Manual backup trigger
- ✅ Schedule management
- ✅ Log access
- ✅ Configuration access

### What Stays in CLI (Power Features)
- `mnb list` - Browse all snapshots with filtering
- `mnb restore` - Restore files with full control
- `mnb clean` - Advanced cleanup with retention policies
- `mnb config` - Detailed configuration management

This separation keeps the GUI lightweight and focused while maintaining full functionality through the CLI.

## Features Under Consideration

These enhancements would improve the monitoring experience without adding complexity:

### ⚠️ Visual Status Indicators
- Red icon when backup fails
- Yellow icon when backup is old (>24h)
- Green when everything is healthy
- Notifications for critical issues

### 🎨 Custom Menu Bar Icon
- Visual backup status at a glance
- Progress indicator during active backup
- Different states (idle, backing up, error, warning)

### 📊 Quick Stats in Menu
- Show last backup time directly in menu
- File count and size summary
- No dialog needed for quick check

## Troubleshooting

### "No backup configuration found"

Initialize first:
```bash
mnb init
```

### GUI won't launch

Check if dependencies installed:
```bash
pip3 list | grep rumps
```

Install if missing:
```bash
pip3 install rumps
```

### "Permission denied"

Make sure mnb-gui is executable:
```bash
chmod +x $(which mnb-gui)
```

### Menu bar icon missing

rumps uses system icons by default. Custom icon coming soon.

### Can't find MNB in menu bar

Look in top-right corner of screen, near clock/wifi icons.

If too many menu bar items, might be hidden. Remove some other items.

## Keyboard Shortcuts

Currently no keyboard shortcuts.

Coming soon:
- `⌘R` - Run backup
- `⌘S` - Show status
- `⌘L` - View logs
- `⌘,` - Preferences

## Technical Details

### Built With
- **rumps**: Python library for macOS menu bar apps
- **pyobjc**: Python-Objective-C bridge
- **subprocess**: Launch mnb commands

### How It Works

1. **Status Updates**: Reads from metadata.db
2. **Commands**: Launches `mnb` CLI in background
3. **Notifications**: Uses macOS notification center
4. **Logs**: Opens Console.app with log file

### Process Model

- GUI runs as separate process
- Launches `mnb` commands via subprocess
- Commands run independently
- GUI polls for status updates

### Memory Usage

Very lightweight:
- ~20-30 MB RAM
- Minimal CPU (only when active)
- No background polling (event-driven)

## Comparison

### CLI vs GUI

| Feature | CLI (`mnb`) | GUI (`mnb-gui`) |
|---------|-------------|-----------------|
| **Run backup** | `mnb backup` | Click menu item |
| **Check status** | `mnb status` | Click "Status" |
| **View logs** | `tail -f ~/Library/Logs/...` | Click "View Logs" |
| **Enable schedule** | `mnb schedule --interval hourly` | Click toggle |
| **Visibility** | Terminal only | Always in menu bar |
| **Automation** | Easy to script | Not scriptable |
| **Power users** | ✅ Preferred | ⚠️ Optional |
| **Casual users** | ⚠️ Intimidating | ✅ Easy |

### Best of Both Worlds

Use both! They're designed to complement each other:

**GUI (Menu Bar) - For Daily Monitoring:**
- Quick status checks without opening terminal
- One-click manual backups
- Toggle automatic backups on/off
- Visual presence reminding you backups are running

**CLI (Terminal) - For Power Operations:**
- Browse and search through all snapshots
- Restore specific files or directories
- Advanced configuration and cleanup
- Automation and scripting
- Detailed control over backup process

They share the same configuration and database, so you can freely switch between them based on what you're doing.

## FAQ

**Q: Do I need to keep terminal open?**
A: No! GUI runs independently.

**Q: Can I use both CLI and GUI?**
A: Yes! They share the same configuration.

**Q: Will GUI slow down my Mac?**
A: No. It's very lightweight (20-30 MB RAM).

**Q: Can GUI run backups faster?**
A: No. Same speed as CLI (it calls CLI internally).

**Q: Can I customize the menu?**
A: Not yet. Custom menus coming in future version.

**Q: Does it work on macOS Ventura/Sonoma?**
A: Yes! Works on macOS 11+ (Big Sur and later).

## Screenshots

(Coming soon - need to create custom icons and take screenshots)

## Contributing

Want to improve the GUI? Some ideas:

- [ ] Custom menu bar icon
- [ ] Progress indicator during backup
- [ ] File browser for restore
- [ ] Backup history graph
- [ ] Preferences window (instead of text editor)
- [ ] Keyboard shortcuts
- [ ] Drag-and-drop restore

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

---

**Enjoy your visual backup manager!** 🎉
