#!/usr/bin/env python3
import os
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
site_packages = os.path.join(script_dir, "lib", "python3.12", "site-packages")
if os.path.exists(site_packages):
    sys.path.insert(0, site_packages)
else:
    lib_dir = os.path.join(script_dir, "..", "lib", "python3.12", "site-packages")
    if os.path.exists(lib_dir):
        sys.path.insert(0, os.path.normpath(lib_dir))

from src.cli import main

if __name__ == "__main__":
    exit(main())
