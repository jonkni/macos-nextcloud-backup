# TSD File API for Educloud - Investigation

> **Context:** This document investigates whether the TSD File API (used by UiO's research storage platform) could be a better alternative to WebDAV for uploading backups to Educloud. Since Educloud and TSD share infrastructure, the TSD File API is potentially accessible for Educloud storage operations.
>
> **Current Implementation:** The backup tool uses **WebDAV** (standard Nextcloud protocol). This investigation explores whether switching to TSD File API would offer better performance or reliability.
>
> **Related:** See [EDUCLOUD_SETUP.md](EDUCLOUD_SETUP.md) for standard WebDAV-based setup instructions.

---

## Correction: TSD File API Works for Educloud!

Based on https://www.uio.no/english/services/it/research/platforms/edu-research/help/storage-guide.html:

The **TSD File API** is used for BOTH:
- TSD (Tjeneste for Sensitive Data)
- **Educloud storage**

## TSD API Client Analysis

Repository: https://github.com/unioslo/tsd-api-client

### Features:
- File upload/download via REST API
- Resumable uploads
- Chunked transfers
- Streaming support
- Import/export functionality

### Key Benefits Over WebDAV:
1. **Resumable uploads** - Can continue after network interruption
2. **Chunked transfers** - Better for large files
3. **Optimized protocol** - Purpose-built for file transfer
4. **Likely faster** - Less HTTP overhead

## Questions to Answer

### 1. Authentication
- Does it use the same Nextcloud credentials?
- Or different API tokens?
- How to get credentials?

### 2. File Accessibility
- **Critical**: Will files uploaded via TSD File API appear in Nextcloud web interface?
- Are they in the same storage backend?
- Can we access them via WebDAV too?

### 3. Performance
- How much faster is it vs WebDAV?
- Actual benchmarks?

### 4. Compatibility with Our Use Case
- Can we use it for `share.educloud.no`?
- What's the API endpoint?
- Does it work with our authentication (app password)?

## Next Steps to Investigate

### 1. Check TSD API Client Documentation

```bash
# Clone the repo
git clone https://github.com/unioslo/tsd-api-client.git
cd tsd-api-client

# Read documentation
cat README.md
ls docs/
```

### 2. Find API Endpoint for Educloud

From storage guide, look for:
- Educloud API endpoint URL
- Authentication method
- Whether it's the same as Nextcloud storage

### 3. Test Compatibility

Questions:
- Can we use `ec-jonkni` username and app password?
- Or need different credentials?
- Does it access Nextcloud storage or separate?

### 4. Prototype Integration

If compatible:
- Create TSD File API client wrapper
- Test upload to Educloud
- Verify files appear in Nextcloud web interface
- Benchmark speed vs WebDAV

## Research Tasks

### Task 1: Read TSD API Client README
- [ ] Clone repository
- [ ] Read documentation
- [ ] Understand authentication model
- [ ] Find Educloud-specific setup

### Task 2: Test Authentication
- [ ] Try connecting to Educloud with TSD client
- [ ] See if Nextcloud credentials work
- [ ] Or find how to get API credentials

### Task 3: Verify Storage Backend
- [ ] Upload test file via TSD API
- [ ] Check if it appears in Nextcloud
- [ ] Confirm same storage backend

### Task 4: Benchmark Performance
- [ ] Upload same files via WebDAV and TSD API
- [ ] Compare speeds
- [ ] Measure improvement

## Potential Implementation

If TSD File API works and is faster:

```python
# New storage backend option
from mnb.storage.tsd_api import TSDAPIClient

# In backup engine
if config.get('storage.backend') == 'tsd_api':
    self.storage = TSDAPIClient(...)
else:
    self.storage = WebDAVClient(...)
```

### Benefits:
- Faster uploads
- Resumable uploads
- Better for large files
- Still accessible in Nextcloud (if confirmed)

### Concerns:
- Different authentication?
- Additional complexity
- Need to maintain two backends
- Compatibility with all Nextcloud features?

## Current Status

✅ **WebDAV optimizations completed** (connection pooling, parallel uploads, caching)
🔍 **TSD File API investigation needed** (this document)

## Action Plan

1. **Let current backup complete** with optimized WebDAV
2. **Measure current performance** - baseline for comparison
3. **Investigate TSD File API** thoroughly:
   - Clone repo and read docs
   - Test authentication
   - Verify Nextcloud integration
   - Benchmark if successful
4. **Implement if worthwhile**:
   - Only if significantly faster (>2x)
   - Only if files still in Nextcloud
   - Only if authentication works

## Decision Criteria

Implement TSD File API if:
- ✅ Files appear in Nextcloud web interface
- ✅ Can authenticate with existing credentials (or easy to get new ones)
- ✅ >2x faster than optimized WebDAV
- ✅ Resumable uploads work
- ✅ Reasonable implementation effort

Skip TSD File API if:
- ❌ Files don't appear in Nextcloud
- ❌ Complex authentication setup
- ❌ Not significantly faster
- ❌ Breaking changes to architecture

## Want Me To Investigate Now?

I can:
1. Clone tsd-api-client repository
2. Read the documentation
3. Try to understand Educloud integration
4. Test if it works with your credentials
5. Benchmark against WebDAV

Should I proceed with the investigation?
