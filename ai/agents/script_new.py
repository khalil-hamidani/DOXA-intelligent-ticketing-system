from pathlib import Path
import sys
import importlib

# Ensure repository root (parent of `ai/`) is on sys.path so we can import the package `ai`.
repo_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(repo_root))

# Import the real module under its package path and re-export `app`
real = importlib.import_module("ai.script_new")
app = real.app
