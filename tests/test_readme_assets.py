"""Controlled browser failures cannot qualify stale README image exports."""
from contextlib import redirect_stdout
from hashlib import sha256
import importlib.util
import io
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zlib

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('cse_readme_renderer',ROOT/'assets/readme/render.py')
renderer=importlib.util.module_from_spec(spec);spec.loader.exec_module(renderer)

def chunk(kind,body):
    return struct.pack('>I',len(body))+kind+body+struct.pack('>I',zlib.crc32(kind+body)&0xffffffff)

def png(width=2,height=3,color=b'\x34\x78\x90'):
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,8,2,0,0,0))+chunk(b'IDAT',zlib.compress((b'\0'+color*width)*height))+chunk(b'IEND',b'')

class RendererFailureTests(unittest.TestCase):
    def setUp(self):
        (ROOT/'.tmp').mkdir(exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(dir=ROOT/'.tmp');self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.assets=self.root/'assets/readme';self.assets.mkdir(parents=True)
        self.browser=self.root/'controlled-browser';self.browser.write_text('Unit fixture only; not an actual rasterizer.\n')
        for name in ('cse-overview.svg','connected-overview.svg'):
            (self.assets/name).write_text('<svg xmlns="http://www.w3.org/2000/svg" width="2" height="3"><title>New source</title></svg>')
        (self.assets/'build.py').write_text('# Controlled illustration source\n')
        ledger=self.root/'examples/configuration-review/connected/generated/view.json';ledger.parent.mkdir(parents=True);ledger.write_text('{}\n')
        for name in ('cse-overview.png','connected-context.png'):(self.assets/name).write_bytes(png(color=b'\x11\x22\x33'))
        (self.assets/'render-receipt.json').write_text('Previous receipt; preserve on failure.\n')
        self.before={name:(self.assets/name).read_bytes() for name in ('cse-overview.png','connected-context.png','render-receipt.json')}
        self.calls=[]

    def execute(self,behavior):
        def run(command,**options):
            if '--version' in command:return subprocess.CompletedProcess(command,0,'Controlled browser fixture\n','')
            output=Path(next(arg.split('=',1)[1] for arg in command if arg.startswith('--screenshot=')))
            self.calls.append(output)
            return behavior(command,output,len(self.calls))
        with patch.object(renderer,'ROOT',self.root),patch.object(renderer,'HERE',self.assets),patch.object(renderer.subprocess,'run',side_effect=run),patch.object(sys,'argv',['render.py','--browser',str(self.browser)]),redirect_stdout(io.StringIO()):
            renderer.main()

    def unchanged(self):
        self.assertEqual({name:(self.assets/name).read_bytes() for name in self.before},self.before)

    def test_zero_exit_without_new_image_refuses_existing_png_and_receipt(self):
        with self.assertRaises(RuntimeError):
            self.execute(lambda command,output,index:subprocess.CompletedProcess(command,0,'',''))
        self.unchanged()
        self.assertNotEqual(self.calls[0],self.assets/'cse-overview.png')

    def test_invalid_or_wrong_sized_fresh_png_refuses_and_preserves_outputs(self):
        for data in (b'not a PNG',png(width=1,height=1)):
            with self.subTest(data=data[:12]):
                self.calls=[]
                def capture(command,output,index):
                    output.write_bytes(data);return subprocess.CompletedProcess(command,0,'','')
                with self.assertRaises(ValueError):self.execute(capture)
                self.unchanged()

    def test_second_capture_failure_preserves_both_old_images_and_receipt(self):
        def capture(command,output,index):
            if index==1:
                output.write_bytes(png());return subprocess.CompletedProcess(command,0,'','')
            return subprocess.CompletedProcess(command,1,'','Controlled second-image failure')
        with self.assertRaises(RuntimeError):self.execute(capture)
        self.unchanged()

    def test_two_new_captures_publish_images_with_exact_source_bindings(self):
        def capture(command,output,index):
            self.assertFalse(output.exists(),'Each capture must use a fresh owned path')
            output.write_bytes(png());return subprocess.CompletedProcess(command,0,'','')
        self.execute(capture)
        receipt=json.loads((self.assets/'render-receipt.json').read_text())
        self.assertEqual(len(receipt['assets']),2)
        for item in receipt['assets']:
            source=self.root/item['source'];output=self.root/item['png']
            self.assertEqual(item['source_sha256'],sha256(source.read_bytes()).hexdigest())
            self.assertEqual(item['png_sha256'],sha256(output.read_bytes()).hexdigest())
            self.assertNotEqual(output.read_bytes(),self.before[output.name])

if __name__=='__main__':unittest.main()
