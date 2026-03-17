#!/usr/bin/env python3
"""Launcher script for macOS Nextcloud Backup GUI."""

import sys
from pathlib import Path

# Add the package to path
repo_dir = Path(__file__).parent
sys.path.insert(0, str(repo_dir))

print("Starting MNB GUI...")
print("If you don't see 'MNB' in menu bar:")
print("1. Check top-right corner (near clock)")
print("2. If too many menu bar items, some may be hidden")
print("3. Try: System Settings → Control Center → Show in Menu Bar")
print()

# Import and run GUI
from mnb.gui.menubar import main

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
