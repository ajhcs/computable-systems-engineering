#!/usr/bin/env node
/* Local HTML/SVG export with selected fonts, native asset reuse and actual-glyph evidence. */
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const crypto = require('node:crypto');
const { spawnSync } = require('node:child_process');
const RUNTIME = path.resolve(__dirname, '..');
const sha256 = value => crypto.createHash('sha256').update(value).digest('hex');
const json = value => JSON.stringify(value, null, 2) + '\n';
const MIME = {'.html':'text/html; charset=utf-8','.svg':'image/svg+xml','.woff':'font/woff','.woff2':'font/woff2',
  '.ttf':'font/ttf','.otf':'font/otf','.png':'image/png','.jpg':'image/jpeg','.jpeg':'image/jpeg','.webp':'image/webp','.gif':'image/gif','.css':'text/css'};

function argumentsFor(argv) {
  const args = {mode: argv.shift(), svg: []};
  while (argv.length) {
    const name = argv.shift();
    if (!['--root','--profile','--html','--output-dir','--svg','--python','--page-selector'].includes(name) || !argv.length)
      throw new Error('Use preflight|render --root PROJECT --profile FILE [--html FILE --output-dir NEW --svg FILE --python PYTHON --page-selector .page]');
    const value = argv.shift();
    if (name === '--svg') args.svg.push(value); else args[name.slice(2)] = value;
  }
  if (!['preflight','render'].includes(args.mode) || !args.root || !args.profile) throw new Error('Mode, --root and --profile are required');
  if (args.mode === 'render' && (!args.html || !args['output-dir'])) throw new Error('Rendering requires --html and a new --output-dir');
  args.root = fs.realpathSync(path.resolve(args.root));
  args.profile = path.resolve(args.root, args.profile);
  args.python = args.python || process.env.CSE_PYTHON || 'python3';
  return args;
}

function preflight(args) {
  const run = spawnSync(args.python, [path.join(RUNTIME,'scripts/visual_profile.py'),'preflight',
    '--root',args.root,'--profile',args.profile,'--runtime',RUNTIME], {encoding:'utf8',timeout:30000});
  let profile;
  try { profile = JSON.parse(run.stdout); } catch (_) { throw new Error('Profile preflight did not return JSON: ' + (run.stderr || run.error || '')); }
  let playwright, tooling;
  try {
    if(Number(process.versions.node.split('.')[0])<20)throw new Error('Use an existing Node 20+ runtime for Playwright; current Node '+process.versions.node+' is unsupported.');
    playwright = require(processEnvModule());
    const executable = processEnvBrowser(playwright);
    const pdf = spawnSync(args.python,['-c','try:\n import pymupdf\nexcept ImportError:\n import fitz'],{encoding:'utf8',timeout:15000});
    tooling = {status: fs.existsSync(executable) && pdf.status === 0 ? 'pass' : 'unsupported',
      playwright_available: true, chromium_path: executable, chromium_present:fs.existsSync(executable),
      pdf_inspector_available: pdf.status === 0, python:args.python,
      limits:'Availability does not establish browser launch permission. No tools are installed and execution permissions are unchanged.'};
  } catch (error) { tooling = {status:'unsupported',findings:[String(error.message)]}; }
  return {schema:'cse.document-environment/1',status:profile.status === 'pass' && tooling.status === 'pass'?'pass':profile.status==='pass'?'unsupported':profile.status,
    profile_preflight:profile, tooling, playwright};
}
function processEnvModule() { return process.env.CSE_NODE_MODULES ? path.join(process.env.CSE_NODE_MODULES,'playwright') : 'playwright'; }
function processEnvBrowser(playwright) { return process.env.CSE_CHROMIUM || playwright.chromium.executablePath(); }
function dataURI(file) { const type=MIME[path.extname(file).toLowerCase()]; if(!type)throw new Error('Unsupported asset format: '+file); return 'data:'+type+';base64,'+fs.readFileSync(file).toString('base64'); }
function newOutputPath(root, requested) {
  const proposed=path.resolve(root,requested);
  let ancestor=proposed, missing=[];
  while(!fs.existsSync(ancestor)) {missing.unshift(path.basename(ancestor));ancestor=path.dirname(ancestor);}
  const resolved=path.join(fs.realpathSync(ancestor),...missing);
  if(!resolved.startsWith(root+path.sep)||resolved===RUNTIME||resolved.startsWith(RUNTIME+path.sep))throw new Error('Output must be inside the selected project and outside the plugin runtime');
  if(fs.existsSync(resolved))throw new Error('Output directory exists; choose a fresh path to preserve prior work');
  return resolved;
}
function cssString(value) { return JSON.stringify(value); }
function profileCSS(preflight) {
  const profile=preflight.profile;
  let css=preflight.fonts.map(f=>`@font-face{font-family:${cssString(f.family)};src:url(${cssString(dataURI(f.resolved_path))});font-weight:${f.weight};font-style:${f.style||'normal'};font-display:block}`).join('\n');
  css += '\n:root{'+Object.entries(profile.palette||{}).map(([k,v])=>`--cse-${k}:${v}`).join(';')+'}\n';
  for(const role of Object.values(profile.typography)) {
    const font=preflight.fonts.find(f=>f.id===role.font);
    css+=`${role.selectors.join(',')}{font-family:${cssString(font.family)};font-weight:${font.weight};font-style:${font.style||'normal'};font-size:${role.size_pt}pt}\n`;
  }
  for(const key of ['figure','table']) {
    const style=profile[key]; if(!style)continue;
    const values=[];
    if(style.rule_color)values.push(`border-color:var(--cse-${style.rule_color})`);
    if(style.rule_width_pt!==undefined)values.push(`border-width:${style.rule_width_pt}pt`,'border-style:solid');
    if(style.padding_pt!==undefined)values.push(`padding:${style.padding_pt}pt`);
    css+=`${style.selectors.join(',')}{${values.join(';')}}\n`;
  }
  return css;
}

async function prepare(page, source, preflight, css) {
  return page.evaluate(({source,profile,assets,css})=>{
    const isSvg=source.trim().replace(/^<\?xml[^>]*>\s*/,'').startsWith('<svg');
    const doc=new DOMParser().parseFromString(source,isSvg?'image/svg+xml':'text/html');
    if(doc.querySelector('parsererror'))throw new Error('Malformed source XML');
    if(doc.querySelector('script,iframe,object,embed')||[...doc.querySelectorAll('*')].some(el=>[...el.attributes].some(a=>/^on/i.test(a.name))))throw new Error('Executable/embedded documents are outside this static export helper');
    const style=doc.createElementNS(isSvg?'http://www.w3.org/2000/svg':'http://www.w3.org/1999/xhtml','style');
    style.setAttribute('data-cse-profile','');style.textContent=css;
    (isSvg?doc.documentElement:doc.head).append(style);
    const geometry=root=>[...root.querySelectorAll('path,rect,circle,ellipse,line,polyline,polygon')].map(el=>({
      tag:el.localName,geometry:[...el.attributes].filter(a=>['d','x','y','x1','x2','y1','y2','width','height','cx','cy','r','rx','ry','points','transform'].includes(a.name)).map(a=>[a.name,a.value]).sort()}));
    const records=[];
    for(const asset of assets) {
      const targets=[...doc.querySelectorAll('[data-cse-asset]')].filter(el=>el.getAttribute('data-cse-asset')===asset.id);
      for(let index=0;index<targets.length;index++) {
        const target=targets[index];
        if(asset.kind==='svg') {
          const master=new DOMParser().parseFromString(asset.content,'image/svg+xml');
          if(master.querySelector('parsererror,script,foreignObject'))throw new Error('Unsupported SVG master: '+asset.id);
          if(asset.role==='formal-symbol'&&master.querySelector('image'))throw new Error('Formal SVG master contains raster images: '+asset.id);
          const before=geometry(master.documentElement), imported=doc.importNode(master.documentElement,true);
          const prefix=`cse-${asset.id}-${index}-`, ids=new Map();
          for(const el of [imported,...imported.querySelectorAll('[id]')])if(el.id){ids.set(el.id,prefix+el.id);el.id=prefix+el.id;}
          for(const el of [imported,...imported.querySelectorAll('*')])for(const attr of [...el.attributes]) {
            let value=attr.value;
            for(const [oldId,newId]of ids) {value=value.split('url(#'+oldId+')').join('url(#'+newId+')');if(value==='#'+oldId)value='#'+newId;}
            if(['aria-labelledby','aria-describedby'].includes(attr.name))value=value.split(/\s+/).map(id=>ids.get(id)||id).join(' ');
            if(value!==attr.value)el.setAttribute(attr.name,value);
          }
          for(const el of imported.querySelectorAll('style')) {
            if(/#[A-Za-z_][\w-]*\s*[,{]/.test(el.textContent))throw new Error('SVG CSS ID selectors need explicit adaptation before export: '+asset.id);
            for(const [oldId,newId]of ids)el.textContent=el.textContent.split('url(#'+oldId+')').join('url(#'+newId+')');
          }
          imported.setAttribute('data-cse-source',asset.id);
          target.replaceChildren(imported);
          records.push({id:asset.id,kind:asset.kind,role:asset.role,source_sha256:asset.sha256,
            geometry_preserved:before.length>0&&JSON.stringify(before)===JSON.stringify(geometry(imported)),primitive_count:before.length});
        }else{
          let img=target;
          if(target.localName!=='img'){img=doc.createElement('img');target.replaceChildren(img);}
          img.setAttribute('src',asset.content);img.setAttribute('data-cse-source',asset.id);
          records.push({id:asset.id,kind:asset.kind,role:asset.role,source_sha256:asset.sha256,geometry_preserved:null});
        }
      }
    }
    for(const el of doc.querySelectorAll('[data-cse-asset]'))if(!assets.some(a=>a.id===el.getAttribute('data-cse-asset')))
      throw new Error('Unknown asset placeholder: '+el.getAttribute('data-cse-asset'));
    return {content:(isSvg?'<?xml version="1.0" encoding="UTF-8"?>\n':'<!doctype html>\n')+new XMLSerializer().serializeToString(doc.documentElement),records,isSvg};
  },{source,profile:preflight.profile,assets:preflight.assets.map(a=>({...a,content:a.kind==='svg'?fs.readFileSync(a.resolved_path,'utf8'):dataURI(a.resolved_path)})),css});
}

async function probe(page, preflight, pageSelector) {
  await page.evaluate(async()=>{await document.fonts.ready;await Promise.all([...document.images].map(i=>i.decode().catch(()=>{})));});
  const layout=await page.evaluate(({profile,pageSelector})=>{
    const visible=el=>{const s=getComputedStyle(el),b=el.getBoundingClientRect();let opacity=1;for(let p=el;p;p=p.parentElement)opacity*=Number(getComputedStyle(p).opacity);return s.display!=='none'&&s.visibility!=='hidden'&&opacity>0&&b.width>0&&b.height>0;};
    const walker=document.createTreeWalker(document.documentElement,NodeFilter.SHOW_TEXT), elements=new Set();
    while(walker.nextNode()) {const p=walker.currentNode.parentElement;if(walker.currentNode.textContent.trim()&&p&&!p.closest('style,script,title,desc,metadata')&&visible(p))elements.add(p);}
    const pages=[...document.querySelectorAll(pageSelector)];
    const records=[];let index=0;
    for(const el of elements) {
      const key='p'+index++;el.setAttribute('data-cse-probe',key);
      const s=getComputedStyle(el),range=document.createRange();range.selectNodeContents(el);const b=range.getBoundingClientRect();
      const containingPage=el.closest(pageSelector), pb=containingPage?.getBoundingClientRect();
      const svg=el.closest('svg'),sb=svg?.getBoundingClientRect();
      const within=(r)=>!r||(b.left>=r.left-1&&b.top>=r.top-1&&b.right<=r.right+1&&b.bottom<=r.bottom+1);
      const roleMatches=Object.entries(profile.typography).filter(([,r])=>r.selectors.some(sel=>el.matches(sel)||!!el.closest(sel)));
      records.push({probe:key,tag:el.localName,text:el.textContent.trim(),family:s.fontFamily,weight:Number(s.fontWeight),
        size_px:parseFloat(s.fontSize),style:s.fontStyle,roles:roleMatches.map(([name])=>name),bounds:{x:b.x,y:b.y,width:b.width,height:b.height},
        within_page:within(pb),within_svg:within(sb)});
    }
    const bounded=el=>{
      const b=el.getBoundingClientRect();
      for(let parent=el.parentElement;parent;parent=parent.parentElement){
        const style=getComputedStyle(parent), clips=parent.matches(pageSelector)||parent.localName==='svg'||['hidden','clip','scroll','auto'].includes(style.overflow);
        if(clips){const p=parent.getBoundingClientRect();if(b.left<p.left-1||b.top<p.top-1||b.right>p.right+1||b.bottom>p.bottom+1)return false;}
      }
      return true;
    };
    const graphics=[...document.querySelectorAll('img[data-cse-source]')].map(el=>({id:el.getAttribute('data-cse-source'),loaded:el.complete&&el.naturalWidth>0,visible:visible(el),within_bounds:bounded(el),width:el.naturalWidth,height:el.naturalHeight}));
    const vectors=[...document.querySelectorAll('svg[data-cse-source]')].map(el=>({id:el.getAttribute('data-cse-source'),visible:visible(el),within_bounds:bounded(el)&&[...el.querySelectorAll('path,rect,circle,ellipse,line,polyline,polygon')].every(bounded)}));
    const unsupported=[...document.querySelectorAll('foreignObject,canvas,img:not([data-cse-source])')].map(el=>el.localName);
    return {records,graphics,vectors,page_count:pages.length,unsupported};
  },{profile:preflight.profile,pageSelector});
  const session=await page.context().newCDPSession(page);
  await session.send('DOM.enable');await session.send('CSS.enable');
  const {root}=await session.send('DOM.getDocument',{depth:-1});
  for(const item of layout.records) {
    const {nodeId}=await session.send('DOM.querySelector',{nodeId:root.nodeId,selector:`[data-cse-probe="${item.probe}"]`});
    item.fonts=(await session.send('CSS.getPlatformFontsForNode',{nodeId})).fonts.filter(f=>f.glyphCount>0);
    const families=item.family.split(',').map(v=>v.trim().replace(/^['"]|['"]$/g,''));
    item.selected_font_id=preflight.fonts.find(f=>families[0]===f.family&&f.weight===item.weight&&(f.style||'normal')===item.style)?.id;
    const expected=preflight.fonts.find(f=>f.id===item.selected_font_id);
    item.font_matches_selection=!!expected&&item.fonts.length>0&&item.fonts.every(f=>f.isCustomFont&&(expected.postscript_name?f.postScriptName===expected.postscript_name:f.familyName===expected.family));
  }
  await session.detach();
  return layout;
}

async function captureSvg(page, filename) {
  // Playwright's animation-stabilization injection can stall on script-disabled
  // standalone SVG documents. CDP captures the already checked loaded glyphs.
  const clip=await page.evaluate(()=>{const b=document.documentElement.getBoundingClientRect();return {x:b.x,y:b.y,width:b.width,height:b.height,scale:1};});
  if(clip.width<=0||clip.height<=0)throw new Error('Standalone SVG has no visible capture bounds');
  const session=await page.context().newCDPSession(page);
  try {
    const {data}=await session.send('Page.captureScreenshot',{format:'png',captureBeyondViewport:true,clip});
    fs.writeFileSync(filename,Buffer.from(data,'base64'),{flag:'wx'});
  }finally{await session.detach();}
}

async function render(args, environment) {
  const output=newOutputPath(args.root,args['output-dir']);
  const inside=file=>{const real=fs.realpathSync(path.resolve(args.root,file));if(!real.startsWith(args.root+path.sep))throw new Error('Input must be inside project root');return real;};
  const html=inside(args.html), svgs=args.svg.map(inside);
  if(path.extname(html)!=='.html')throw new Error('Document source must be HTML');
  fs.mkdirSync(output,{recursive:true});
  const write=(name,value)=>fs.writeFileSync(path.join(output,name),typeof value==='string'?value:json(value),{flag:'wx'});
  const preflight=environment.profile_preflight;
  write('profile-preflight.json',preflight);
  const receipt={schema:'cse.document-render/1',status:'error',checks:{},profile_preflight:preflight,tooling:environment.tooling,
    inputs:[html,...svgs].map(file=>({path:file,sha256:sha256(fs.readFileSync(file))})).concat([{path:preflight.profile_path,sha256:preflight.profile_sha256}]),font_probes:[],assets:[],outputs:[],findings:[],
    claim_scope:'selected_font_and_asset_use_in_this_static_HTML_SVG_PDF_export; visual reading and engineering acceptance remain separate'};
  const requests=[],blocked=[],browserErrors=[];
  const server=http.createServer((req,res)=>{
    try {
      const requested=decodeURIComponent(new URL(req.url,'http://local').pathname);
      const file=path.resolve(output,'.'+requested);
      if(!file.startsWith(output+path.sep)){res.writeHead(403);return res.end();}
      res.writeHead(200,{'Content-Type':MIME[path.extname(file)]||'application/octet-stream'});res.end(fs.readFileSync(file));
    }catch(_){res.writeHead(404);res.end('Not found');}
  });
  let browser;
  // The relative temp path prevents Chromium's Unix socket path from exceeding
  // its short platform limit. Nothing is written to the plugin or system /tmp.
  const temporary=fs.mkdtempSync(path.join(output,'.browser-'));
  const oldCwd=process.cwd();
  const tempKeys=['TMPDIR','TMP','TEMP','XDG_CACHE_HOME','XDG_CONFIG_HOME','XDG_DATA_HOME'];
  const oldEnv=Object.fromEntries(tempKeys.map(k=>[k,process.env[k]]));
  const watchdog=setTimeout(()=>{receipt.findings.push('Browser export exceeded the 90-second bound.');if(browser)browser.close().catch(()=>{});},90000);
  try {
    process.chdir(output);
    const tmpRelative=path.basename(temporary);
    for(const key of tempKeys)process.env[key]=tmpRelative;
    browser=await environment.playwright.chromium.launch({headless:true,executablePath:environment.tooling.chromium_path,
      env:{...process.env,TMPDIR:tmpRelative,TMP:tmpRelative,TEMP:tmpRelative},timeout:30000});
    const context=await browser.newContext({viewport:{width:1200,height:1600},javaScriptEnabled:false});
    await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
    const origin='http://127.0.0.1:'+server.address().port;
    await context.route('**/*',route=>{
      const url=route.request().url();requests.push(url);
      if(url.startsWith(origin+'/')||url.startsWith('data:'))return route.continue();
      blocked.push(url);return route.abort();
    });
    const page=await context.newPage();
    page.on('pageerror',e=>browserErrors.push(String(e)));
    page.on('requestfailed',r=>browserErrors.push(r.url()+': '+r.failure()?.errorText));
    page.on('response',r=>{if(r.status()>=400)browserErrors.push(r.url()+': HTTP '+r.status());});
    const css=profileCSS(preflight), prepared=await prepare(page,fs.readFileSync(html,'utf8'),preflight,css);
    write('document.html',prepared.content);
    await page.goto(origin+'/document.html',{waitUntil:'networkidle'});await page.emulateMedia({media:'print'});
    const inspected=await probe(page,preflight,args['page-selector']||'.page');
    receipt.font_probes.push(...inspected.records.map(p=>({...p,artifact:'document.html'})));
    const assetRecords=[...prepared.records], graphics=[...inspected.graphics], vectors=[...inspected.vectors], layouts=[inspected];
    await page.screenshot({path:path.join(output,'document.png'),fullPage:true});
    await page.pdf({path:path.join(output,'document.pdf'),preferCSSPageSize:true,printBackground:true,displayHeaderFooter:false,tagged:true});
    for(let i=0;i<svgs.length;i++) {
      const preparedSvg=await prepare(page,fs.readFileSync(svgs[i],'utf8'),preflight,css);
      if(!preparedSvg.isSvg)throw new Error('Standalone SVG source must have an SVG root');
      const filename='figure-'+(i+1)+'.svg';write(filename,preparedSvg.content);
      await page.goto(origin+'/'+filename,{waitUntil:'networkidle'});
      const svgInspection=await probe(page,preflight,'svg');
      receipt.font_probes.push(...svgInspection.records.map(p=>({...p,artifact:filename})));
      assetRecords.push(...preparedSvg.records);graphics.push(...svgInspection.graphics);vectors.push(...svgInspection.vectors);layouts.push(svgInspection);
      await captureSvg(page,path.join(output,'figure-'+(i+1)+'.png'));
    }
    receipt.assets=preflight.assets.map(a=>({id:a.id,kind:a.kind,role:a.role,source_sha256:a.sha256,
      occurrences:assetRecords.filter(r=>r.id===a.id).length,
      geometry_preserved:a.kind==='svg'?assetRecords.filter(r=>r.id===a.id).every(r=>r.geometry_preserved):null,
      primitive_counts:assetRecords.filter(r=>r.id===a.id).map(r=>r.primitive_count),
      images:graphics.filter(g=>g.id===a.id),vectors:vectors.filter(g=>g.id===a.id)}));
    const usedFontIds=[...new Set(inspected.records.map(p=>p.selected_font_id).filter(Boolean))];
    const rasterAssets=receipt.assets.filter(a=>a.kind==='image'&&prepared.records.some(r=>r.id===a.id)).length;
    const formalAssets=receipt.assets.filter(a=>a.kind==='svg'&&a.role==='formal-symbol'&&prepared.records.some(r=>r.id===a.id)).length;
    const pdfArgs=[path.join(RUNTIME,'scripts/check_document_pdf.py'),'--pdf',path.join(output,'document.pdf'),
      '--profile-preflight',path.join(output,'profile-preflight.json'),'--output',path.join(output,'pdf-receipt.json'),
      '--font-ids',usedFontIds.join(','),'--raster-assets',String(rasterAssets),'--formal-assets',String(formalAssets)];
    if(inspected.page_count)pdfArgs.push('--expected-pages',String(inspected.page_count));
    const pdf=spawnSync(args.python,pdfArgs,{encoding:'utf8',timeout:30000});
    let pdfReceipt;
    try{pdfReceipt=JSON.parse(pdf.stdout);}catch(_){pdfReceipt={status:'error',findings:[pdf.stderr||String(pdf.error)]};}
    receipt.pdf=pdfReceipt;
    receipt.checks={actual_fonts_match:receipt.font_probes.length>0&&receipt.font_probes.every(p=>p.font_matches_selection),
      text_within_bounds:receipt.font_probes.every(p=>p.within_page&&p.within_svg),
      selected_assets_used:receipt.assets.every(a=>a.occurrences>0),
      svg_geometry_preserved:receipt.assets.filter(a=>a.kind==='svg').every(a=>a.geometry_preserved),
      selected_vectors_visible:receipt.assets.filter(a=>a.kind==='svg').every(a=>a.vectors.length>0&&a.vectors.every(i=>i.visible&&i.within_bounds)),
      selected_images_loaded:receipt.assets.filter(a=>a.kind==='image').every(a=>a.images.length>0&&a.images.every(i=>i.loaded&&i.visible&&i.within_bounds)),
      no_uninspected_content:layouts.every(l=>l.unsupported.length===0),
      no_external_requests:blocked.length===0,no_browser_errors:browserErrors.length===0,
      pdf_export_checked:pdf.status===0&&pdfReceipt.status==='pass',
      sources_unchanged:receipt.inputs.every(i=>sha256(fs.readFileSync(i.path))===i.sha256)&&
        [...preflight.fonts,...preflight.assets].every(a=>sha256(fs.readFileSync(a.resolved_path))===a.sha256)};
    receipt.status=Object.values(receipt.checks).every(Boolean)?'pass':'fail';
    receipt.browser_version=browser.version();receipt.requests=requests;receipt.blocked=blocked;receipt.browser_errors=browserErrors;
    receipt.outputs=fs.readdirSync(output).filter(n=>fs.statSync(path.join(output,n)).isFile()).map(n=>({path:n,sha256:sha256(fs.readFileSync(path.join(output,n)))}));
  }catch(error){receipt.findings.push(String(error.stack||error));}
  finally {
    clearTimeout(watchdog);
    if(browser)await browser.close();if(server.listening)await new Promise(resolve=>server.close(resolve));
    process.chdir(oldCwd);fs.rmSync(temporary,{recursive:true,force:true});
    for(const key of tempKeys)if(oldEnv[key]===undefined)delete process.env[key];else process.env[key]=oldEnv[key];
    write('render-receipt.json',receipt);
  }
  return receipt;
}

async function main(argv) {
  const args=argumentsFor(argv), environment=preflight(args);
  if(args.mode==='preflight'||environment.status!=='pass') {
    const {playwright,...report}=environment;console.log(json(report));return report.status==='pass'?0:1;
  }
  const report=await render(args,environment);
  console.log(json({schema:report.schema,status:report.status,checks:report.checks,receipt:path.resolve(args.root,args['output-dir'],'render-receipt.json'),findings:report.findings}));
  return report.status==='pass'?0:1;
}
if(require.main===module)main(process.argv.slice(2)).then(code=>{process.exitCode=code;}).catch(error=>{
  console.log(json({schema:'cse.document-render/1',status:'error',checks:{},findings:[String(error.message)]}));process.exitCode=1;
});
module.exports={argumentsFor,profileCSS,preflight,newOutputPath};
