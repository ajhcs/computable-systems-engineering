const fs=require('fs');
const path=require('path');
const crypto=require('crypto');
const { chromium }=require(process.env.CSE_PLAYWRIGHT || 'playwright');
(async()=>{
 const root=path.resolve(__dirname,'..');
 const args=process.argv.slice(2);
 const checkOnly=args.includes('--check');
 const output=path.resolve(args.find(a=>a!=='--check') || root+'/examples/diagram-reference/rendered');
 const browser=await chromium.launch({headless:true,executablePath:process.env.CSE_CHROMIUM || chromium.executablePath()});
 const page=await browser.newPage({viewport:{width:1280,height:720},deviceScaleFactor:1});
 let findings=[];
 for(const name of fs.readdirSync(output).filter(n=>n.endsWith('.svg'))){
  await page.goto('file://'+path.join(output,name));
  const pngPath=path.join(output,name.replace('.svg','.png'));
  const raster=await page.screenshot();
  if(checkOnly){
   if(!fs.existsSync(pngPath) || !raster.equals(fs.readFileSync(pngPath))) throw Error('Stale PNG: '+pngPath);
  } else fs.writeFileSync(pngPath,raster);
  const labels=await page.locator('text').evaluateAll(elements=>elements.map(e=>{
    const b=e.getBBox(); return {cell:e.getAttribute('data-cell'),text:e.textContent,x:b.x,y:b.y,w:b.width,h:b.height};
  }));
  const errors=labels.filter(b=>b.x<0 || b.y<0 || b.x+b.w>1280 || b.y+b.h>720);
  if(errors.length) throw Error('Clipped text: '+JSON.stringify(errors));
  findings.push({file:name,width:1280,height:720,text_labels:labels.length,clipped:errors,svg_sha256:crypto.createHash('sha256').update(fs.readFileSync(path.join(output,name))).digest('hex'),png_sha256:crypto.createHash('sha256').update(raster).digest('hex')});
 }
 if(!checkOnly) fs.writeFileSync(path.join(output,'visual-checks.json'),JSON.stringify(findings,null,2)+'\n');
 await browser.close();
 console.log(JSON.stringify(findings));
})();