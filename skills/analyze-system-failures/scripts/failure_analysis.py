#!/usr/bin/env python3
"""Run the shared CSE failure checker from any working directory."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scripts.failure_analysis import main

if __name__ == '__main__':
    raise SystemExit(main())
