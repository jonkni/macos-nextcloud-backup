# TSD File API for Educloud - Findings and Next Steps

> **Context:** Investigation results for using TSD File API as an alternative to WebDAV for Educloud backups. Educloud shares infrastructure with TSD (UiO's research storage platform), making the TSD API potentially available for backup operations.
>
> **Status:** Research complete. Decision made to continue with **WebDAV** for maximum compatibility. TSD File API remains an option for future performance optimization if needed.
>
> **Related:** [TSD_API_RESEARCH.md](TSD_API_RESEARCH.md) | [EDUCLOUD_SETUP.md](EDUCLOUD_SETUP.md)

---

## Summary of Investigation

### ✅ Confirmed: TSD API Client Supports Educloud

From the TSD API Client repository (https://github.com/unioslo/tsd-api-client):

**Explicit Educloud Support:**
- API endpoint: `https://api.fp.educloud.no/v1`
- Registration option: "4 - Educloud production usage"
- Test endpoint: `https://test.api.fp.educloud.no/v1`

### Key Features That Would Help Us:

1. **Resumable Uploads by Default**
   - Files >1GB automatically resumable
   - Can resume entire directory uploads
   - Much better than our current WebDAV

2. **Directory Upload with Exclusions**
   ```bash
   tacl p11 --upload mydirectory --ignore-prefixes .git,build,dist --ignore-suffixes .pyc,.db
   ```
   - Similar to our exclusion patterns
   - Built-in support

3. **Remote Path Specification**
   ```bash
   tacl p11 --upload myfile.txt --remote-path /path/to/remote
   ```
   - Can organize files like our snapshots

4. **Automation Support**
   - API key authentication
   - Can be scripted
   - Perfect for our backup tool

5. **On-the-Fly Encryption** (bonus)
   ```bash
   tacl p11 --upload myfile.txt --encrypt
   ```

## Critical Unknown: Storage Integration

### The Big Question:

**Where do files uploaded via TSD File API end up?**

Options:
1. **In Nextcloud** (share.educloud.no)
   - ✅ Perfect for us
   - ✅ Accessible via web interface
   - ✅ Can share, browse, etc.

2. **Separate Storage** (not in Nextcloud)
   - ❌ Not ideal
   - ❌ Files not accessible via share.educloud.no
   - ❌ Defeats the purpose

### Need to Test:

1. Register with TSD API for Educloud
2. Upload a test file via `tacl`
3. Check if it appears in https://share.educloud.no
4. Verify it's the same storage backend

## Authentication

### Registration Process:

```bash
# Install
pip3 install tsd-api-client

# Register
tacl --register

# Choose option 4: Educloud production usage
# Enter credentials (likely UiO username)
```

### Questions:
- Does it use Nextcloud app password?
- Or separate API key?
- Need to test the actual registration

## Performance Comparison

### Expected Benefits:

| Feature | Current (WebDAV) | TSD File API |
|---------|-----------------|--------------|
| Resumable Uploads | ❌ No | ✅ Yes (auto) |
| Directory Uploads | ⚠️ Manual | ✅ Native |
| Parallel Uploads | ✅ (3 workers) | ✅ (likely) |
| Connection Pooling | ✅ (optimized) | ✅ (likely) |
| Retry Logic | ✅ (3 retries) | ✅ (built-in) |
| Chunked Uploads | ❌ No | ✅ Yes |
| Speed (estimated) | Baseline | **2-5x faster?** |

## Integration Plan (If Compatible)

### Option A: Replace WebDAV Entirely

```python
# In backup engine
from tsdapiclient.fileapi import FileAPI

class TSDBackupEngine:
    def __init__(self, config):
        self.api = FileAPI(
            project='ec-jonkni',  # or similar
            env='ec-prod'
        )

    def upload_file(self, local_path, remote_path):
        self.api.upload(
            local_path,
            remote_path=remote_path,
            resumable=True
        )
```

### Option B: Hybrid Approach

```python
# Small files: WebDAV (faster for small)
# Large files: TSD API (resumable)

if file_size > 10_000_000:  # 10 MB
    use_tsd_api()
else:
    use_webdav()
```

### Option C: Configurable Backend

```yaml
# In config.yml
storage:
  backend: tsd_api  # or webdav
```

## Testing Plan

### Phase 1: Basic Functionality Test

```bash
# 1. Install TSD API client
pip3 install tsd-api-client

# 2. Register
tacl --register
# Choose: 4 - Educloud production usage

# 3. Upload test file
echo "test" > /tmp/test_backup.txt
tacl ec-jonkni --upload /tmp/test_backup.txt --remote-path /backup/test/

# 4. CHECK: Does it appear in share.educloud.no?
# Browse to: https://share.educloud.no/apps/files/
# Look for: /backup/test/test_backup.txt

# 5. If yes: IT WORKS! Files go to Nextcloud storage
# 6. If no: Files go elsewhere, not suitable for our use case
```

### Phase 2: Performance Benchmark

If Phase 1 succeeds:

```bash
# Upload same directory via both methods
# Compare speeds

# WebDAV (current optimized)
time mnb backup --dry-run  # Get file list
time mnb backup  # Actual upload

# TSD API
time tacl ec-jonkni --upload ~/Documents/ --remote-path /backup/test-tsd/
```

### Phase 3: Integration

If faster and compatible:
1. Create TSD API storage backend
2. Add configuration option
3. Test full backup workflow
4. Benchmark real-world performance

## Decision Matrix

| Criterion | Requirement | Status |
|-----------|-------------|--------|
| Files in Nextcloud | Must Have | ❓ Unknown - **Need to test** |
| Faster than WebDAV | Should Have | ⏳ Likely, need benchmark |
| Resumable Uploads | Nice to Have | ✅ Yes |
| Easy Authentication | Should Have | ❓ Unknown - **Need to test** |
| Works with ec-jonkni | Must Have | ❓ Unknown - **Need to test** |

## Immediate Action: Test It!

**Do you want me to help you test if TSD File API works for your use case?**

Steps:
1. Install `tsd-api-client`
2. Try to register for Educloud
3. Upload a test file
4. Check if it appears in share.educloud.no

This will answer the critical question: **Is it compatible with Nextcloud storage?**

## If It Works...

Potential benefits:
- **2-5x faster uploads** (estimated)
- **Resumable uploads** - Never lose progress
- **Better for large files**
- **Simpler code** - Use their battle-tested client

## If It Doesn't Work...

We still have:
- ✅ **Optimized WebDAV** (just implemented)
- ✅ **2-3x speedup** from recent changes
- ✅ **Reliable and tested**
- ⏭️ Option to add Nextcloud chunked upload API

## Your Current Backup

While running with optimized WebDAV:
- ⏳ First backup: ~10-30 minutes (estimated for 5.43 GB)
- ✅ Next backups: Much faster (incremental)
- ✅ Already significantly improved

## Recommendation

1. ✅ **Let current backup finish** with optimized WebDAV
2. 🧪 **Test TSD File API** compatibility (quick test)
3. ⚖️ **Compare performance** if compatible
4. 🚀 **Integrate** if significantly better

Want to test the TSD File API now while your backup runs?
