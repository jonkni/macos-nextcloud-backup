# API Investigation: WebDAV vs Nextcloud File API vs Educloud API

## Current Situation

We're using **WebDAV** for file operations, which can be slow because:
- HTTP overhead for each operation
- Multiple round-trips for directory creation
- Less efficient for bulk operations
- No built-in chunking/resumable uploads in our implementation

## Available Options

### 1. **WebDAV** (Current)

**Protocol**: HTTP-based WebDAV (RFC 4918)

**Pros:**
- ✅ Standard protocol, widely supported
- ✅ Files accessible in Nextcloud web interface
- ✅ Works with all Nextcloud instances
- ✅ Simple authentication

**Cons:**
- ❌ Slower for many small files
- ❌ Higher overhead per operation
- ❌ Limited metadata capabilities

**Speed**: ~1-5 MB/s for many small files, better for large files

---

### 2. **Nextcloud REST API** (OCS API + Files API)

**Protocol**: Nextcloud's native REST API

**Documentation**: https://docs.nextcloud.com/server/latest/developer_manual/client_apis/

**Endpoints:**
- `/ocs/v2.php/apps/files_sharing/api/v1/` - Sharing
- `/remote.php/dav/files/` - Still uses WebDAV under the hood
- `/ocs/v1.php/apps/files/api/v1/` - File operations

**Key Features:**
- Chunked uploads: `/remote.php/dav/uploads/{user}/`
- Bulk operations
- Better error handling
- Metadata support

**Pros:**
- ✅ Files still in Nextcloud, fully accessible via web
- ✅ Chunked uploads (resumable!)
- ✅ Better for large files
- ✅ Can get file info more efficiently

**Cons:**
- ❌ Still HTTP-based (some overhead)
- ❌ More complex implementation
- ❌ May not be much faster for many small files

**Speed**: ~5-15 MB/s with chunking, better for large files

---

### 3. **Educloud/NREC API** (if it exists)

**What is Educloud?**
- Norwegian Research and Education Cloud (NREC)
- Operated by University of Oslo
- Uses OpenStack infrastructure
- Nextcloud is ONE service running on this infrastructure

**Possible APIs:**
1. **OpenStack Swift API** (object storage)
   - If Nextcloud uses Swift as storage backend
   - Direct access to object storage
   - Files would NOT be in Nextcloud interface

2. **NREC/Educloud specific API**
   - Need to investigate if this exists
   - Might be for provisioning/management, not file storage

**Investigation needed:**
- Does Educloud expose a direct file API?
- Is it separate from Nextcloud or integrated?
- Would files still appear in Nextcloud web interface?

---

## Performance Comparison

### Test Case: Backup 2136 files, 5.43 GB

| Method | Small Files | Large Files | Total Time (est) | Files in Nextcloud? |
|--------|-------------|-------------|------------------|---------------------|
| **WebDAV** (current) | Slow | Good | 30-60 min | ✅ Yes |
| **Nextcloud Chunked Upload** | Medium | Fast | 15-30 min | ✅ Yes |
| **Direct Object Storage** | Fast | Fast | 10-20 min | ❌ No |

---

## Recommendations

### Option A: **Optimize Current WebDAV** (Quick Win)

Improvements we can make NOW:
1. **Parallel uploads** (already configured but not fully utilized)
2. **Connection pooling** (reuse HTTP connections)
3. **Batch directory creation**
4. **Progress tracking only every N files**

**Effort**: Low (few hours)
**Speed improvement**: 2-3x faster
**Files in Nextcloud**: ✅ Yes

### Option B: **Switch to Nextcloud Chunked Upload API** (Better)

Use Nextcloud's chunked upload API:
- Better for large files
- Resumable uploads
- Still stores in Nextcloud

**Effort**: Medium (1-2 days)
**Speed improvement**: 3-5x faster for large files
**Files in Nextcloud**: ✅ Yes

### Option C: **Hybrid Approach** (Best)

Use different methods based on file size:
- Small files (<10 MB): Optimized WebDAV with parallel uploads
- Large files (>10 MB): Chunked upload API

**Effort**: Medium-High (2-3 days)
**Speed improvement**: 4-6x faster overall
**Files in Nextcloud**: ✅ Yes

---

## Questions to Answer

### For Educloud Specific API:

1. **Does Educloud expose a direct file API separate from Nextcloud?**
   - Need to check Educloud/NREC documentation
   - Contact UiO IT support

2. **If yes, are files stored there accessible via Nextcloud interface?**
   - Critical for usability
   - Need to test integration

3. **Is it actually faster than Nextcloud's own APIs?**
   - Need benchmarks
   - May not be worth the complexity

---

## Next Steps

### Immediate (Today):

1. **Optimize current WebDAV implementation**
   - Add connection pooling
   - Improve parallel upload logic
   - Better progress tracking

2. **Research Educloud APIs**
   - Check https://docs.nrec.no/
   - Look for file storage APIs
   - Test if they integrate with Nextcloud

### Short-term (This Week):

1. **Implement Nextcloud chunked uploads**
   - For files >10 MB
   - Resumable functionality
   - Better error handling

2. **Benchmark different approaches**
   - Measure actual speed differences
   - Test with your real data

### Questions for You:

1. Do you have access to any Educloud/NREC documentation about APIs?
2. Is it important that files remain accessible via Nextcloud web interface?
3. What's more important: speed or simplicity?

---

## My Recommendation

**Start with Option A (Optimize WebDAV)** because:
1. Quick to implement (can do while backup runs)
2. 2-3x speed improvement with low risk
3. No compatibility concerns
4. Files stay in Nextcloud

**Then consider Option C (Hybrid)** if speed is still an issue:
1. Use chunked uploads for large files
2. Keep optimized WebDAV for small files
3. Best of both worlds

**Skip direct Educloud API unless:**
1. It's documented and accessible
2. Files remain in Nextcloud
3. Proven to be significantly faster

---

## Questions?

- Want me to implement WebDAV optimizations now?
- Should I research Educloud/NREC APIs further?
- Do you have links to Educloud API documentation?
