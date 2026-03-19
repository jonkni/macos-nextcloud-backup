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

**Overall Status: 🎉 Core Product Complete (v1.0)**

As of March 2026:
- ✅ Phase 1: Core Backend - COMPLETED
- ✅ Phase 2: CLI Tool - COMPLETED
- ✅ Phase 3: Scheduling - COMPLETED
- ✅ Phase 4: GUI Application - COMPLETED
- ⚙️ Phase 5: Advanced Features - IN PROGRESS

The backup system is fully functional and deployed. Focus has shifted to:
- Bug fixes and stability improvements
- Performance optimizations
- Advanced features (encryption, verification)
- Documentation and user experience

---

### Phase 1: Core Backend (Priority: High) ✅ COMPLETED

**Week 1: Foundation**
- [x] Project structure setup
- [x] WebDAV client wrapper
  - [x] Test connection
  - [x] Upload/download files
  - [x] Directory operations
  - [x] Batch directory creation
  - [x] Parallel uploads support
- [x] Configuration system
  - [x] YAML parsing
  - [x] Keychain integration for passwords
  - [x] Validation
  - [x] Include/exclude patterns

**Week 2: Backup Engine**
- [x] File scanner
  - [x] Walk directory tree
  - [x] Apply exclusion patterns
  - [x] Calculate checksums (fast hash)
- [x] Change detection
  - [x] Compare mtime/size
  - [x] Content hash (checksum)
  - [x] Metadata database (SQLite)
  - [x] Track upload failures for retry
- [x] Snapshot creation
  - [x] Upload changed files
  - [x] Create snapshot metadata
  - [x] Reference unchanged files (metadata links)
  - [x] Cleanup incomplete snapshots

### Phase 2: CLI Tool (Priority: High) ✅ COMPLETED

**Commands implemented:**
```
mnb init                    # [x] Initial setup wizard
mnb config show             # [x] Show configuration
mnb config set              # [x] Set configuration values
mnb backup [--initial]      # [x] Run backup (with --dry-run, --force)
mnb status                  # [x] Show backup status
mnb list                    # [x] List snapshots (with --all, --limit)
mnb restore                 # [ ] Restore files (basic structure, needs full implementation)
mnb estimate                # [x] Estimate storage requirements
mnb clean                   # [x] Clean old snapshots (with retention policy)
mnb schedule                # [x] Setup automatic backups (with --interval, --disable, --status)
```

**Additional features implemented:**
- [x] Progress bars with tqdm
- [x] Network connectivity checks
- [x] Backup locking (prevent concurrent backups)
- [x] Timestamped logging
- [x] Colored output
- [x] Dry-run mode for testing

### Phase 3: Scheduling (Priority: High) ✅ COMPLETED

- [x] launchd plist generation
- [x] Auto-start on login (RunAtLoad)
- [x] Notification on completion/error (via GUI, webhook support added)
- [x] Log routing (stdout/stderr to separate files)
- [ ] Log rotation (manual cleanup needed, not automatic)

### Phase 4: GUI Application (Priority: Medium) ✅ COMPLETED

- [x] Menu bar icon (rumps-based)
- [x] Status display (last backup time, file count, size)
- [x] Manual backup trigger
- [x] View logs (opens in Console.app)
- [x] Settings panel (opens config file in editor)
- [x] Schedule toggle (enable/disable automatic backups)
- [x] Auto-refresh status (30-second timer)
- [ ] View recent snapshots (removed - CLI preferred for browsing)
- [ ] Restore files UI (removed - CLI preferred for restore)
- [ ] Custom icon (using system default)

### Phase 5: Advanced Features (Priority: Low)

- [ ] Backup encryption (AES-256)
- [x] Bandwidth throttling (max_upload_speed config)
- [x] Parallel uploads (configurable worker threads)
- [ ] Backup verification
- [ ] Multi-Nextcloud support
- [ ] Web dashboard

**Additional features implemented:**
- [x] Network connectivity validation
- [x] Backup locking mechanism
- [x] Failed upload retry tracking
- [x] Configurable checksum modes (fast/full)
- [x] Flexible retention policies
- [x] Webhook notifications (Google Chat, Zabbix)
- [x] Exclude pattern support (with glob matching)

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

**Actual Implementation** (as of March 2026):

> Note: The implementation consolidated several planned modules for simplicity. For example, `detector.py` and `snapshot.py` were merged into `backup_engine.py` for better cohesion.

```
macos-nextcloud-backup/
├── README.md
├── PLAN.md
├── QUICKSTART.md
├── GUI.md
├── EDUCLOUD_SETUP.md        # Platform-specific setup
├── TSD_API_*.md             # Platform research docs
├── LICENSE
├── setup.py
├── requirements.txt
├── config.example.yml       # Example configuration
├── .gitignore
├── mnb/                     # Main package
│   ├── __init__.py
│   ├── __main__.py          # Entry point
│   ├── cli/                 # CLI interface
│   │   ├── __init__.py
│   │   └── main.py          # All CLI commands (consolidated)
│   ├── core/                # Core logic
│   │   ├── __init__.py
│   │   ├── backup_engine.py # Backup orchestration + detection + snapshots
│   │   └── scanner.py       # File scanning with exclusions
│   ├── storage/             # Storage backends
│   │   ├── __init__.py
│   │   ├── webdav.py        # WebDAV/Nextcloud client
│   │   └── metadata.py      # SQLite metadata database
│   ├── config/              # Configuration
│   │   ├── __init__.py
│   │   ├── manager.py       # Config + keychain integration
│   │   └── schema.py        # Default config schema
│   ├── gui/                 # GUI application
│   │   ├── __init__.py
│   │   └── menubar.py       # macOS menu bar app (rumps)
│   └── utils/               # Utilities
│       ├── __init__.py
│       ├── exclude.py       # Pattern matching for exclusions
│       ├── lock.py          # Backup locking mechanism
│       ├── network.py       # Network connectivity checks
│       ├── progress.py      # Progress tracking utilities
│       └── scheduler.py     # launchd integration
├── tests/                   # Tests
│   ├── test_scanner.py
│   ├── test_webdav.py
│   └── test_backup.py
├── launch-gui.py            # GUI launcher script
└── test_workflow.sh         # Integration test script
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

## Design Questions & Resolutions

These questions were resolved during implementation:

### 1. Does Nextcloud WebDAV support hard links or need to duplicate files?

**Answer:** ❌ Hard links not supported in WebDAV.

**Solution Implemented:** Metadata-based references. The SQLite database tracks which files exist in each snapshot via `remote_path`. Unchanged files reference their location from the previous snapshot without re-uploading. This achieves similar space savings without requiring WebDAV hard link support.

**Implementation:** See `metadata.py` - files table with `uploaded` flag tracks which files were actually uploaded vs. referenced.

### 2. Should we compress data before upload?

**Answer:** ❌ No client-side compression.

**Rationale:**
- Nextcloud handles storage efficiency server-side
- Many file types already compressed (images, videos, compressed archives)
- Client-side compression adds CPU overhead and complexity
- Would complicate restore process (need to decompress)
- No clear benefit for most backup content

**Decision:** Upload files as-is, rely on Nextcloud's storage management.

### 3. How to handle large files (>1 GB)?

**Answer:** ✅ Chunked uploads via WebDAV.

**Implementation:**
- Configurable chunk size: `backup.chunk_size: 10` (MB) in config.yml
- WebDAV client handles chunked transfer automatically
- Works well for large files without memory issues

**Code:** See `webdav.py` - chunked upload support built into WebDAV client.

### 4. Chunk size for uploads?

**Answer:** ✅ 10 MB default, configurable.

**Configuration:**
```yaml
backup:
  chunk_size: 10  # MB, adjust based on network reliability
```

**Rationale:** 10 MB balances memory usage with upload efficiency. Users can adjust based on network conditions.

### 5. How to handle network interruptions mid-backup?

**Answer:** ✅ Multi-layered approach.

**Implementation:**
1. **Upload tracking:** Failed uploads marked with `uploaded: false` in metadata
2. **Automatic retry:** Next backup detects failed uploads and retries them
3. **Incomplete snapshot cleanup:** Snapshots stuck in `in_progress` automatically marked as failed on next backup start
4. **Network validation:** Pre-flight connectivity check before starting backup
5. **Connection pooling:** WebDAV client reuses connections for reliability

**Code:**
- `metadata.py`: `has_file_changed()` returns `True` for failed uploads
- `backup_engine.py`: `_cleanup_incomplete_snapshots()` handles stuck snapshots
- `network.py`: `check_nextcloud_connectivity()` validates before backup
