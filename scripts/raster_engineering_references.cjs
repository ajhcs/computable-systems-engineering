const fs=require('fs'), path=require('path'), crypto=require('crypto');
const {chromium}=require(process.env.CSE_PLAYWRIGHT||'playwright');
(async()=>{
 const dir=path.resolve(process.argv[2]||'examples/engineering-reference/rendered');
 const check=process.argv.includes('--check');
 const browser=await chromium.launch({headless:true,executablePath:process.env.CSE_CHROMIUM});
 const page=await browser.newPage({viewport:{width:1280,height:900},deviceScaleFactor:1});
 const results=[];
 for(const f of fs.readdirSync(dir).filter(x=>x.endsWith('.svg'))){
  await page.goto('file://'+path.join(dir,f));
  const bounds=await page.locator('text').evaluateAll(xs=>xs.map(e=>{const b=e.getBBox();return {text:e.textContent,x:b.x,y:b.y,w:b.width,h:b.height}}));
  const clipped=bounds.filter(b=>b.x<0||b.y<0||b.x+b.w>1280||b.y+b.h>900);
  if(clipped.length)throw Error('Clipped labels: '+JSON.stringify(clipped));
  const png=await page.screenshot(), target=path.join(dir,f.replace('.svg','.png'));
  if(check){if(!fs.existsSync(target)||!png.equals(fs.readFileSync(target)))throw Error('Stale PNG '+target);}
  else fs.writeFileSync(target,png);
  results.push({file:f,width:1280,height:900,text_labels:bounds.length,clipped,svg_sha256:crypto.createHash('sha256').update(fs.readFileSync(path.join(dir,f))).digest('hex'),png_sha256:crypto.createHash('sha256').update(png).digest('hex')});
 }
 await browser.close();
 if(!check)fs.writeFileSync(path.join(dir,'visual-checks.json'),JSON.stringify(results,null,2)+'\n');
 console.log(JSON.stringify(results));
})().catch(e=>{console.error(e.message);process.exit(1)});
