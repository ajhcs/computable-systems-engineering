const fs=require('fs'),path=require('path');const{chromium}=require(process.env.CSE_PLAYWRIGHT);
(async()=>{
 const root=path.resolve('examples/diagram-style-prototypes'),w=path.resolve('work/diagram-reference-expansion-20261002/style-review');const b=await chromium.launch({headless:true,executablePath:process.env.CSE_CHROMIUM});const p=await b.newPage({viewport:{width:1440,height:1100}});await p.goto('file://'+path.join(root,'review.html'));const checks=[];
 for(const view of ['01-tmt-maintenance','02-tmt-timing','03-ape-composition','04-ape-optical','05-tmt-exposure','06-tmt-sequence-order']){
  await p.selectOption('#view',view);const treatments=await p.locator('#treatment option:not([disabled])').evaluateAll(xs=>xs.map(x=>x.value));
  for(const t of treatments){await p.selectOption('#treatment',t);await p.locator('#diagram').evaluate(i=>i.decode());const row=await p.evaluate(()=>({view:document.querySelector('#view').value,treatment:document.querySelector('#treatment').value,diagram_width:document.querySelector('#diagram').naturalWidth,paths:[...document.querySelectorAll('a')].map(a=>a.href)}));if(row.diagram_width!==1280)throw Error(JSON.stringify(row));for(const link of row.paths)if(!fs.existsSync(new URL(link)))throw Error('Broken '+link);checks.push(row)}
 }
 fs.writeFileSync(path.join(root,'gallery-validation.json'),JSON.stringify(checks,null,2)+'\n');
 const labels=['Accepted baseline','Technical Ledger','Instrument Record','Quiet Precision','Research Folio','Engineering Standard'],dirs=[null,'technical-ledger','instrument-record','quiet-precision','research-folio','engineering-standard'];
 for(const stem of ['01-tmt-maintenance','02-tmt-timing','03-ape-composition','04-ape-optical']){
  const html='<html><head><style>body{margin:0;background:white;font:20px Arial;color:#172f45}h1{margin:16px}.row{display:flex}.tile{width:640px}h2{font-size:21px;margin:12px 24px}img{display:block;width:640px;height:450px}</style></head><body><h1>'+stem+' | matched baseline and five presentation hypotheses</h1><div class="row">'+dirs.map((d,i)=>'<div class="tile"><h2>'+labels[i]+'</h2><img src="file://'+path.resolve(d?path.join(root,d,stem+'.png'):path.join(root,'../engineering-reference/rendered',stem+'.png'))+'"></div>').join('')+'</div></body></html>';
  await p.setViewportSize({width:3840,height:570});await p.setContent(html);await p.locator('img').evaluateAll(xs=>Promise.all(xs.map(i=>i.decode())));await p.screenshot({path:path.join(w,stem+'-matched-comparison.png')});
 }
 await b.close();console.log(JSON.stringify({gallery_combinations:checks.length,comparison_posters:4}));
})().catch(e=>{console.error(e);process.exit(1)});
