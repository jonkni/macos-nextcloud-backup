# Implementation Plan

## Storage Analysis

### Capacity Estimation for 3 MacBooks

Based on selective backup (Documents, Config, System Preferences):

#### Initial Backup (per machine)
- **Conservative scenario**: 15-20 GB per machine
  - Documents/Projects: 10 GB
  - Config files: 500 MB
  - App data: 5 GB
  - System prefs: 100 MB

- **Heavy user scenario**: 25-30 GB per machine
  - Documents/Projects: 20 GB
  - Config files: 1 GB
  - App data: 8 GB
  - System prefs: 200 MB

#### Incremental Growth (per machine/week)
- **Light usage**: 500 MB - 1 GB/week
- **Heavy usage**: 2-3 GB/week

#### 100 GB Nextcloud Analysis

**Tight fit scenario:**
- 3 machines x 20 GB = 60 GB initial
- 3 weeks of incrementals = 9-18 GB
- **Total: 69-78 GB** ✓ Fits!

**Heavy usage scenario:**
- 3 machines x 30 GB = 90 GB initial
- 1 week of incrementals = 6-9 GB
- **Total: 96-99 GB** ⚠️ Very tight!

**Recommendation**:
- **100 GB is workable** with:
  - Aggressive exclusions
  - Short retention (2-3 weeks)
  - Regular cleanup
- **200-300 GB is ideal** for:
  - 4-6 weeks retention
  - More relaxed exclusions
  - Better safety margin

## Architecture Design

### System Components

```
┌─────────────────────────────────────────────────┐
│                  User Interface                 │
├─────────────────┬───────────────────────────────┤
│   CLI Tool      │      GUI App (menu bar)       │
│   (Click)       │      (Rumps/PyObjC)           │
└────────┬────────┴──────────────┬────────────────┘
         │                       │
         └───────────┬───────────┘
                     │
         ┌───────────▼────────────┐
         │   Backup Controller    │
         │  - Orchestrates jobs   │
         │  - Manages state       │
         └───────────┬────────────┘
                     │
         ┌───────────▼────────────┐
         │   Backup Engine        │
         │  - File scanner        │
         │  - Change detector     │
         │  - Snapshot manager    │
         └───────────┬────────────┘
                     │
    ┌────────────────┼────────────────┐
    │                │                │
┌───▼────┐    ┌──────▼──────┐  ┌─────▼─────┐
│ WebDAV │    │   Storage   │  │ Metadata  │
│ Client │    │   Manager   │  │    DB     │
│        │    │             │  │ (SQLite)  │
└────────┘    └─────────────┘  └───────────┘
     │
┌────▼─────────────────┐
│  Nextcloud Instance  │
│  (WebDAV endpoint)   │
└──────────────────────┘
```

### Data Flow

1. **Scan Phase**: Walk filesystem, check against exclusion rules
2. **Detection Phase**: Compare with last snapshot metadata
3. **Upload Phase**: Upload changed/new files via WebDAV
4. **Snapshot Phase**: Create new snapshot with hard links to unchanged files
5. **Cleanup Phase**: Remove old snapshots based on retention policy

### Snapshot Strategy

Similar to Time Machine's approach:
- Keep all hourly backups for 24 hours
- Keep daily backups for 7 days
- Keep weekly backups for 1 month
- Keep monthly backups for 3 months

With 100 GB constraint, reduce to:
- Hourly: last 12 hours
- Daily: last 5 days
- Weekly: last 2 weeks

## Implementation Phases

### Phase 1: Core Backend (Priority: High)

**Week 1: Foundation**
- [x] Project structure setup
- [ ] WebDAV client wrapper
  - Test connection
  - Upload/download files
  - Directory operations
- [ ] Configuration system
  - YAML parsing
  - Keychain integration for passwords
  - Validation

**Week 2: Backup Engine**
- [ ] File scanner
  - Walk directory tree
  - Apply exclusion patterns
  - Calculate checksums (fast hash)
- [ ] Change detection
  - Compare mtime/size
  - Optional content hash
  - Metadata database
- [ ] Snapshot creation
  - Upload changed files
  - Create snapshot metadata
  - Hard link unchanged files (if Nextcloud supports, else reference)

### Phase 2: CLI Tool (Priority: High)

**Commands to implement:**
```
mnb init                    # Initial setup wizard
mnb config                  # Configure settings
mnb backup [--initial]      # Run backup
mnb status                  # Show backup status
mnb list                    # List snapshots
mnb restore                 # Restore files
mnb estimate                # Estimate storage
mnb clean                   # Clean old snapshots
mnb schedule                # Setup automatic backups
```

### Phase 3: Scheduling (Priority: High)

- [ ] launchd plist generation
- [ ] Auto-start on login
- [ ] Notification on completion/error
- [ ] Log rotation

### Phase 4: GUI Application (Priority: Medium)

- [ ] Menu bar icon
- [ ] Status display
- [ ] Manual backup trigger
- [ ] View recent snapshots
- [ ] Settings panel

### Phase 5: Advanced Features (Priority: Low)

- [ ] Backup encryption (AES-256)
- [ ] Bandwidth throttling
- [ ] Backup verification
- [ ] Multi-Nextcloud support
- [ ] Web dashboard

## Technical Decisions

### Language: Python
**Pros:**
- Fast development
- Great libraries (webdavclient3, click)
- Easy CLI and GUI
- Cross-platform potential

**Cons:**
- Slower than compiled languages
- Distribution requires Python

**Alternative**: Go (better performance, single binary)

### WebDAV Library: webdavclient3
- Well-maintained
- Good Nextcloud support
- Chunked uploads

### GUI: Rumps
- Simple menu bar apps
- Pure Python
- Good for status display

**Alternative**: Swift/SwiftUI (native, better performance)

### Metadata: SQLite
- Fast lookups
- Reliable
- No external dependencies
- Good for file metadata

### Scheduling: launchd
- Native macOS
- Better than cron
- Handles sleep/wake

## File Structure

```
macos-nextcloud-backup/
├── README.md
├── PLAN.md
├── LICENSE
├── setup.py
├── requirements.txt
├── .gitignore
├── mnb/                    # Main package
│   ├── __init__.py
│   ├── __main__.py         # Entry point
│   ├── cli/                # CLI interface
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── backup.py
│   │   ├── restore.py
│   │   └── config.py
│   ├── core/               # Core logic
│   │   ├── __init__.py
│   │   ├── backup_engine.py
│   │   ├── scanner.py
│   │   ├── detector.py
│   │   └── snapshot.py
│   ├── storage/            # Storage backends
│   │   ├── __init__.py
│   │   ├── webdav.py
│   │   └── metadata.py
│   ├── config/             # Configuration
│   │   ├── __init__.py
│   │   ├── manager.py
│   │   └── schema.py
│   └── utils/              # Utilities
│       ├── __init__.py
│       ├── exclude.py
│       ├── keychain.py
│       └── logging.py
├── tests/                  # Tests
│   ├── test_scanner.py
│   ├── test_webdav.py
│   └── test_backup.py
└── gui/                    # GUI app (future)
    └── menu_bar.py
```

## Next Steps

1. **Setup Python project structure**
   - Create package directories
   - Setup.py and requirements.txt
   - Basic CLI skeleton

2. **Implement WebDAV client**
   - Test connection to Nextcloud
   - Basic upload/download
   - Directory operations

3. **Create file scanner**
   - Walk filesystem
   - Apply exclusions
   - Generate file list

4. **Build backup engine**
   - Detect changes
   - Upload files
   - Create snapshots

5. **Add scheduling**
   - Generate launchd plist
   - Auto-start configuration

6. **Test with real data**
   - Small test backup
   - Verify restore
   - Measure performance

## Security Considerations

1. **Credentials**: Store in macOS Keychain, never in config files
2. **Encryption**: Optional client-side encryption before upload
3. **Permissions**: Read-only access to system files
4. **Logging**: Don't log sensitive paths or data
5. **Network**: HTTPS only, verify certificates

## Performance Targets

- **Scan speed**: 10,000 files/second
- **Upload speed**: Limited by network (target: 10 MB/s)
- **Memory usage**: < 200 MB for metadata
- **CPU usage**: < 20% during backup
- **Initial backup time**: 2-3 hours for 20 GB (on 50 Mbps connection)
- **Incremental backup**: < 5 minutes for typical changes

## Questions to Resolve

1. Does Nextcloud WebDAV support hard links or need to duplicate files?
2. Should we compress data before upload?
3. How to handle large files (>1 GB)?
4. Chunk size for uploads?
5. How to handle network interruptions mid-backup?
