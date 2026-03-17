#!/bin/bash
# Test script for TSD File API integration with Educloud

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${CYAN}=== TSD File API Test for Educloud ===${NC}"
echo

# Step 1: Check if tacl is installed
echo -e "${YELLOW}Step 1: Checking tacl installation...${NC}"
if ! command -v tacl &> /dev/null; then
    echo -e "${RED}Error: tacl not found${NC}"
    echo "Install with: pip3 install tsd-api-client"
    exit 1
fi
echo -e "${GREEN}✓ tacl installed: $(tacl --version | head -1)${NC}"
echo

# Step 2: Check current config
echo -e "${YELLOW}Step 2: Checking current registrations...${NC}"
tacl --config-show 2>/dev/null || echo "No registrations yet"
echo

# Step 3: Registration instructions
echo -e "${YELLOW}Step 3: Registration${NC}"
echo "To register with Educloud, run:"
echo -e "${CYAN}  tacl --register${NC}"
echo
echo "When prompted:"
echo "  1. Choose: ${GREEN}4${NC} - for Educloud normal production usage"
echo "  2. Enter project/username: ${GREEN}ec-jonkni${NC} (or similar)"
echo "  3. Enter your UiO password (or app password)"
echo "  4. Complete 2FA if prompted"
echo
read -p "Have you already registered? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Please run registration first:"
    echo -e "${CYAN}  tacl --register${NC}"
    echo
    echo "Then run this script again."
    exit 0
fi
echo

# Step 4: Create test file
echo -e "${YELLOW}Step 4: Creating test file...${NC}"
TEST_FILE="/tmp/mnb_test_$(date +%s).txt"
cat > "$TEST_FILE" <<EOF
macOS Nextcloud Backup - TSD API Test
Generated: $(date)
Purpose: Testing if TSD File API uploads to Nextcloud storage
EOF
echo -e "${GREEN}✓ Created: $TEST_FILE${NC}"
echo "Content:"
cat "$TEST_FILE"
echo

# Step 5: Upload test file
echo -e "${YELLOW}Step 5: Uploading test file via TSD API...${NC}"
REMOTE_PATH="/mnb-test/tsd-api-test"
echo "Remote path: $REMOTE_PATH"
echo "Command: tacl ec-jonkni --upload $TEST_FILE --remote-path $REMOTE_PATH"
echo

if tacl ec-jonkni --upload "$TEST_FILE" --remote-path "$REMOTE_PATH"; then
    echo -e "${GREEN}✓ Upload successful!${NC}"
else
    echo -e "${RED}✗ Upload failed${NC}"
    echo "This might mean:"
    echo "  1. Not registered yet (run: tacl --register)"
    echo "  2. Wrong project name (try: tacl --config-show)"
    echo "  3. Authentication issue"
    exit 1
fi
echo

# Step 6: Verification instructions
echo -e "${YELLOW}Step 6: CRITICAL - Verify file location${NC}"
echo
echo -e "${CYAN}=== ACTION REQUIRED ===${NC}"
echo "1. Open your browser and go to:"
echo -e "   ${GREEN}https://share.educloud.no/apps/files/${NC}"
echo
echo "2. Look for the test file in one of these locations:"
echo "   - ${CYAN}/$REMOTE_PATH/$(basename $TEST_FILE)${NC}"
echo "   - ${CYAN}/mnb-test/tsd-api-test/$(basename $TEST_FILE)${NC}"
echo "   - Or search for: ${CYAN}$(basename $TEST_FILE)${NC}"
echo
echo "3. ${YELLOW}If you find the file in Nextcloud:${NC}"
echo "   ✅ ${GREEN}SUCCESS!${NC} TSD API uploads to Nextcloud storage!"
echo "   → We can use TSD API for much faster backups"
echo "   → Expected speedup: 3-8x faster than WebDAV"
echo
echo "4. ${YELLOW}If you DON'T find the file in Nextcloud:${NC}"
echo "   ❌ ${RED}Files go to separate storage${NC}"
echo "   → TSD API not suitable for our use case"
echo "   → Stick with optimized WebDAV (still 2-5x faster)"
echo
echo "5. ${YELLOW}Try downloading the file via TSD API:${NC}"
echo "   Run: ${CYAN}tacl ec-jonkni --download-list $REMOTE_PATH${NC}"
echo "   This will show what files are available via TSD API"
echo
echo -e "${CYAN}=== Please check and report back! ===${NC}"
echo
echo "Cleanup (after testing):"
echo "  rm $TEST_FILE"
echo "  tacl ec-jonkni --download-delete $(basename $TEST_FILE)"
