# TSD File API Test Results

**Date:** 2026-03-17
**Tested by:** jonkni
**Verdict:** ❌ **NOT SUITABLE for Nextcloud backups**

## Test Summary

### What We Tested
Whether TSD File API uploads files to Nextcloud storage (share.educloud.no) or separate storage.

### Test Procedure
1. ✅ Installed `tsd-api-client` v3.7.2
2. ✅ Registered with TSD API for Educloud (projects: ec01, ec11, ec12)
3. ✅ Created test file: `/tmp/mnb_test.txt`
4. ✅ Uploaded via TSD API: `tacl ec11 --basic --upload /tmp/mnb_test.txt --remote-path /mnb-test/tsd-api-test`
5. ✅ Upload succeeded without errors
6. ❌ **File NOT found in Nextcloud** (searched share.educloud.no/apps/files/)

### Results

| Test | Result |
|------|--------|
| TSD API Upload | ✅ Success |
| File in Nextcloud | ❌ **NOT FOUND** |
| File in TSD Storage | ✅ Yes (separate storage) |
| Suitable for our use case | ❌ **NO** |

## Key Findings

### 1. TSD API Uses Separate Storage
- Files uploaded via TSD API go to **TSD/Educloud file storage**
- This is **separate from Nextcloud storage**
- Files are NOT accessible via share.educloud.no web interface
- Files can only be accessed via `tacl` commands

### 2. Not Compatible with Our Requirements
Our backup tool requires:
- ✅ Files accessible via Nextcloud web interface
- ✅ Can browse, search, share via share.educloud.no
- ✅ Standard Nextcloud features (versioning, sharing, etc.)

TSD API provides:
- ❌ Files in separate storage
- ❌ Only accessible via tacl CLI
- ❌ No Nextcloud web interface access

### 3. Why This Makes Sense
TSD/Educloud File API is designed for:
- **Research data workflows**
- **Automated data transfers**
- **Large-scale data import/export**
- **Command-line batch operations**

NOT designed for:
- Personal file backup
- Nextcloud integration
- Web-accessible storage

## Conclusion

**TSD File API is NOT suitable for our macOS Nextcloud backup tool.**

While it offers excellent features (resumable uploads, chunked transfers, automation), the fact that files don't end up in Nextcloud storage makes it incompatible with our use case.

## Recommendation: Optimized WebDAV

**Use our optimized WebDAV implementation** (already implemented and tested):

### Benefits:
- ✅ Files in Nextcloud storage
- ✅ Accessible via share.educloud.no
- ✅ 2-5x faster than original WebDAV
- ✅ Connection pooling and parallel uploads
- ✅ Proven, reliable technology
- ✅ Works with all Nextcloud features

### Performance:
- **Original WebDAV**: ~30-60 min for 5.43 GB
- **Optimized WebDAV**: ~10-20 min for 5.43 GB (2-3x faster)
- **TSD File API**: Would be faster, but files not in Nextcloud ❌

## Alternative Future Options

If WebDAV speed is still insufficient, consider:

1. **Nextcloud Chunked Upload API**
   - Use `/remote.php/dav/uploads/` endpoint
   - Resumable chunked uploads
   - Still stores in Nextcloud
   - ~20-30% additional speedup

2. **Network Optimization**
   - Use UiO on-campus network (eduroam)
   - 10 Gbps network vs home wifi
   - Biggest impact for large uploads

3. **Selective Backup**
   - Reduce what gets backed up
   - More aggressive exclusions
   - Faster backups, less storage

## Cleanup

Test files created during testing:
- `/tmp/mnb_test.txt` (local) - can be deleted
- `/mnb-test/tsd-api-test/mnb_test.txt` (TSD storage) - can be left or deleted via tacl

## Final Status

✅ **Testing complete**
✅ **Decision made: Use optimized WebDAV**
✅ **TSD API investigation closed**
✅ **Ready for production use**

---

**Next Steps:**
1. Complete initial backup with optimized WebDAV
2. Set up other 2 MacBooks
3. Implement automatic scheduling (launchd)
4. Optional: Add GUI menu bar app
