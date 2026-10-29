#!/usr/bin/env python3
"""Rasterize README sources with an explicitly selected installed Chromium."""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import struct
import sys
import tempfile
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'scripts'))
from check_reference_release import png_metadata

def digest(path):return sha256(path.read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--browser',type=Path,required=True)
    parser.add_argument('--library-path')
    args=parser.parse_args()
    environment=dict(os.environ)
    if args.library_path:environment['LD_LIBRARY_PATH']=args.library_path
    scratch=ROOT/'.tmp';scratch.mkdir(exist_ok=True)
    version=subprocess.run([str(args.browser),'--version'],env=environment,capture_output=True,text=True,check=True).stdout.strip()
    sources=[(HERE/'cse-overview.svg',HERE/'cse-overview.png','original_explanatory_illustration'),
             (HERE/'connected-overview.svg',HERE/'connected-context.png','simplified_model_derived_presentation')]
    items=[];staged=[]
    with tempfile.TemporaryDirectory(dir=scratch,prefix='readme-render-') as name:
        owned=Path(name);env=dict(environment,TMPDIR=name,TMP=name,TEMP=name)
        for source,output,kind in sources:
            svg=ET.parse(source).getroot();width,height=int(svg.attrib['width']),int(svg.attrib['height'])
            fresh=owned/output.name
            command=[str(args.browser),'--headless','--no-sandbox','--disable-gpu','--allow-file-access-from-files','--hide-scrollbars','--force-device-scale-factor=1','--virtual-time-budget=1000','--user-data-dir='+str(owned/(output.stem+'-profile')),'--window-size='+str(width)+','+str(height),'--screenshot='+str(fresh),source.resolve().as_uri()]
            result=subprocess.run(command,env=env,capture_output=True,text=True,timeout=60)
            if result.returncode or not fresh.is_file() or fresh.is_symlink():raise RuntimeError('Rasterization failed: '+result.stderr[-800:])
            data=fresh.read_bytes()
            png_metadata(data,output.name)
            if len(data)<24 or struct.unpack('>II',data[16:24])!=(width,height):raise ValueError('Rendered PNG dimensions do not match SVG: '+output.name)
            staged.append((fresh,output))
            items.append({'source':source.relative_to(ROOT).as_posix(),'source_sha256':digest(source),'png':output.relative_to(ROOT).as_posix(),'png_sha256':digest(fresh),'viewport':[width,height],'kind':kind})
        receipt={'version':1,'renderer':version,'renderer_sha256':digest(args.browser),'assets':items,
                 'raster_exporter':'assets/readme/render.py','raster_exporter_sha256':digest(Path(__file__)),
                 'illustration_generator':'assets/readme/build.py','illustration_generator_sha256':digest(HERE/'build.py'),
                 'native_view_ledger':'examples/configuration-review/connected/generated/view.json',
                 'native_view_ledger_sha256':digest(ROOT/'examples/configuration-review/connected/generated/view.json'),
                 'claim':'Actual browser rasterization and exact source/image bindings; native behavior and engineering acceptance are separate.'}
        saved=owned/'render-receipt.json';saved.write_text(json.dumps(receipt,indent=2)+'\n')
        # Do not touch previous published artifacts when either render or any
        # source/receipt validation fails. Each final replacement is atomic;
        # this local helper does not promise a cross-file filesystem transaction.
        for fresh,output in staged:fresh.replace(output)
        saved.replace(HERE/'render-receipt.json')
    print('Rendered '+str(len(items))+' README assets; source bindings saved.')

if __name__=='__main__':main()
