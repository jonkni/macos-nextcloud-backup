#!/bin/bash
# Test workflow for macOS Nextcloud Backup
# This script demonstrates basic functionality

set -e  # Exit on error

echo "=== macOS Nextcloud Backup - Test Workflow ==="
echo

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if mnb is installed
if ! command -v mnb &> /dev/null; then
    echo "Error: mnb command not found"
    echo "Install with: pip install -e ."
    exit 1
fi

echo -e "${GREEN}✓ mnb command found${NC}"
echo

# Test 1: Version
echo "Test 1: Check version"
mnb --version
echo

# Test 2: Help
echo "Test 2: Check help"
mnb --help > /dev/null
echo -e "${GREEN}✓ Help works${NC}"
echo

# Test 3: Commands exist
echo "Test 3: Check all commands exist"
for cmd in init backup status list estimate clean config schedule; do
    if mnb $cmd --help > /dev/null 2>&1; then
        echo -e "${GREEN}✓ $cmd command exists${NC}"
    else
        echo -e "${YELLOW}⚠ $cmd command missing or broken${NC}"
    fi
done
echo

# Test 4: Check if config exists
echo "Test 4: Configuration status"
if [ -f ~/.config/mnb/config.yml ]; then
    echo -e "${GREEN}✓ Configuration found${NC}"
    echo "Location: ~/.config/mnb/config.yml"
    echo
    echo "You can test with:"
    echo "  mnb status           # Show backup status"
    echo "  mnb estimate         # Estimate backup size"
    echo "  mnb backup --dry-run # Test backup without uploading"
else
    echo -e "${YELLOW}⚠ No configuration found${NC}"
    echo
    echo "Initialize with: mnb init"
    echo
    echo "You'll need:"
    echo "  - Nextcloud URL (e.g., https://share.educloud.no)"
    echo "  - Username"
    echo "  - Password"
fi
echo

echo "=== Test workflow complete ==="
echo
echo "Next steps:"
echo "  1. Initialize: mnb init"
echo "  2. Estimate size: mnb estimate"
echo "  3. Test backup: mnb backup --initial --dry-run"
echo "  4. Real backup: mnb backup --initial"
echo
echo "For more info: cat QUICKSTART.md"
