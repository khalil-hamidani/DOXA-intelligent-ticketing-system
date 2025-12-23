"""Cleanup script for the `ai/` directory.
Removes __pycache__ directories and .pyc files recursively.
Run from repository root (or from ai/).
"""
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).parent

removed = {"pycache_dirs": [], "pyc_files": []}

for dirpath, dirnames, filenames in os.walk(ROOT):
    # remove __pycache__ directories
    for d in list(dirnames):
        if d == "__pycache__":
            p = Path(dirpath) / d
            try:
                shutil.rmtree(p)
                removed["pycache_dirs"].append(str(p))
            except Exception as e:
                print(f"Failed to remove {p}: {e}")
    # remove .pyc files
    for f in filenames:
        if f.endswith('.pyc'):
            p = Path(dirpath) / f
            try:
                p.unlink()
                removed["pyc_files"].append(str(p))
            except Exception as e:
                print(f"Failed to remove {p}: {e}")

print("Cleanup complete.")
print(f"Removed {len(removed['pycache_dirs'])} __pycache__ dirs and {len(removed['pyc_files'])} .pyc files")
if removed['pycache_dirs']:
    print('\n__pycache__ removed:')
    for p in removed['pycache_dirs']:
        print(' -', p)
if removed['pyc_files']:
    print('\n.pyc files removed:')
    for p in removed['pyc_files']:
        print(' -', p)
