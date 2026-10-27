const fs=require('fs'),path=require('path'),crypto=require('crypto');const {chromium}=require(process.env.CSE_PLAYWRIGHT);
(async()=>{
 const root=path.resolve('examples/diagram-style-prototypes');
 const browser=await chromium.launch({headless:true,executablePath:process.env.CSE_CHROMIUM});
 const page=await browser.newPage({viewport:{width:1280,height:900},deviceScaleFactor:1});
 const rows=[];
 for(const treatment of fs.readdirSync(root).filter(n=>fs.statSync(path.join(root,n)).isDirectory())){
  for(const filename of fs.readdirSync(path.join(root,treatment)).filter(n=>n.endsWith('.svg'))){
   const p=path.join(root,treatment,filename);await page.goto('file://'+p);await page.evaluate(()=>document.fonts.ready);
   const labels=await page.locator('text').evaluateAll(xs=>xs.map(e=>{const b=e.getBBox();return {text:e.textContent,x:b.x,y:b.y,w:b.width,h:b.height}}));
   const clipped=labels.filter(b=>b.x<0||b.y<0||b.x+b.w>1280||b.y+b.h>900);
   if(clipped.length)throw Error('Clipped '+p+': '+JSON.stringify(clipped));
   const screenshot=await page.screenshot();fs.writeFileSync(p.replace('.svg','.png'),screenshot);
   rows.push({treatment,file:filename,width:1280,height:900,clipped,png_sha256:crypto.createHash('sha256').update(screenshot).digest('hex'),labels:labels.length});
  }
 }
 await browser.close();fs.writeFileSync(path.join(root,'actual-render-validation.json'),JSON.stringify(rows,null,2)+'\n');console.log(JSON.stringify({rendered:rows.length,clipped:0}));
})().catch(e=>{console.error(e.message);process.exit(1)});
