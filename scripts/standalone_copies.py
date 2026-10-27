#!/usr/bin/env python3
"""Check the maintained standalone-copy inventory without changing any files."""
from pathlib import Path
import json,sys

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from verifier.standalone import check_copies

if __name__=='__main__':
    report=check_copies(ROOT)
    print(json.dumps(report,sort_keys=True,indent=2))
    raise SystemExit(0 if report['status']=='pass' else 1)
