'use strict';
// The embedded reader remains the exact saved native artifact. This controller
// submits existing typed project operations; it supplies no engineering verdict.
const byId=id=>document.getElementById(id), frame=byId('view');
const uiSession=crypto.randomUUID();
let state, csrf, selectedId, busy=false, dirty=false, pending=null, unknown=false, polling=false, ghost=null;
let formRevision, formCommit, restoredSelection, restoredNavigation, restoredInspection;
let editTargetId, draftGeneration=0, loadGeneration=0, gestureActive=false, frameReady=false, creationDraft=false;
let candidateSvg=null,candidateMode='readable';
const key=()=> 'cse-pending-save:'+state.projection.project_id;
const notice=text=>{byId('notice').textContent=text;};
const clone=value=>JSON.parse(JSON.stringify(value));
const editableInputs=['rename-name','multiplicity-lower','multiplicity-upper','box-x','box-y','box-width','box-height','restore-target','create-name','create-short','create-placement','create-x','create-y','create-width','create-height','create-points'];
function showCandidate(svg,mode='readable'){
  candidateSvg=svg;candidateMode=mode;
  byId('candidate-diagram').hidden=!svg;byId('candidate-navigation').hidden=!svg;
  if(!svg){byId('candidate-diagram').srcdoc='';return;}
  const parsed=new DOMParser().parseFromString(svg,'image/svg+xml').documentElement;
  const width=Number(parsed.getAttribute('width')),height=Number(parsed.getAttribute('height'));
  if(parsed.localName!=='svg'||!Number.isFinite(width)||!Number.isFinite(height)||width<=0||height<=0)throw Error('Invalid native candidate drawing');
  const scale=mode==='overview'?Math.min(1,byId('candidate-diagram').clientWidth/width,byId('candidate-diagram').clientHeight/height):1;
  byId('candidate-scale').textContent=mode==='overview'?'Overview · use readable size for labels':'Readable size · 100%';
  byId('candidate-diagram').srcdoc='<!doctype html><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{margin:0;font:16px "DejaVu Sans",sans-serif}svg{display:block;width:'+width*scale+'px;height:'+height*scale+'px}</style>'+svg;
}
byId('candidate-overview').addEventListener('click',()=>showCandidate(candidateSvg,'overview'));
byId('candidate-readable').addEventListener('click',()=>showCandidate(candidateSvg,'readable'));
window.addEventListener('resize',()=>{if(candidateSvg&&candidateMode==='overview')showCandidate(candidateSvg,'overview');});
function controls(){
  if(frameReady)frame.contentWindow.cseDiagramNavigation?.lock(gestureActive);
  const different=Boolean(editTargetId&&selectedId!==editTargetId);
  byId('edits').disabled=busy||gestureActive||unknown||Boolean(pending)||!selectedId||different;
  byId('multiplicity-fields').disabled=creationDraft||!state||editingNode()?.[1].kind!=='PartUsage';
  byId('create-definition-fields').disabled=!state||state.projection.mode!=='definitions'||editingNode()?.[1].kind!=='PartDefinition'||dirty&&!creationDraft;
  for(const id of ['rename-form','layout-form','restore-form'])for(const input of byId(id).querySelectorAll('input,button,select'))input.disabled=creationDraft;
  byId('create-coordinates').hidden=byId('create-placement').value!=='manual';
  byId('save').disabled=busy||!pending||Boolean(pending.stale);
  byId('save').textContent=unknown?'Retry save with the same request ID':'Save change';
  byId('discard').disabled=busy||unknown;
  byId('refresh').disabled=busy||gestureActive;
  byId('preview').hidden=!pending;
  if(!pending&&candidateSvg)showCandidate(null);
  if(pending)byId('pending-indicator').textContent=unknown?'Unacknowledged save · retain this exact request':pending.stale?'Stale candidate · current saved model is separate':'Unsaved change · saved model below remains authoritative';
  byId('return-target').hidden=!different;
  byId('edit-selected').hidden=!different;
  byId('edit-selected').disabled=busy||unknown||Boolean(pending);
  byId('discard-draft').hidden=!dirty||Boolean(pending);
  byId('discard-draft').disabled=busy||unknown;
}
async function api(path,body){
  const options={credentials:'same-origin',cache:'no-store'};
  if(body!==undefined)Object.assign(options,{method:'POST',headers:{'Content-Type':'application/json','X-CSE-CSRF':csrf||''},body:JSON.stringify(body)});
  const response=await fetch(path,options), result=await response.json();
  if(!response.ok){const error=new Error(result.error?.detail||'Request failed');error.code=result.error?.code;error.definitiveRefusal=result.error?.definitive_refusal===true;throw error;}
  return result;
}
function selectedNode(){return Object.entries(state.projection.nodes).find(([,node])=>node.element_id===selectedId);}
function editingNode(){return Object.entries(state.projection.nodes).find(([,node])=>node.element_id===editTargetId);}
function showFields(force=false){
  const found=selectedNode();
  if(!found)return;
  const [id,node]=found;
  byId('selected').textContent='Selected saved element: '+node.element+' · revision '+state.revision;
  if(force||!dirty&&!pending){
    editTargetId=selectedId;
    byId('rename-name').value=node.native.name;
    const quantity=node.native.multiplicity;
    for(const bound of ['lower','upper'])byId('multiplicity-'+bound).value=node.kind==='PartUsage'&&['default','literal'].includes(quantity?.status)?quantity[bound]:'';
    for(const field of ['x','y','width','height'])byId('box-'+field).value=state.layout.nodes[id][field];
    formRevision=state.revision;formCommit=state.commit;
    byId('create-name').value='';byId('create-short').value='';byId('create-placement').value='automatic';
    for(const field of ['x','y','width','height','points'])byId('create-'+field).value='';
  }
  const target=editingNode();
  byId('create-owner').textContent=target?'Native owner: '+target[1].element+' · captured revision '+formRevision:'';
  byId('multiplicity-saved').textContent=target?.[1].kind==='PartUsage'?'Saved multiplicity of '+target[1].element+': '+(target[1].native.source_multiplicity||'no local bounds')+' · '+target[1].native.multiplicity.status:'Part definitions have no usage multiplicity.';
  byId('edit-target').textContent=target?'Editing target: '+target[1].element+' · base revision '+formRevision:'The edit target is absent from this saved view.';
  controls();
}
function selectionChanged(){
  const inner=frame.contentWindow.cseSelectionContext;
  if(!inner)return;
  const next=inner.selected_element_ids[0];
  if(next!==selectedId)draftGeneration++;
  if(next!==selectedId&&(dirty||pending))notice('Inspection selection changed. The retained edit still targets its original element.');
  selectedId=next;
  globalThis.cseSelectionContext={...inner,ui_session_id:uiSession,scope:'local_connected_saved_selection'};
  showFields();
}
function removeGhost(){ghost?.remove();ghost=null;}
function drawGhost(id,box){
  removeGhost();
  const doc=frame.contentDocument, svg=doc.querySelector('svg');
  ghost=doc.createElementNS('http://www.w3.org/2000/svg','rect');
  for(const [name,value]of Object.entries({...box,fill:'none',stroke:'#777','stroke-width':3,'stroke-dasharray':'8 5','pointer-events':'none','data-role':'unsaved-layout-preview'}))ghost.setAttribute(name,String(value));
  svg.append(ghost);
}
function transformedLayout(id,box){
  const layout=clone(state.layout), old=layout.nodes[id];
  const map=point=>[box.x+(point[0]-old.x)/old.width*box.width,box.y+(point[1]-old.y)/old.height*box.height];
  for(const [edgeId,edge]of Object.entries(state.projection.edges)){
    const points=layout.edges[edgeId].points;
    if(points.length===2&&(edge.source===id||edge.target===id)){
      const a=edge.source===id?map(points[0]):points[0],b=edge.target===id?map(points[1]):points[1],mid=(a[0]+b[0])/2;
      layout.edges[edgeId].points=[a,[mid,a[1]],[mid,b[1]],b].filter((point,i,array)=>!i||point[0]!==array[i-1][0]||point[1]!==array[i-1][1]);
      continue;
    }
    for(const [at,adjacent]of [[0,1],[points.length-1,points.length-2]]){
      if((at===0?edge.source:edge.target)!==id)continue;
      const original=points[at],moved=map(original);
      if(original[0]===points[adjacent][0])points[adjacent][0]=moved[0];
      else if(original[1]===points[adjacent][1])points[adjacent][1]=moved[1];
      points[at]=moved;
    }
  }
  layout.nodes[id]=box;
  return layout;
}
function request(operation,fields){return{operation,request_id:crypto.randomUUID(),expected_revision:formRevision,...fields};}
async function previewChange(change,description,layoutBox){
  if(busy||unknown)return;
  draftGeneration++;
  busy=true;controls();notice('Checking the unsaved candidate…');
  try{
    const result=await api('/api/preview',change);
    const {candidate_svg,...metadata}=result.preview;
    pending={request:change,description,preview:metadata,stale:false};
    showCandidate(candidate_svg||null);
    const reviewLines=result.preview.configuration_reviews.map(review=>review.file+': '+review.report.status);
    byId('summary').textContent=description+'\nBase revision: '+result.preview.base_revision+'\nChanged model files: '+(result.preview.changed_model_files.join(', ')||'none')+'\nChanged companion files: '+(result.preview.changed_linked_records.join(', ')||'none')+(reviewLines.length?'\nRetained configuration reviews:\n'+reviewLines.join('\n'):'');
    byId('pending-indicator').textContent='Unsaved change · saved model below remains authoritative';
    if(layoutBox)drawGhost(layoutBox.id,layoutBox.box);
    notice('Candidate checked. Review it, then save or discard.');
    return{outcome:'previewed',request:clone(change),preview:clone(metadata)};
  }catch(error){removeGhost();pending=null;notice(error.code==='stale_revision'?'Conflict: '+error.message+'. Your form values remain available. Refresh before another preview.':error.message);return{outcome:'refused',error:{code:error.code||'preview_unavailable',detail:error.message}};}
  finally{busy=false;controls();}
}
function previewLayout(){
  const found=editingNode();if(!found)return;
  const box=Object.fromEntries(['x','y','width','height'].map(field=>[field,Number(byId('box-'+field).value)]));
  const [id,node]=found;
  return previewChange(request('set_layout',{layout:transformedLayout(id,box)}),'Layout of '+node.element+' → x '+box.x+', y '+box.y+', width '+box.width+', height '+box.height,{id,box});
}
function bindDragging(){
  const doc=frame.contentDocument, svg=doc.querySelector('svg');
  for(const group of doc.querySelectorAll('g[data-node-id]'))group.addEventListener('pointerdown',event=>{
    if(event.button!==0||busy||pending||unknown||dirty||gestureActive)return;
    if(frame.contentWindow.cseDiagramNavigation.state().mode==='overview')return;
    group.dispatchEvent(new MouseEvent('click',{bubbles:true}));
    selectionChanged();
    gestureActive=true;draftGeneration++;controls();
    const id=group.dataset.nodeId,box=clone(state.layout.nodes[id]),mode=byId('drag-action').value;
    const at=e=>{const point=svg.createSVGPoint();point.x=e.clientX;point.y=e.clientY;return point.matrixTransform(svg.getScreenCTM().inverse());};
    const start=at(event);let changed=false,next=box;
    group.setPointerCapture(event.pointerId);
    function move(e){const p=at(e),dx=Math.round(p.x-start.x),dy=Math.round(p.y-start.y);changed=dx!==0||dy!==0;next=mode==='move'?{...box,x:box.x+dx,y:box.y+dy}:{...box,width:Math.max(1,box.width+dx),height:Math.max(1,box.height+dy)};if(changed)drawGhost(id,next);}
    function detach(){group.removeEventListener('pointermove',move);group.removeEventListener('pointerup',end);group.removeEventListener('pointercancel',cancel);group.removeEventListener('lostpointercapture',cancel);doc.removeEventListener('keydown',escape);gestureActive=false;draftGeneration++;}
    function end(e){detach();if(group.hasPointerCapture(e.pointerId))group.releasePointerCapture(e.pointerId);if(changed){dirty=true;for(const field of ['x','y','width','height'])byId('box-'+field).value=next[field];previewLayout();}else controls();}
    function cancel(){detach();if(group.hasPointerCapture(event.pointerId))group.releasePointerCapture(event.pointerId);removeGhost();controls();}
    function escape(e){if(e.key==='Escape'){e.preventDefault();cancel();}}
    group.addEventListener('pointermove',move);group.addEventListener('pointerup',end);group.addEventListener('pointercancel',cancel);group.addEventListener('lostpointercapture',cancel);doc.addEventListener('keydown',escape);
    event.preventDefault();
  });
}
frame.addEventListener('load',()=>{
  const doc=frame.contentDocument;if(!doc.querySelector('#cse-data'))return;
  for(const link of doc.querySelectorAll('a')){link.href=new URL(link.getAttribute('href'),location.origin).href+'?commit='+state.commit;link.target='_blank';link.rel='noopener';}
  doc.addEventListener('click',selectionChanged);doc.addEventListener('keyup',selectionChanged);
  doc.addEventListener('cse-navigation-change',()=>{if(frameReady)selectionChanged();});
  const wanted=restoredSelection&&Object.entries(state.projection.nodes).find(([,node])=>node.element_id===restoredSelection);
  if(wanted){const element=doc.querySelector('g[data-node-id="'+wanted[0]+'"]');element?.dispatchEvent(new MouseEvent('click',{bubbles:true}));}
  const navigation=frame.contentWindow.cseDiagramNavigation;
  if(restoredNavigation)navigation.restore(restoredNavigation);
  if(restoredNavigation?.mode!=='overview'&&wanted&&(!restoredNavigation||restoredSelection!==restoredInspection))navigation.reveal(wanted[0]);
  restoredNavigation=null;
  restoredSelection=null;selectionChanged();bindDragging();frameReady=true;
});
async function loadState(preserve=false,background=false){
  const generation=draftGeneration,ticket=++loadGeneration;
  const result=await api('/api/state');
  if(ticket!==loadGeneration||background&&(busy||gestureActive||dirty||pending||generation!==draftGeneration))return false;
  restoredNavigation=frameReady?frame.contentWindow.cseDiagramNavigation.state():null;
  restoredInspection=selectedId;
  state=result.state;csrf=result.csrf;restoredSelection=selectedId;
  byId('saved').textContent='Saved revision '+state.revision+' · '+state.projection.id+' · '+state.commit.slice(0,12);
  const restoreTarget=preserve?byId('restore-target').value:null;
  byId('restore-target').replaceChildren(...state.history.map(row=>{const option=document.createElement('option');option.value=row.revision;option.textContent='Revision '+row.revision+' · '+row.operation;return option;}));
  if(restoreTarget!==null)byId('restore-target').value=restoreTarget;
  if(!preserve){dirty=false;creationDraft=false;pending=null;removeGhost();formRevision=state.revision;formCommit=state.commit;}
  frameReady=false;frame.srcdoc=result.view_html;
  controls();
  return true;
}
function previewRename(){const found=editingNode();if(found)return previewChange(request('rename',{element_id:editTargetId,new_name:byId('rename-name').value}),'Rename '+found[1].element+' → '+byId('rename-name').value);}
function previewCreateDefinition(){
  const found=editingNode();if(!found)return;
  creationDraft=true;
  let placement=null;
  if(byId('create-placement').value==='manual'){
    const fields=['x','y','width','height'],box=Object.fromEntries(fields.map(key=>[key,Number(byId('create-'+key).value)]));
    const lines=byId('create-points').value.split(/\r?\n/),points=lines.map(line=>line.split(',').map(value=>value.trim()===''?NaN:Number(value)));
    if(fields.some(key=>byId('create-'+key).value==='')||!Object.values(box).every(Number.isFinite)||points.length<2||points.length>128||points.some(p=>p.length!==2||!p.every(Number.isFinite))){notice('Supply frame coordinates and two to 128 finite x,y route points.');return{outcome:'refused',error:{code:'input',detail:'Invalid creation placement'}};}
    placement={box,points};
  }
  return previewChange(request('create_definition',{owner_id:editTargetId,element_id:crypto.randomUUID(),new_name:byId('create-name').value,short_id:byId('create-short').value===''?null:byId('create-short').value,view_id:state.projection.id,placement}),'Create owned part definition '+byId('create-name').value+' under '+found[1].element);
}
function previewMultiplicity(){
  const found=editingNode();
  if(!found||found[1].kind!=='PartUsage')return{outcome:'refused',error:{code:'element_kind',detail:'Multiplicity belongs to a part usage.'}};
  const raw=['lower','upper'].map(field=>byId('multiplicity-'+field).value),[lower,upper]=raw.map(Number);
  if(raw.some(value=>!value.trim())||!Number.isInteger(lower)||!Number.isInteger(upper)||lower<0||upper<lower||upper>2147483647){
    const detail='Supply both integer bounds: 0 ≤ lower ≤ upper ≤ 2147483647.';notice(detail);return{outcome:'refused',error:{code:'multiplicity',detail}};
  }
  return previewChange(request('set_multiplicity',{element_id:editTargetId,lower,upper}),'Multiplicity of '+found[1].element+' → ['+lower+(lower===upper?'':'..'+upper)+']');
}
function previewRestore(){return previewChange(request('restore',{target_revision:Number(byId('restore-target').value)}),'Restore all source, identity and presentation state from revision '+byId('restore-target').value+' into a new revision.');}
byId('rename-form').addEventListener('submit',event=>{event.preventDefault();previewRename();});
byId('create-definition-form').addEventListener('submit',event=>{event.preventDefault();previewCreateDefinition();});
byId('multiplicity-form').addEventListener('submit',event=>{event.preventDefault();previewMultiplicity();});
byId('layout-form').addEventListener('submit',event=>{event.preventDefault();previewLayout();});
byId('restore-form').addEventListener('submit',event=>{event.preventDefault();previewRestore();});
byId('edits').addEventListener('input',event=>{if(event.target.id==='drag-action')return;if(event.target.closest('#create-definition-form'))creationDraft=true;draftGeneration++;dirty=true;if(pending&&!unknown){pending=null;removeGhost();}controls();});
function discard(){if(unknown||busy)return;draftGeneration++;pending=null;dirty=false;creationDraft=false;removeGhost();showFields(true);notice('Pending values discarded. Saved state is unchanged.');controls();}
byId('discard').addEventListener('click',discard);
byId('discard-draft').addEventListener('click',discard);
byId('edit-selected').addEventListener('click',discard);
byId('return-target').addEventListener('click',()=>{const found=editingNode();if(!found)return;const group=frame.contentDocument.querySelector('g[data-node-id="'+found[0]+'"]');group?.dispatchEvent(new MouseEvent('click',{bubbles:true}));group?.scrollIntoView({block:'nearest',inline:'nearest'});});
async function refreshSaved(){
  if(busy||gestureActive)return{outcome:'refused',error:{code:'interaction_busy',detail:'Finish the current interaction first.'}};
  draftGeneration++;busy=true;controls();
  try{const keepValues=dirty||Boolean(pending),target=editTargetId;await loadState(true);if(!unknown){pending=null;dirty=keepValues;formRevision=state.revision;formCommit=state.commit;if(keepValues)restoredSelection=target;else showFields(true);}notice(unknown?'Saved state refreshed. Retry the pending save to recover its durable receipt.':'Saved state refreshed. Form values retain their original target; review it, then preview against revision '+state.revision+'.');return{outcome:'refreshed',revision:state.revision,commit:state.commit};}
  catch(error){notice(error.message);return{outcome:'refused',error:{code:error.code||'refresh_unavailable',detail:error.message}};}
  finally{busy=false;controls();}
}
byId('refresh').addEventListener('click',refreshSaved);
async function saveChange(){
  if(!pending||busy||gestureActive||pending.stale)return{outcome:'refused',error:{code:'save_unavailable',detail:'Inspect and preview a current change before saving.'}};
  draftGeneration++;
  busy=true;controls();notice('Saving the checked request…');
  const savedRequest=pending.request;
  let acknowledged=null;
  try{
    sessionStorage.setItem(key(),JSON.stringify({request:savedRequest,selectedId,editTargetId,description:pending.description,
      baseCommit:formCommit,fields:Object.fromEntries(editableInputs.map(id=>[id,byId(id).value]))}));
    const result=await api('/api/apply',savedRequest);
    acknowledged=result.receipt;
    sessionStorage.removeItem(key());unknown=false;pending=null;dirty=false;creationDraft=false;removeGhost();
    if(savedRequest.operation==='create_definition')selectedId=savedRequest.element_id;
    await loadState();
    notice('Saved revision '+result.receipt.revision+'. Request '+result.receipt.request_id+'.'+(state.revision!==result.receipt.revision?' The current project is now at revision '+state.revision+'.':''));
    return{outcome:'committed',receipt:clone(acknowledged)};
  }catch(error){
    if(acknowledged){notice('Saved revision '+acknowledged.revision+'. Refresh is unavailable: '+error.message);return{outcome:'committed',receipt:clone(acknowledged),refresh_error:{code:error.code||'refresh_unavailable',detail:error.message}};}
    else if(error.definitiveRefusal){sessionStorage.removeItem(key());unknown=false;if(pending)pending.stale=error.code==='stale_revision';notice((error.code==='stale_revision'?'Conflict: ':'Save refused: ')+error.message+' Pending values are retained.');return{outcome:'refused',error:{code:error.code,detail:error.message},request:clone(savedRequest)};}
    else{unknown=true;notice('Save acknowledgement was not received. Retry with the same request ID to recover its outcome.');return{outcome:'unconfirmed',request:clone(savedRequest),error:{code:'outcome_unknown',detail:'Retry this exact request or look up its durable receipt.'}};}
  }finally{busy=false;controls();}
}
byId('save').addEventListener('click',saveChange);
async function start(){
  try{
    const access=new URLSearchParams(location.hash.slice(1)).get('access');
    if(access){await api('/session',{access});history.replaceState(null,'',location.pathname);}
    await loadState();
    const saved=sessionStorage.getItem(key());
    if(saved){
      const entry=JSON.parse(saved);pending={request:entry.request,description:entry.description,stale:false};
      selectedId=entry.selectedId;editTargetId=entry.editTargetId||entry.request.owner_id||entry.request.element_id||entry.selectedId;restoredSelection=selectedId;
      formRevision=entry.request.expected_revision;formCommit=entry.baseCommit||null;
      for(const id of editableInputs)if(typeof entry.fields?.[id]==='string')byId(id).value=entry.fields[id];
      // Older retained intents still expose the exact typed requested values.
      if(!entry.fields&&entry.request.operation==='set_multiplicity')for(const bound of ['lower','upper'])byId('multiplicity-'+bound).value=entry.request[bound];
      if(!entry.fields&&entry.request.operation==='rename')byId('rename-name').value=entry.request.new_name;
      unknown=true;byId('pending-indicator').textContent='Unacknowledged save';
      creationDraft=entry.request.operation==='create_definition';
      byId('summary').textContent=(entry.description||entry.request.operation)+'\nRequest '+entry.request.request_id+' · expected revision '+entry.request.expected_revision;
      notice('A previous save needs acknowledgement. Retry the exact request to recover its receipt.');controls();
    }
    else notice('Select a saved element to inspect or edit.');
  }catch(error){notice(error.message);}
}
setInterval(async()=>{
  if(!state||busy||gestureActive||polling)return;polling=true;
  try{const head=await api('/api/head');if(head.commit!==state.commit){if(busy||gestureActive||dirty||pending)notice('The project changed elsewhere. Your pending values are retained; refresh and review before another preview.');else await loadState(false,true);}}
  catch(error){notice('Refresh unavailable: '+error.message);}
  finally{polling=false;}
},1500);
start();
