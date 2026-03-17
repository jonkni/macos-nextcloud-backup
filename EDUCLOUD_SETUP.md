# Setup Guide for share.educloud.no

This guide is specifically for users of **share.educloud.no** (University of Oslo Nextcloud).

## Important: 2FA is Enabled

The educloud.no Nextcloud instance has **Two-Factor Authentication (2FA)** enabled. This means you **cannot** use your regular UiO password for API/WebDAV access. You must create an **app password**.

## Step-by-Step Setup

### Step 1: Create App Password

1. **Open web browser** and go to: https://share.educloud.no

2. **Log in** with your UiO credentials (username + 2FA)

3. **Click your profile icon** in the top-right corner

4. Select **"Settings"** or **"Personal settings"**

5. In the left sidebar, click **"Security"**

6. Scroll down to **"Devices & sessions"** section

7. Under **"Create new app password"** or **"App name"**:
   - Enter a name: `MacBook Backup` (or similar)
   - Click the **"Create new app password"** button

8. **Copy the generated password**
   - It will look like: `Abcde-Fghij-Klmno-Pqrst-Uvwxy`
   - This is a one-time display - save it somewhere temporarily
   - You can always create a new one if you lose it

### Step 2: Install the Tool

Open Terminal and run:

```bash
# Clone the repository
cd ~/repos
git clone https://github.com/YOUR_USERNAME/macos-nextcloud-backup.git
cd macos-nextcloud-backup

# Install
pip3 install -e .
```

### Step 3: Initialize Configuration

Run the initialization wizard:

```bash
mnb init
```

When prompted, enter:

- **Nextcloud URL**: `https://share.educloud.no`
- **Username**: Your UiO username (e.g., `ec-jonkni`)
- **Password**: **USE THE APP PASSWORD** you created in Step 1
  - NOT your regular UiO password
  - Paste the app password (format: `xxxxx-xxxxx-xxxxx-xxxxx-xxxxx`)
- **Machine name**: Something unique for this Mac (e.g., `MacBook-Air-Home`)

The tool will test the connection and save your configuration.

### Step 4: Estimate Storage

Before backing up, check how much space you need:

```bash
mnb estimate
```

This will scan your files and show the estimated backup size.

### Step 5: Run First Backup

Test with a dry run first:

```bash
mnb backup --initial --dry-run
```

If everything looks good, run the real backup:

```bash
mnb backup --initial
```

This will upload all your files to Nextcloud. Depending on size, it may take several hours.

## Understanding Your 100 GB Quota

Your Nextcloud storage: **100 GB**

Estimated usage for 1 MacBook (with default exclusions):
- **Initial backup**: 15-30 GB
- **After 2 weeks**: 20-35 GB (with incremental backups)
- **After 1 month**: 25-40 GB

For **3 MacBooks**:
- **Initial**: 45-90 GB
- **After 2 weeks**: 60-105 GB ⚠️ (may exceed quota)

### Recommendations:

1. **Start with 1 MacBook** to see actual storage usage
2. **Monitor with** `mnb status` regularly
3. **Clean old backups** if needed: `mnb clean --keep-last 15`
4. **Adjust exclusions** in `~/.config/mnb/config.yml` to reduce size

## Troubleshooting

### "Could not connect to Nextcloud"

**Cause**: Usually means you're using your regular UiO password instead of app password

**Solution**:
1. Go back to Step 1 and create a new app password
2. Run `mnb init` again with the app password

### "Permission denied" errors

**Cause**: Some files can't be read (system files, etc.)

**Solution**: These are automatically skipped - normal behavior

### Running out of storage

**Solution 1**: Clean old backups
```bash
mnb clean --keep-last 10
```

**Solution 2**: Add more exclusions to `~/.config/mnb/config.yml`:
```yaml
exclude_patterns:
  - "~/Movies/"
  - "~/Music/"
  - "**/*.mp4"
  - "**/*.mov"
```

## Daily Usage

### Check backup status
```bash
mnb status
```

### Run incremental backup
```bash
mnb backup
```

### List all snapshots
```bash
mnb list
```

## Multiple MacBooks

To backup multiple MacBooks to the same Nextcloud:

1. **On each MacBook**, run through Steps 2-5
2. **Use a different machine name** for each (e.g., "MacBook-Pro-Work", "MacBook-Air-Home")
3. Each machine will have its own folder in Nextcloud

Your Nextcloud structure will look like:
```
backup/
├── MacBook-Pro-Work/
│   └── snapshots/
├── MacBook-Air-Home/
│   └── snapshots/
└── MacBook-Pro-Personal/
    └── snapshots/
```

## Need Help?

- Read the full documentation: `README.md`
- Quick start guide: `QUICKSTART.md`
- Report issues: https://github.com/YOUR_USERNAME/macos-nextcloud-backup/issues
