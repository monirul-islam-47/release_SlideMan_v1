#!/usr/bin/env python
# main.py - Entry point for SLIDEMan application
import os
import sys

# Add resource_path helper for PyInstaller
def resource_path(rel_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, rel_path)

# Add the src directory to Python path
src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

if __name__ == "__main__":
    # Import and run the main function from slideman.__main__
    from slideman.__main__ import main
    main()
