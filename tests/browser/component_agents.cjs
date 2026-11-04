const {chromium}=require(process.env.CSE_PLAYWRIGHT_MODULE || 'playwright');
const fs=require('fs'),path=require('path'),assert=require('assert');
const {pathToFileURL}=require('url');
const work=path.resolve(process.argv[2] || '.');
(async()=>{
 const browser=await chromium.launch({executablePath:process.env.CSE_BROWSER || undefined,headless:true,args:process.env.CSE_BROWSER_NO_SANDBOX==='1'?['--no-sandbox']:[]});
 const errors=[];const requests=[];const receipts=[];
 try{
  const ctx=await browser.newContext({viewport:{width:1100,height:800},acceptDownloads:true});
  const page=await ctx.newPage();page.on('pageerror',e=>errors.push(String(e)));page.on('request',r=>requests.push(r.url()));
  await page.addInitScript(()=>Object.defineProperty(navigator,'clipboard',{value:undefined,configurable:true}));
  await page.goto(pathToFileURL(path.join(work,'shortlist.html')).href);
  assert.equal(await page.getByRole('checkbox').count(),3);
  assert(await page.getByRole('button',{name:'Copy IDs',exact:true}).isDisabled());
  await page.keyboard.press('Tab');await page.keyboard.press('Space');
  assert.equal(await page.locator('#cse-selection-status').getAttribute('data-selected-ids'),'["mech-pulley-variant-a"]');
  await page.reload();assert(await page.getByRole('checkbox').first().isChecked());
  await page.getByRole('button',{name:'Copy IDs',exact:true}).click();
  assert(await page.getByLabel('Selected component IDs',{exact:true}).isVisible());
  assert.equal(await page.getByLabel('Selected component IDs',{exact:true}).inputValue(),'mech-pulley-variant-a');
  await page.getByRole('checkbox').nth(1).check();
  assert.equal(await page.getByLabel('Selected component IDs',{exact:true}).inputValue(),'mech-pulley-variant-a\nmech-pulley-variant-c');
  const downloaded=page.waitForEvent('download');await page.getByRole('button',{name:'Download selection',exact:true}).click();
  const file=await downloaded;await file.saveAs(path.join(work,'browser-selection.json'));
  const data=JSON.parse(fs.readFileSync(path.join(work,'browser-selection.json')));
  assert.deepEqual(data.component_ids,['mech-pulley-variant-a','mech-pulley-variant-c']);
  assert.equal(data.schema,'cse.component-selection/1');assert.equal(Object.keys(data).length,3);
  for(const [width,scale,dark] of [[1100,100,false],[390,100,false],[390,200,false],[390,100,true]]){
   await page.setViewportSize({width,height:900});await page.emulateMedia({colorScheme:dark?'dark':'light'});
   await page.evaluate(scale=>document.documentElement.style.fontSize=scale+'%',scale);
   const facts=await page.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth,
      images:[...document.images].map(i=>({alt:i.alt,loaded:i.complete&&i.naturalWidth>0})),
      buttons:[...document.querySelectorAll('button')].map(b=>({text:b.textContent,width:b.getBoundingClientRect().width,height:b.getBoundingClientRect().height})),
      selected:JSON.parse(document.getElementById('cse-selection-status').dataset.selectedIds)}));
   assert(facts.scroll<=facts.width);assert(facts.images.every(i=>i.alt&&i.loaded));assert(facts.buttons.every(b=>b.height>=44));
   receipts.push({width,scale,dark,...facts});
   await page.screenshot({path:path.join(work,`shortlist-${width}-${scale}-${dark?'dark':'light'}.png`),fullPage:true});
  }
  await page.evaluate(()=>location.hash=encodeURIComponent(JSON.stringify({revision:'old',ids:['mech-pulley-variant-a']})));
  await page.reload();assert((await page.getByRole('status').textContent()).includes('unavailable'));
  assert.equal(await page.locator('#cse-selection-status').getAttribute('data-selected-ids'),'[]');
  assert.equal(errors.length,0);assert(requests.every(url=>url.startsWith('file:')||url.startsWith('data:')));
  fs.writeFileSync(path.join(work,'browser-check.json'),JSON.stringify({status:'pass',checks:['keyboard selection','catalog-bound reload state','clipboard fallback','selection JSON download','stale state refusal','stable accessible selectors','desktop/narrow/200-percent/dark layouts','no external network'],errors,receipts},null,2)+'\n');
  console.log('PASS: keyboard, state, error, download and responsive checks; '+receipts.length+' layouts.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
