'use strict';
// The embedded reader remains the exact saved native artifact. This controller
// submits existing typed project operations; it supplies no engineering verdict.
const byId=id=>document.getElementById(id), frame=byId('view');
const uiSession=crypto.randomUUID();
let state, csrf, selectedId, busy=false, dirty=false, pending=null, unknown=false, polling=false, ghost=null;
let formRevision, formCommit, restoredSelection, restoredNavigation, restoredInspection;
let editTargetId, draftGeneration=0, loadGeneration=0, gestureActive=false, frameReady=false;
const key=()=> 'cse-pending-save:'+state.projection.project_id;
const notice=text=>{byId('notice').textContent=text;};
const clone=value=>JSON.parse(JSON.stringify(value));
function controls(){
  if(frameReady)frame.contentWindow.cseDiagramNavigation?.lock(gestureActive);
  const different=Boolean(editTargetId&&selectedId!==editTargetId);
  byId('edits').disabled=busy||gestureActive||unknown||Boolean(pending)||!selectedId||different;
  byId('save').disabled=busy||!pending||Boolean(pending.stale);
  byId('save').textContent=unknown?'Retry save with the same request ID':'Save change';
  byId('discard').disabled=busy||unknown;
  byId('refresh').disabled=busy||gestureActive;
  byId('preview').hidden=!pending;
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
    for(const field of ['x','y','width','height'])byId('box-'+field).value=state.layout.nodes[id][field];
    formRevision=state.revision;formCommit=state.commit;
  }
  const target=editingNode();
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
    pending={request:change,description,preview:result.preview,stale:false};
    const reviewLines=result.preview.configuration_reviews.map(review=>review.file+': '+review.report.status);
    byId('summary').textContent=description+'\nBase revision: '+result.preview.base_revision+'\nChanged model files: '+(result.preview.changed_model_files.join(', ')||'none')+'\nChanged companion files: '+(result.preview.changed_linked_records.join(', ')||'none')+(reviewLines.length?'\nRetained configuration reviews:\n'+reviewLines.join('\n'):'');
    byId('pending-indicator').textContent='Unsaved change · saved model below remains authoritative';
    if(layoutBox)drawGhost(layoutBox.id,layoutBox.box);
    notice('Candidate checked. Review it, then save or discard.');
    return{outcome:'previewed',request:clone(change),preview:clone(result.preview)};
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
  if(!preserve){dirty=false;pending=null;removeGhost();formRevision=state.revision;formCommit=state.commit;}
  frameReady=false;frame.srcdoc=result.view_html;
  controls();
  return true;
}
function previewRename(){const found=editingNode();if(found)return previewChange(request('rename',{element_id:editTargetId,new_name:byId('rename-name').value}),'Rename '+found[1].element+' → '+byId('rename-name').value);}
function previewRestore(){return previewChange(request('restore',{target_revision:Number(byId('restore-target').value)}),'Restore all source, identity and presentation state from revision '+byId('restore-target').value+' into a new revision.');}
byId('rename-form').addEventListener('submit',event=>{event.preventDefault();previewRename();});
byId('layout-form').addEventListener('submit',event=>{event.preventDefault();previewLayout();});
byId('restore-form').addEventListener('submit',event=>{event.preventDefault();previewRestore();});
byId('edits').addEventListener('input',event=>{if(event.target.id==='drag-action')return;draftGeneration++;dirty=true;if(pending&&!unknown){pending=null;removeGhost();}controls();});
function discard(){if(unknown||busy)return;draftGeneration++;pending=null;dirty=false;removeGhost();showFields(true);notice('Pending values discarded. Saved state is unchanged.');controls();}
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
    sessionStorage.setItem(key(),JSON.stringify({request:savedRequest,selectedId,editTargetId,description:pending.description}));
    const result=await api('/api/apply',savedRequest);
    acknowledged=result.receipt;
    sessionStorage.removeItem(key());unknown=false;pending=null;dirty=false;removeGhost();
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
    if(saved){const entry=JSON.parse(saved);pending={request:entry.request,description:entry.description,stale:false};selectedId=entry.selectedId;editTargetId=entry.editTargetId||entry.request.element_id||entry.selectedId;restoredSelection=selectedId;unknown=true;byId('pending-indicator').textContent='Unacknowledged save';byId('summary').textContent=(entry.description||entry.request.operation)+'\nRequest '+entry.request.request_id+' · expected revision '+entry.request.expected_revision;notice('A previous save needs acknowledgement. Retry the exact request to recover its receipt.');controls();}
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
