#!/usr/bin/env python3
"""Show sampled-trace input shapes or check a byte-bound language-1 trace."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from verifier.sampled_trace import main


if __name__ == "__main__":
    raise SystemExit(main())
