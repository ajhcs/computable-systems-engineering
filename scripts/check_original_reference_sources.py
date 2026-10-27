#!/usr/bin/env python3
"""Optional local reserialized-source-slice identity check. No source fragments are distributed.

This checks selected, reserialized fragment bytes against historical local comparison digests. It does
not fetch sources, write fragments, authenticate provenance, or establish source
correctness, independent engineering validation or full v1/v2 equivalence.
"""
from pathlib import Path
import argparse, hashlib, json, sys
import xml.etree.ElementTree as ET
EXPECTED = {'engineering-reference/source/tmt-maintenance.xml': '8590fd8e2b9d597068e70bd4f8c379ff17538a1b1d72bf193066acd1341bee1f', 'engineering-reference/source/tmt-timing.xml': '0cc4519ee89f34919bec6e1675de9c7cc38d237a86a89f714e6958d64055aa6a', 'engineering-reference/source/ape-composition.xml': 'a9b3e1dc735868e14732194cc6b677f8dacb9d6068232b35b2d928928f78dfa9', 'engineering-reference/source/ape-optical.xml': 'bae7b75ebb4e3e407e371b6acb5c8349a6d7df3ed6c3412338636394aad0e26e', 'engineering-reference-extension/source/tmt-exposure.xml': '6417309ac51b6667f1d6e3b0949b53a2f3ecc2e9219977fd8d732cc5b32e9164', 'engineering-reference-extension/source/tmt-sequence-order.xml': 'f653db948501eb08cf3526567b0976a299067db4d2a92449ac4037ad60e3c847'}
def check_local_slices(source_root, expected=None):
 expected=EXPECTED if expected is None else expected
 rows=[]
 for name,digest in sorted(expected.items()):
  path=Path(source_root)/name
  data=path.read_bytes()
  if hashlib.sha256(data).hexdigest()!=digest:raise ValueError('Local reserialized source-slice identity mismatch: '+name)
  root=ET.fromstring(data)
  rows.append({'slice':name,'sha256':digest,'elements':sum(1 for _ in root.iter())})
 return {'status':'pass','claim_scope':'optional-local-source-slice-identity','checks':rows,
         'limits':'Supplied local reserialized source-fragment bytes match historical comparison inputs, not original archive bytes. No archive identity, source authenticity, independent engineering validation, behavior or equivalence claim.'}
def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--source-root',type=Path,required=True,help='Explicit local examples root containing the six local reserialized source slices/fragments. These are not original archive bytes. No acquisition or fallback occurs.')
 args=parser.parse_args()
 try:result=check_local_slices(args.source_root)
 except (OSError,ValueError,ET.ParseError) as exc:
  print(json.dumps({'status':'error','claim_scope':'optional-local-source-slice-identity','error':str(exc)}));return 1
 print(json.dumps(result,indent=2));return 0
if __name__=='__main__':sys.exit(main())
