#!/usr/bin/env python3
"""Optional actual-browser PNGs and geometry inspection; uses installed tools only."""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import shutil
import tempfile


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


SCRIPT = r'''
const fs = require('fs');
const {chromium} = require(process.env.SHOWCASE_PLAYWRIGHT);
(async()=>{
 const output=process.env.SHOWCASE_OUTPUT;
 const manifest=JSON.parse(fs.readFileSync(output+'/build-manifest.json','utf8'));
 const context=await chromium.launchPersistentContext(process.env.SHOWCASE_PROFILE,{executablePath:process.env.SHOWCASE_BROWSER,headless:true,viewport:{width:800,height:900},deviceScaleFactor:1,args:['--no-sandbox','--allow-file-access-from-files']});
 const page=await context.newPage();
 const receipt={viewport_width:800,device_scale_factor:1,views:[],errors:[]};
 page.on('pageerror',e=>receipt.errors.push(String(e)));
 for(const id of manifest.views){
  const svg=fs.readFileSync(output+'/'+id+'.svg','utf8');
  const height=Number(svg.match(/height="([0-9]+)"/)[1]);
  await page.setViewportSize({width:800,height});
  await page.setContent('<!doctype html><html><meta charset="utf-8"><style>html,body{margin:0;padding:0}svg{display:block}</style>'+svg+'</html>',{waitUntil:'load'});
  await page.evaluate(()=>document.fonts.ready);
  const inspected=await page.evaluate(()=>{
   const svg=document.querySelector('svg'),view=svg.viewBox.baseVal;
   const failures=[];let count=0;const textBoxes=[];
   for(const text of svg.querySelectorAll('text')){
    count++; const b=text.getBBox();textBoxes.push({text:text.textContent,b});
    if(b.x<-.2||b.y<-.2||b.x+b.width>view.width+.2||b.y+b.height>view.height+.2)failures.push({kind:'canvas',text:text.textContent,bounds:{x:b.x,y:b.y,width:b.width,height:b.height}});
    const id=text.getAttribute('data-box');
    if(id){const box=svg.querySelector('#'+id).getBBox();if(b.x<box.x||b.y<box.y||b.x+b.width>box.x+box.width||b.y+b.height>box.y+box.height)failures.push({kind:'card',text:text.textContent,box:id});}
   }
   for(let i=0;i<textBoxes.length;i++)for(let j=i+1;j<textBoxes.length;j++){const a=textBoxes[i],b=textBoxes[j];const w=Math.min(a.b.x+a.b.width,b.b.x+b.b.width)-Math.max(a.b.x,b.b.x);const h=Math.min(a.b.y+a.b.height,b.b.y+b.b.height)-Math.max(a.b.y,b.b.y);if(w>1&&h>1)failures.push({kind:'text-overlap',a:a.text,b:b.text,width:w,height:h});}
   return {text_count:count,failures,width:view.width,height:view.height};
  });
  await page.screenshot({path:output+'/'+id+'.png',clip:{x:0,y:0,width:800,height},animations:'disabled',timeout:15000});
  await page.setViewportSize({width:390,height:844});
  await page.setContent('<!doctype html><html><meta name="viewport" content="width=device-width"><style>html,body{margin:0;padding:0}.scroll{width:390px;overflow:auto}svg{display:block;max-width:none}</style><div class="scroll">'+svg+'</div></html>');
  const narrow=await page.evaluate(()=>({viewport:innerWidth,document:document.documentElement.scrollWidth,scrollClient:document.querySelector('.scroll').clientWidth,scrollContent:document.querySelector('.scroll').scrollWidth,naturalWidth:document.querySelector('svg').getBoundingClientRect().width}));
  receipt.views.push({id,...inspected,narrow});
 }
 await page.setViewportSize({width:390,height:844});
 await page.goto('file://'+output+'/index.html',{waitUntil:'load'});
 receipt.gallery=await page.evaluate(()=>{
  const ids=[...document.querySelectorAll('[id]')].map(e=>e.id);
  const labels=[...document.querySelectorAll('svg')].map(svg=>{
   const refs=(svg.getAttribute('aria-labelledby')||'').split(/\s+/);
   const nodes=refs.map(id=>document.getElementById(id));
   return {refs,own:nodes.every(node=>node&&svg.contains(node)),name:nodes.map(node=>node?node.textContent:'').join(' ')};
  });
  return {viewport:innerWidth,document:document.documentElement.scrollWidth,frames:[...document.querySelectorAll('.diagram')].map(e=>({client:e.clientWidth,scroll:e.scrollWidth})),textAlternatives:document.querySelectorAll('details').length,duplicateIds:ids.filter((id,i)=>ids.indexOf(id)!==i),labels};
 });
 receipt.gallery.ariaSnapshots=[];
 for(const svg of await page.locator('svg').all())receipt.gallery.ariaSnapshots.push(await svg.ariaSnapshot());
 if(receipt.gallery.duplicateIds.length||receipt.gallery.labels.some(label=>!label.own)||new Set(receipt.gallery.ariaSnapshots).size!==manifest.views.length)receipt.errors.push('Combined gallery SVG identity or accessible-name collision');
 if(receipt.gallery.document!==390||receipt.gallery.textAlternatives!==manifest.views.length)receipt.errors.push('Narrow full-gallery overflow or missing text alternatives');
 await context.close();
 fs.writeFileSync(output+'/browser-inspection.json',JSON.stringify(receipt,null,2)+'\n');
 if(receipt.errors.length||receipt.views.some(v=>v.failures.length||v.narrow.document!==390||v.narrow.naturalWidth!==800))process.exit(1);
})().catch(e=>{console.error(e);process.exit(1)});
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--browser', type=Path, required=True)
    parser.add_argument('--playwright-module', type=Path, required=True)
    parser.add_argument('--library-path', type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    root = Path(__file__).resolve().parents[2]
    env = os.environ.copy()
    if args.library_path:
        env['LD_LIBRARY_PATH'] = str(args.library_path)
    with tempfile.TemporaryDirectory(prefix='showcase-browser-', dir=root/'.cache') as temporary:
        for name in ('TMPDIR','TMP','TEMP'):
            env[name] = temporary
        env.update(SHOWCASE_OUTPUT=str(output), SHOWCASE_BROWSER=str(args.browser), SHOWCASE_PLAYWRIGHT=str(args.playwright_module), SHOWCASE_PROFILE=temporary+'/profile')
        subprocess.run(['node','-e',SCRIPT],env=env,check=True,timeout=180)
    manifest = json.loads((output/'build-manifest.json').read_text())
    receipt = {'claim':'Actual pinned installed-browser rasterization and bounds/scroll checks; independent human review remains separate.', 'browser':str(args.browser),'browser_sha256':digest(args.browser),'node_executable':str(Path(shutil.which('node')).resolve()),'node_sha256':digest(Path(shutil.which('node')).resolve()),'playwright_package_sha256':digest(args.playwright_module/'package.json'),'playwright_module':str(args.playwright_module),'library_path':str(args.library_path) if args.library_path else None,'temporary_data':'Private workspace cache TMPDIR/TMP/TEMP and explicit browser profile; HOME/CODEX_HOME unchanged.','views':{v:{'svg_sha256':digest(output/(v+'.svg')),'png_sha256':digest(output/(v+'.png'))} for v in manifest['views']}}
    (output/'render-receipt.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    for p in output.iterdir():
        if p.suffix=='.png' or p.name in ('browser-inspection.json','render-receipt.json'):
            manifest['files'][p.name]=digest(p)
    (output/'build-manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print('PASS actual browser PNG rendering and all preview bounds/scroll checks')


if __name__=='__main__':
    main()
