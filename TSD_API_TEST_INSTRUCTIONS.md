# TSD File API Testing Instructions

## Goal
Test if TSD File API uploads files to Nextcloud (share.educloud.no) or separate storage.

## Step-by-Step Instructions

### Step 1: Register with TSD API

Run this command:
```bash
tacl --register
```

When prompted:
1. **Choose environment**: Type `4` and press Enter
   ```
   4 - for Educloud normal production usage
   ```

2. **Enter project name**: Type `ec-jonkni` (or whatever your Educloud project is)
   - This is likely your UiO username with `ec-` prefix
   - Example: `ec-jonkni`

3. **Enter password**: Use your UiO password or Nextcloud app password
   - Try app password first (the one you created for mnb)
   - If that doesn't work, try your regular UiO password

4. **Complete 2FA** if prompted

5. **Registration should complete** with a message saying it's valid for 1 year

### Step 2: Verify Registration

Check that registration worked:
```bash
tacl --config-show
```

You should see your `ec-jonkni` (or similar) registration listed.

### Step 3: Upload Test File

Run the automated test script:
```bash
cd ~/repos/macos-nextcloud-backup
./test_tsd_api.sh
```

This will:
- Create a test file
- Upload it via TSD File API
- Give you instructions to verify

### Step 4: CRITICAL - Check Nextcloud

**This is the most important step!**

1. Open browser: https://share.educloud.no/apps/files/

2. Look for the test file in these locations:
   - `/mnb-test/tsd-api-test/` folder
   - Search for files with `mnb_test` in the name

3. **If you find it**:
   - ✅ **SUCCESS!** TSD API uploads to Nextcloud!
   - ✅ We can integrate TSD API for faster backups
   - ✅ Expected: 3-8x faster than WebDAV

4. **If you DON'T find it**:
   - ❌ Files go to separate storage
   - ❌ TSD API not suitable for our use case
   - ❌ Stick with optimized WebDAV

### Step 5: Alternative Check

Try listing files via TSD API:
```bash
tacl ec-jonkni --download-list
tacl ec-jonkni --download-list /mnb-test/tsd-api-test
```

This shows what files are accessible via TSD API.

### Step 6: Report Results

**Please report back what you find:**

Option A - Success:
```
✅ Found the test file in Nextcloud at: [path]
✅ TSD API uploads to Nextcloud storage!
```

Option B - Not in Nextcloud:
```
❌ Test file NOT found in Nextcloud
✅ Can see file via: tacl ec-jonkni --download-list
❌ TSD API uses separate storage
```

## Cleanup After Testing

Once you've checked:
```bash
# Delete test file from your system
rm /tmp/mnb_test_*.txt

# Delete from remote (if in TSD storage)
tacl ec-jonkni --download-delete mnb_test_*.txt
```

## What This Tells Us

### If files ARE in Nextcloud:
- We can implement TSD API backend
- Much faster uploads (resumable, chunked)
- Better reliability
- Worth the integration effort

### If files are NOT in Nextcloud:
- TSD API uses different storage
- Files not accessible via share.educloud.no
- Not suitable for our backup use case
- Stick with optimized WebDAV (already 2-5x faster)

## Troubleshooting

### Registration fails
- Try using your regular UiO password instead of app password
- Check project name (might be different than ec-jonkni)
- Ensure you're choosing option 4 (Educloud production)

### Upload fails
- Check registration: `tacl --config-show`
- Try re-registering: `tacl --config-delete` then `tacl --register`
- Check project name matches your Educloud access

### Can't find file anywhere
- List available files: `tacl ec-jonkni --download-list`
- List with path: `tacl ec-jonkni --download-list /`
- Try different paths: `tacl ec-jonkni --download-list /mnb-test`

## Next Steps Based on Results

### If TSD API works with Nextcloud:
1. Benchmark speed vs WebDAV
2. Design TSD API storage backend
3. Implement integration
4. Test full backup workflow
5. Deploy to all 3 MacBooks

### If TSD API doesn't work with Nextcloud:
1. Continue using optimized WebDAV
2. Monitor backup speeds
3. Consider Nextcloud Chunked Upload API if needed
4. Focus on other features (scheduling, GUI)

---

**Ready to test!** Start with Step 1 above. 🚀
