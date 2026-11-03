#!/usr/bin/env python3
"""Use the shared measure checker in this CSE checkout from any directory."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scripts.measures import main

if __name__ == '__main__':
    raise SystemExit(main())
