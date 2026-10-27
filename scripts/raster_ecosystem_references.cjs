#!/usr/bin/env node
// Optional installed-browser qualification; no downloader, package install or implicit release.
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const root=path.resolve(__dirname,'../examples/ecosystem-diagram-reference');
const digest=b=>crypto.createHash('sha256').update(b).digest('hex');
(async()=>{
 const args=process.argv.slice(2);if(args.some(x=>x!=='--check'))throw new Error('Only --check is supported; curated PNGs are never overwritten.');
 if(!process.env.CSE_PLAYWRIGHT||!process.env.CSE_CHROMIUM||!process.env.CSE_EVIDENCE_DIR)throw new Error('Set CSE_PLAYWRIGHT, CSE_CHROMIUM and CSE_EVIDENCE_DIR to installed tools and an ignored workspace output directory.');
 const {chromium}=require(process.env.CSE_PLAYWRIGHT);const out=path.resolve(process.env.CSE_EVIDENCE_DIR);if(out===root||out.startsWith(root+path.sep)||fs.existsSync(out))throw new Error('Evidence directory must be new and outside the curated library.');fs.mkdirSync(out,{recursive:true});
 const browser=await chromium.launch({executablePath:process.env.CSE_CHROMIUM,headless:true,args:['--disable-dev-shm-usage']});
 try{
  const page=await browser.newPage({viewport:{width:1400,height:1000},deviceScaleFactor:1});const rows=[];
  for(const key of ['C-maintenance','D-smart-grid','E-ape-allocation']){
   await page.goto('file://'+path.join(root,'rendered',key+'.svg'));await page.evaluate(()=>document.fonts.ready);
   const png=await page.locator('svg').screenshot({path:path.join(out,key+'.png'),timeout:15000});
   const audit=await page.evaluate(()=>{
    const s=document.querySelector('svg'),v=s.viewBox.baseVal;const labels=[...s.querySelectorAll('text')].map(t=>{const b=t.getBBox();return {text:t.textContent,x:b.x,y:b.y,w:b.width,h:b.height};});
    const clipped=labels.filter(b=>b.x<0||b.y<0||b.x+b.w>v.width||b.y+b.h>v.height);const overlap=[];
    for(let i=0;i<labels.length;i++)for(let j=i+1;j<labels.length;j++){const a=labels[i],b=labels[j];if(a.x<b.x+b.w-.5&&b.x<a.x+a.w-.5&&a.y<b.y+b.h-.5&&b.y<a.y+a.h-.5)overlap.push([a.text,b.text]);}
    return {labels,clipped,overlap};
   });
   const view=JSON.parse(fs.readFileSync(path.join(root,'rendered',key+'.view.json')));const intersections=[];
   for(const edge of view.edges)for(const t of audit.labels)for(let i=1;i<edge.points.length;i++){
    const [x,y]=edge.points[i-1],[xx,yy]=edge.points[i],l=t.x+.2,r=t.x+t.w-.2,top=t.y+.2,b=t.y+t.h-.2;
    if((x===xx&&l<x&&x<r&&Math.max(Math.min(y,yy),top)<Math.min(Math.max(y,yy),b))||(y===yy&&top<y&&y<b&&Math.max(Math.min(x,xx),l)<Math.min(Math.max(x,xx),r)))intersections.push({edge:edge.id,text:t.text});
   }
   const cdp=await page.context().newCDPSession(page);await cdp.send('DOM.enable');await cdp.send('CSS.enable');const doc=await cdp.send('DOM.getDocument');const ids=await cdp.send('DOM.querySelectorAll',{nodeId:doc.root.nodeId,selector:'text'});const fonts=new Map();
   for(const nodeId of ids.nodeIds){const f=await cdp.send('CSS.getPlatformFontsForNode',{nodeId});for(const x of f.fonts)fonts.set(x.postScriptName,{postScriptName:x.postScriptName,isCustomFont:x.isCustomFont});}await cdp.detach();
   const same=digest(png)===digest(fs.readFileSync(path.join(root,'rendered',key+'.png')));
   const row={key,svg_sha256:digest(fs.readFileSync(path.join(root,'rendered',key+'.svg'))),png_sha256:digest(png),reviewed_png_equal:same,clipped:audit.clipped,text_overlaps:audit.overlap,edge_text_crossings:intersections,fonts:[...fonts.values()]};rows.push(row);
   if(!same||row.clipped.length||row.text_overlaps.length||intersections.length||row.fonts.some(f=>!f.isCustomFont))throw new Error(key+' browser/PNG check failed: '+JSON.stringify(row));
  }
  await page.goto('file://'+path.join(root,'gallery.html'));await page.evaluate(()=>document.fonts.ready);const links=await page.locator('a[href]').evaluateAll(a=>a.map(x=>x.getAttribute('href')));const broken=links.filter(a=>!a.startsWith('#')&&!a.startsWith('http')&&!fs.existsSync(path.resolve(root,a.split('#')[0])));
  const viewport=[];for(const width of [1400,390]){await page.setViewportSize({width,height:1000});const r=await page.evaluate(()=>({width:innerWidth,document_width:document.body.scrollWidth,sections:document.querySelectorAll('section').length,canvases:[...document.querySelectorAll('.canvas')].map(x=>({visible:x.clientWidth,scroll:x.scrollWidth}))}));viewport.push(r);await page.screenshot({path:path.join(out,'gallery-'+width+'.png')});if(r.document_width>width||r.sections!==3)throw new Error('Gallery viewport check failed');}
  if(broken.length)throw new Error('Unresolved gallery links: '+broken.join(', '));
  fs.writeFileSync(path.join(out,'browser.json'),JSON.stringify({status:'pass',browser:browser.version(),rows,viewport,broken_links:broken,limits:'Pixel and font qualification only; not a human comprehension or engineering acceptance result.'},null,2)+'\n');
  console.log(JSON.stringify({status:'pass',diagrams:rows.length,reviewed_pngs_equal:rows.every(x=>x.reviewed_png_equal),viewports:viewport.map(x=>x.width)}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e.message);process.exitCode=1;});
