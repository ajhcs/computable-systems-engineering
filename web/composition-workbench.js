'use strict';
// The embedded reader remains the exact saved native artifact. This controller
// submits existing typed project operations; it supplies no engineering verdict.
const byId=id=>document.getElementById(id), frame=byId('view');
const uiSession=crypto.randomUUID();
let state, csrf, selectedId, selectedOccurrenceId, busy=false, dirty=false, pending=null, unknown=false, polling=false, ghost=null;
let formRevision, formCommit, restoredSelection, restoredNavigation, restoredInspection, restoredOccurrence, restoredInspectionOccurrence;
let editTargetId, editTargetOccurrenceId, editTargetName, draftGeneration=0, loadGeneration=0, gestureActive=false, frameReady=false, creationDraft=false, draftKind=null;
let candidateSvg=null,candidateMode='readable';
let ownershipContext=null,ownershipGeneration=0,ownershipOffset=0;
let sourceGeneration=0,sourceReadBusy=false,sourceReadState=null,sourceOptionsKey=null;
let initialized=false,viewStatus='loading',viewGeneration=0,lastReceipt=null;
const contextSubscribers=new Set();let contextQueued=false;
let provider,providerError;
try{provider=compositionProvider();}catch(error){providerError=error;}
const key=()=> 'cse-pending-save:'+state.projection.project_id;
const notice=text=>{byId('notice').textContent=text;notifyContext();};
const clone=value=>JSON.parse(JSON.stringify(value));
function compositionProvider(){
  if(!Object.hasOwn(globalThis,'cseCompositionHost'))return{
    kind:'loopback',localArtifacts:true,
    intentStorage:{getItem:key=>sessionStorage.getItem(key),setItem:(key,value)=>sessionStorage.setItem(key,value),removeItem:key=>sessionStorage.removeItem(key)},
    request:async({operation,payload})=>{
      const path={session:'/session',state:'/api/state',head:'/api/head',inspection:'/api/inspection',ownership_context:'/api/ownership-context',source:'/api/source',preview_view:'/api/preview-view',preview:'/api/preview',apply:'/api/apply',receipt:'/api/receipt'}[operation];
      const options={credentials:'same-origin',cache:'no-store'};
      if(payload!==undefined)Object.assign(options,{method:'POST',headers:{'Content-Type':'application/json','X-CSE-CSRF':csrf||''},body:JSON.stringify(payload)});
      const response=await fetch(path,options);return{status:response.status,body:await response.json()};
    },openArtifact:null,
  };
  const supplied=globalThis.cseCompositionHost;
  if(!supplied||supplied.version!=='cse-composition-host-1'||typeof supplied.kind!=='string'||!supplied.kind||typeof supplied.request!=='function'||
      !supplied.intentStorage||['getItem','setItem','removeItem'].some(name=>typeof supplied.intentStorage[name]!=='function')||
      supplied.openArtifact!==null&&typeof supplied.openArtifact!=='function')throw Error('Unsupported or incomplete physical-composition host provider.');
  return Object.freeze({kind:supplied.kind,localArtifacts:false,request:supplied.request.bind(supplied),
    intentStorage:Object.freeze(Object.fromEntries(['getItem','setItem','removeItem'].map(name=>[name,supplied.intentStorage[name].bind(supplied.intentStorage)]))),
    openArtifact:supplied.openArtifact?.bind(supplied)||null});
}
function notifyContext(){
  if(contextQueued||!contextSubscribers.size)return;
  contextQueued=true;queueMicrotask(()=>{contextQueued=false;for(const subscriber of contextSubscribers){
    const failed=()=>console.warn('CSE context subscriber failed; saved outcome is unchanged.');
    try{const result=subscriber(workbenchContext());if(result&&typeof result.then==='function')Promise.resolve(result).catch(failed);}catch(error){failed();}
  }});
}
const formKinds={'rename-form':'rename','multiplicity-form':'multiplicity','typing-form':'typing','layout-form':'layout','restore-form':'restore','create-definition-form':'create_definition','create-usage-form':'create_usage','ownership-form':'reparent'};
const operationKind=operation=>({set_layout:'layout',set_multiplicity:'multiplicity',set_types:'typing'}[operation]||operation);
const editableInputs=['ownership-values','typing-values','rename-name','multiplicity-lower','multiplicity-upper','box-x','box-y','box-width','box-height','restore-target','create-name','create-short','create-placement','create-x','create-y','create-width','create-height','create-points','usage-name','usage-short','usage-type','usage-kind','usage-multiplicity','usage-lower','usage-upper','usage-placement','usage-x','usage-y','usage-width','usage-height','usage-points'];
function typeDefinitions(){return state?state.projection.inspection.declarations.map(id=>state.projection.inspection.occurrences[id]).filter(row=>row.kind==='PartDefinition'):[];}
function typingRows(){
  const rows=JSON.parse(byId('typing-values').value);
  if(!Array.isArray(rows)||rows.length>128||rows.some(row=>!row||typeof row!=='object'||Array.isArray(row)||Object.keys(row).length!==2||!Object.hasOwn(row,'type_id')||!Object.hasOwn(row,'native_name')||row.type_id!==null&&typeof row.type_id!=='string'||row.native_name!==null&&typeof row.native_name!=='string'))throw Error('Invalid retained explicit-type rows.');
  return rows;
}
function setTypingRows(rows,focus=null){byId('typing-values').value=JSON.stringify(rows);renderTypingRows(focus);}
function renderTypingRows(focus=null){
  const rows=typingRows(),definitions=typeDefinitions(),container=byId('typing-rows');container.replaceChildren();
  rows.forEach((row,index)=>{
    const entry=document.createElement('div');entry.className='typing-row';
    const label=document.createElement('label');label.textContent='Explicit type '+(index+1);
    const select=document.createElement('select');select.setAttribute('aria-label','Explicit type '+(index+1));
    const options=[['','Choose a part definition'],...definitions.map(def=>[def.element_id,def.element])];
    if(row.type_id&&!definitions.some(def=>def.element_id===row.type_id))options.push([row.type_id,'Unavailable type']);
    for(const [value,text]of options){const option=document.createElement('option');option.value=value;option.textContent=text;select.append(option);}
    select.value=row.type_id||'';
    select.addEventListener('change',()=>{const current=typingRows(),definition=typeDefinitions().find(def=>def.element_id===select.value);current[index]={type_id:select.value||null,native_name:definition?.element||null};setTypingRows(current,index);byId('typing-values').dispatchEvent(new Event('input',{bubbles:true}));});
    label.append(select);entry.append(label);
    const detail=document.createElement('p'),available=definitions.find(def=>def.element_id===row.type_id);
    detail.textContent=available?available.element:row.type_id||row.native_name?'Unavailable type: '+(row.native_name||'')+(row.type_id?' · '+row.type_id:'')+'. Replace or remove it explicitly.':'Choose a definition; an unfinished row is not a request to remove all typing.';entry.append(detail);
    const remove=document.createElement('button');remove.type='button';remove.textContent='Remove explicit type '+(index+1);
    remove.addEventListener('click',()=>{const current=typingRows();current.splice(index,1);setTypingRows(current,Math.min(index,current.length-1));byId('typing-values').dispatchEvent(new Event('input',{bubbles:true}));});entry.append(remove);container.append(entry);
  });
  byId('typing-empty').textContent=rows.length?'Each selected entry is an explicit type, not an alternative.':'No explicit typing requested. Implied or inherited typing may still apply.';
  byId('typing-add').disabled=rows.length>=128;
  if(focus!==null){const next=container.querySelectorAll('select')[focus]||byId('typing-add');next.focus({preventScroll:true});next.scrollIntoView({block:'nearest',inline:'nearest'});}
}
byId('typing-add').addEventListener('click',()=>{const rows=typingRows();if(rows.length>=128)return;rows.push({type_id:null,native_name:null});setTypingRows(rows,rows.length-1);byId('typing-values').dispatchEvent(new Event('input',{bubbles:true}));});
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
  sourceControls();
  if(frameReady)frame.contentWindow.cseDiagramNavigation?.lock(gestureActive);
  const different=Boolean(editTargetOccurrenceId&&(selectedId!==editTargetId||selectedOccurrenceId!==editTargetOccurrenceId));
  byId('edits').disabled=busy||gestureActive||unknown||Boolean(pending)||!initialized||!frameReady||different;
  byId('typing-fields').disabled=Boolean(draftKind&&draftKind!=='typing')||!state||editingNode()?.[1].kind!=='PartUsage';
  byId('multiplicity-fields').disabled=Boolean(draftKind&&draftKind!=='multiplicity')||!state||editingNode()?.[1].kind!=='PartUsage';
  byId('create-definition-fields').disabled=!state||state.projection.mode!=='definitions'||editingNode()?.[1].kind!=='PartDefinition'||!Object.values(state.projection.nodes).some(n=>n.element_id===editTargetId)||Boolean(draftKind&&draftKind!=='create_definition');
  for(const id of ['rename-form','layout-form','restore-form'])for(const input of byId(id).querySelectorAll('input,button,select'))input.disabled=Boolean(draftKind&&draftKind!==formKinds[id])||(id==='rename-form'&&!editingNode())||(id==='layout-form'&&!editingNode()?.[1].frame_id);
  byId('create-coordinates').hidden=byId('create-placement').value!=='manual';
  byId('create-usage-fields').disabled=!editingNode()||Boolean(draftKind&&draftKind!=='create_usage');
  byId('usage-coordinates').hidden=byId('usage-placement').value!=='manual';
  byId('usage-bounds').hidden=byId('usage-multiplicity').value!=='finite';
  const typeId=byId('usage-type').value;byId('usage-type-availability').textContent=typeId&&!state?.projection.inspection.declarations.some(id=>{const row=state.projection.inspection.occurrences[id];return row.element_id===typeId&&row.kind==='PartDefinition'})?'Selected type is unavailable: '+typeId+'. Choose an existing definition explicitly or retain this draft until the type is restored.':'';
  byId('usage-presentation').textContent=state?.projection.mode==='usages'&&editingNode()?.[1].kind==='PartUsage'&&Object.values(state.projection.nodes).some(n=>n.element_id===editTargetId)&&byId('usage-kind').value==='composite'?'A new composite child gets an ownership frame and declaration row.':'The new usage appears in the declaration table; no ownership frame or route is added. Manual frame placement will be refused.';
  byId('ownership-fields').disabled=!editingNode()||Boolean(draftKind&&draftKind!=='reparent');
  byId('ownership-candidate-controls').hidden=pending?.request.operation!=='reparent';
  byId('save').disabled=busy||!pending||Boolean(pending.stale)||!frameReady||(!unknown&&pending?.request.operation==='reparent'&&!byId('ownership-candidate-ack').checked);
  byId('ownership-candidate-ack').disabled=busy||unknown;
  byId('ownership-show-candidate').disabled=busy||unknown||Boolean(pending?.stale)||!byId('ownership-candidate-view').value;
  byId('save').textContent=unknown?'Retry save with the same request ID':'Save change';
  byId('discard').disabled=busy||unknown;
  byId('refresh').disabled=busy||gestureActive;
  byId('preview').hidden=!pending;
  if(!pending&&candidateSvg)showCandidate(null);
  if(pending)byId('pending-indicator').textContent=unknown?'Unacknowledged save · retain this exact request':pending.stale?'Stale candidate · current saved model is separate':'Unsaved change · saved model below remains authoritative';
  byId('return-target').hidden=!different;byId('return-target').disabled=busy||gestureActive||!editingNode();
  byId('edit-selected').hidden=!different;
  byId('edit-selected').disabled=busy||unknown||Boolean(pending);
  byId('discard-draft').hidden=!dirty||Boolean(pending);
  byId('discard-draft').disabled=busy||unknown;
  notifyContext();
}
async function api(path,body,requestDigest){
  if(providerError)throw providerError;
  const operation={'/session':'session','/api/state':'state','/api/head':'head','/api/inspection':'inspection','/api/ownership-context':'ownership_context','/api/source':'source','/api/preview-view':'preview_view','/api/preview':'preview','/api/apply':'apply','/api/receipt':'receipt'}[path];
  if(!operation)throw Error('Unsupported physical-composition operation.');
  const response=await provider.request({operation,payload:body}),result=response?.body;
  if(!Number.isInteger(response?.status)||response.status<100||response.status>599||!result||typeof result!=='object'||Array.isArray(result))throw Error('Invalid physical-composition transport response.');
  if(response.status<200||response.status>=300){const error=new Error(result.error?.detail||'Request failed');error.code=result.error?.code;error.definitiveRefusal=result.error?.definitive_refusal===true;throw error;}
  if(operation==='receipt'&&!/^[a-f0-9]{64}$/.test(result.request_sha256||''))throw Error('The exact native request digest was not received.');
  if(operation==='apply'||operation==='receipt'&&result.receipt!==null){
    const receipt=result.receipt;
    if(!receipt||receipt.request_id!==body.request_id||receipt.operation!==body.operation||receipt.revision!==body.expected_revision+1||
        receipt.project_id!==state.projection.project_id||receipt.request_sha256!==(operation==='receipt'?result.request_sha256:requestDigest)||
        typeof receipt.commit!=='string'||!/^[a-f0-9]{40}$/.test(receipt.commit))throw Error('A matching durable transaction receipt was not received.');
  }
  return result;
}
function selectedNode(){const rows=state?.projection.inspection.occurrences,node=rows&&Object.hasOwn(rows,selectedOccurrenceId)?rows[selectedOccurrenceId]:null;return node&&node.element_id===(selectedId||null)?[selectedOccurrenceId,node]:undefined;}
function editingNode(){const rows=state?.projection.inspection.occurrences,node=rows&&Object.hasOwn(rows,editTargetOccurrenceId)?rows[editTargetOccurrenceId]:null;return editTargetId&&node?.element_id===editTargetId?[editTargetOccurrenceId,node]:undefined;}
function showFields(force=false){
  const found=selectedNode();
  if(!found)return;
  const [id,node]=found;
  byId('selected').textContent='Selected saved element: '+node.element+' · revision '+state.revision;
  if(force||!dirty&&!pending){
    editTargetId=selectedId||null;editTargetOccurrenceId=id;editTargetName=node.element;
    byId('rename-name').value=node.native?.name||'';
    setTypingRows((node.native?.types||[]).map(name=>({type_id:typeDefinitions().find(row=>row.element===name)?.element_id||null,native_name:name})));
    const quantity=node.native?.multiplicity;
    for(const bound of ['lower','upper'])byId('multiplicity-'+bound).value=node.kind==='PartUsage'&&['default','literal'].includes(quantity?.status)?quantity[bound]:'';
    for(const field of ['x','y','width','height'])byId('box-'+field).value=node.frame_id?state.layout.nodes[node.frame_id][field]:'';
    formRevision=state.revision;formCommit=state.commit;
    resetOwnershipFields();
    for(const id of ['usage-name','usage-short','usage-type','usage-lower','usage-upper','usage-x','usage-y','usage-width','usage-height','usage-points'])byId(id).value='';byId('usage-kind').value='composite';byId('usage-multiplicity').value='default';byId('usage-placement').value='automatic';
    byId('create-name').value='';byId('create-short').value='';byId('create-placement').value='automatic';
    for(const field of ['x','y','width','height','points'])byId('create-'+field).value='';
  }
  const target=editingNode();
  byId('usage-owner').textContent=target?'Captured native owner: '+target[1].element+' · revision '+formRevision:'Select a native owner.';
  byId('create-owner').textContent=target&&state.projection.mode==='definitions'&&target[1].kind==='PartDefinition'&&Object.values(state.projection.nodes).some(n=>n.element_id===editTargetId)?'Native owner: '+target[1].element+' · captured revision '+formRevision:'Owned-definition creation requires a part definition represented in this definition hierarchy.';
  byId('layout-applicability').textContent=target?.[1].frame_id?'Geometry applies to this framed occurrence.':'This inspection row has no frame geometry.';
  byId('typing-saved').textContent=target?.[1].kind==='PartUsage'?'Saved explicit types of '+target[1].element+': '+(target[1].native.types.join(', ')||'No explicit typing'):target?'Part definitions use specialization rather than feature typing.':'No native declaration is available for editing.';
  byId('multiplicity-saved').textContent=target?.[1].kind==='PartUsage'?'Saved multiplicity of '+target[1].element+': '+(target[1].native.source_multiplicity||'no local bounds')+' · '+target[1].native.multiplicity.status:target?'Part definitions have no usage multiplicity.':'No native declaration is available for editing.';
  byId('edit-target').textContent=target?'Editing target: '+target[1].element+' · base revision '+formRevision:editTargetId?'The retained edit target '+(editTargetName||editTargetId)+' is absent from this saved inspection.':'No native declaration is available for editing.';
  controls();
}
function selectionChanged(){
  const inner=frame.contentWindow.cseSelectionContext;
  if(!inner)return;
  const next=inner.selected_element_ids[0]||null,nextOccurrence=inner.selected_occurrence_ids[0];
  if(next!==selectedId||nextOccurrence!==selectedOccurrenceId)draftGeneration++;
  if((next!==selectedId||nextOccurrence!==selectedOccurrenceId)&&(dirty||pending))notice('Inspection selection changed. The retained edit still targets its original element.');
  selectedId=next;selectedOccurrenceId=nextOccurrence;
  globalThis.cseSelectionContext={...inner,ui_session_id:uiSession,scope:'local_connected_saved_selection'};
  showFields();notifyContext();
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
  const kind=operationKind(change.operation);if(dirty&&draftKind&&draftKind!==kind)return{outcome:'refused',error:{code:'retained_edit',detail:'Preview the retained draft in its own form, or explicitly discard it first.'}};
  draftKind=kind;creationDraft=['create_definition','create_usage'].includes(kind);dirty=true;
  draftGeneration++;
  busy=true;controls();notice('Checking the unsaved candidate…');
  try{
    const result=await api('/api/preview',change);
    const {candidate_svg,...metadata}=result.preview;
    const checked=result.preview.checked_request||change;
    if(change.operation==='reparent'&&(JSON.stringify(orderedOwnership({...checked,checked_bundle_sha256:null}))!==JSON.stringify(orderedOwnership(change))||!/^[a-f0-9]{64}$/.test(checked.checked_bundle_sha256||'')))throw Error('Ownership preview returned a different request or missing candidate binding.');
    pending={request:checked,description,preview:metadata,stale:false};
    byId('ownership-candidate-ack').checked=false;
    prepareOwnershipCandidateViews();
    const affected=result.preview.affected_views||{},showCurrent=change.operation!=='reparent'||!Object.keys(affected).length||Object.hasOwn(affected,state.projection.id);
    showCandidate(showCurrent?candidate_svg||null:null);
    if(!showCurrent)byId('ownership-candidate-status').textContent='The current saved view does not show the moved declaration. Inspect the selected affected candidate view explicitly.';
    const reviewLines=result.preview.configuration_reviews.map(review=>review.file+': '+review.report.status);
    byId('summary').textContent=description+'\nBase revision: '+result.preview.base_revision+'\nChanged model files: '+(result.preview.changed_model_files.join(', ')||'none')+'\nChanged companion files: '+(result.preview.changed_linked_records.join(', ')||'none')+(reviewLines.length?'\nRetained configuration reviews:\n'+reviewLines.join('\n'):'');
    const edited=result.preview.edited_element;if(edited)byId('summary').textContent+='\nCandidate native declaration: '+edited.element+'\nNative owner: '+(edited.native.owner||(edited.native.owner_kind==='Namespace'?'Unnamed namespace':'Unresolved'))+(edited.kind==='PartDefinition'?'\nDeclared supertypes: '+((edited.native.supertypes||[]).join(', ')||'None'):'\nExplicit types: '+((edited.native.types||[]).join(', ')||'No explicit typing'));
    if(result.preview.ownership_change)byId('summary').textContent+='\nOwnership/source/view consequences:\n'+JSON.stringify(result.preview.ownership_change,null,2);
    const created=result.preview.created_element;if(created){const native=created.native;byId('summary').textContent+='\nNew native declaration: '+created.element+'\nNative owner: '+native.owner;if(created.kind==='PartUsage')byId('summary').textContent+='\nDeclaration kind: '+(native.is_composite?'composite part':'reference part')+'\nExplicit type: '+(native.type||'none')+'\nMultiplicity: '+native.multiplicity.status+' ['+native.multiplicity.lower+'..'+native.multiplicity.upper+']';}
    byId('pending-indicator').textContent='Unsaved change · saved model below remains authoritative';
    if(layoutBox)drawGhost(layoutBox.id,layoutBox.box);
    notice('Candidate checked. Review it, then save or discard.');
    return{outcome:'previewed',request:clone(checked),preview:clone(metadata)};
  }catch(error){removeGhost();pending=null;notice(error.code==='stale_revision'?'Conflict: '+error.message+'. Your form values remain available. Refresh before another preview.':error.message);return{outcome:'refused',error:{code:error.code||'preview_unavailable',detail:error.message}};}
  finally{busy=false;controls();}
}
function previewLayout(){
  const found=editingNode();if(!found?.[1].frame_id)return{outcome:'refused',error:{code:'not_framed',detail:'This inspection row has no frame geometry.'}};
  const box=Object.fromEntries(['x','y','width','height'].map(field=>[field,Number(byId('box-'+field).value)]));
  const [occurrence,node]=found,id=node.frame_id;
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
frame.addEventListener('load',async()=>{
  const doc=frame.contentDocument;if(!doc?.querySelector('#cse-data'))return;
  let saved;try{saved=JSON.parse(doc.querySelector('#cse-data').textContent);}catch(error){return;}
  if(saved.commit!==state.commit||saved.revision!==state.revision)return;
  const ticket=viewGeneration,commit=state.commit,revision=state.revision,source=frame.srcdoc;
  const current=()=>ticket===viewGeneration&&doc===frame.contentDocument&&source===frame.srcdoc&&commit===state.commit&&revision===state.revision;
  viewStatus='checking_fonts';frameReady=false;frame.style.visibility='hidden';controls();
  for(const link of doc.querySelectorAll('a')){
    const kind=link.getAttribute('href'),artifact={kind,commit,revision};
    if(provider.localArtifacts){link.href=new URL('/'+kind,location.origin).href+'?commit='+commit;link.target='_blank';link.rel='noopener';}
    else{
      link.removeAttribute('href');
      if(!provider.openArtifact){link.setAttribute('aria-disabled','true');link.title='This host does not support source-bound artifact transfer.';}
      else{link.href='#';link.addEventListener('click',async event=>{event.preventDefault();try{const result=await provider.openArtifact(artifact);if(typeof result?.isError!=='boolean')throw Error('A transfer outcome was not returned.');notice(result.isError?'Artifact transfer was refused or cancelled.':'Artifact transfer requested.');}catch(error){notice('Artifact transfer unavailable: '+error.message);}});}
    }
  }
  let deadline;
  try{
    const faces=[...(doc.fonts||[])],expected=new Set(['DejaVu Sans:400','DejaVu Sans:700','DejaVu Sans Mono:400','DejaVu Sans Mono:700']);
    if(faces.length!==expected.size||faces.some(face=>!expected.delete(face.family.replace(/["']/g,'')+':'+face.weight)))throw Error('Original engineering fonts are missing.');
    await Promise.race([Promise.all(faces.map(face=>face.load())),new Promise((_,reject)=>{deadline=setTimeout(()=>reject(Error('Original-font loading timed out.')),10000);})]);
  }catch(error){
    if(!current())return;
    viewStatus='unsupported_fonts';const drawing=doc.querySelector('.diagram');if(drawing)drawing.style.display='none';frame.style.visibility='visible';
    notice('Unsupported view: the original engineering fonts could not load. The saved model remains available; this drawing is not qualified.');controls();return;
  }finally{clearTimeout(deadline);}
  if(!current())return;
  doc.addEventListener('cse-selection-change',selectionChanged);
  doc.addEventListener('cse-navigation-change',()=>{if(frameReady)selectionChanged();});
  const occurrences=state.projection.inspection.occurrences;
  let wanted=restoredOccurrence&&Object.hasOwn(occurrences,restoredOccurrence)?occurrences[restoredOccurrence]:null;
  if(wanted&&wanted.origin==='frame'&&wanted.element_id!==restoredSelection)wanted=null;
  if(!wanted&&restoredSelection&&!restoredOccurrence){const found=Object.entries(state.projection.nodes).find(([,n])=>n.element_id===restoredSelection);wanted=found?occurrences[found[0]]:occurrences['decl:'+restoredSelection];}
  if(wanted)frame.contentWindow.cseReaderSelection.select(wanted.id);
  const navigation=frame.contentWindow.cseDiagramNavigation;
  if(restoredNavigation)navigation.restore(restoredNavigation);
  if(restoredNavigation?.mode!=='overview'&&wanted&&(!restoredNavigation||wanted.id!==restoredInspectionOccurrence))frame.contentWindow.cseReaderSelection.reveal(wanted.id);
  restoredNavigation=null;
  restoredSelection=null;restoredOccurrence=null;viewStatus='ready';frameReady=true;frame.style.visibility='visible';selectionChanged();bindDragging();controls();
});
async function loadState(preserve=false,background=false,recover=false){
  const generation=draftGeneration,ticket=++loadGeneration;
  const result=await api('/api/state');
  const saved=recover?await provider.intentStorage.getItem('cse-pending-save:'+result.state.projection.project_id):null;
  if(ticket!==loadGeneration||background&&(busy||gestureActive||dirty||pending||generation!==draftGeneration))return false;
  restoredNavigation=frameReady?frame.contentWindow.cseDiagramNavigation.state():null;
  restoredInspection=selectedId;restoredInspectionOccurrence=selectedOccurrenceId;
  state=result.state;csrf=result.csrf;
  const retainedType=preserve?byId('usage-type').value:'';
  const typeOptions=[['','No explicit typing'],...state.projection.inspection.declarations.map(id=>state.projection.inspection.occurrences[id]).filter(row=>row.kind==='PartDefinition').map(row=>[row.element_id,row.element])];
  if(retainedType&&!typeOptions.some(([id])=>id===retainedType))typeOptions.push([retainedType,'Unavailable saved type · '+retainedType]);
  byId('usage-type').replaceChildren(...typeOptions.map(([id,label])=>{const option=document.createElement('option');option.value=id;option.textContent=label;return option;}));byId('usage-type').value=retainedType;restoredSelection=selectedId;restoredOccurrence=selectedOccurrenceId;
  byId('saved').textContent='Saved revision '+state.revision+' · '+state.projection.id+' · '+state.commit.slice(0,12);
  const restoreTarget=preserve?byId('restore-target').value:null;
  byId('restore-target').replaceChildren(...state.history.map(row=>{const option=document.createElement('option');option.value=row.revision;option.textContent='Revision '+row.revision+' · '+row.operation;return option;}));
  if(restoreTarget!==null)byId('restore-target').value=restoreTarget;
  if(!preserve){dirty=false;creationDraft=false;draftKind=null;pending=null;removeGhost();formRevision=state.revision;formCommit=state.commit;}
  if(preserve)renderTypingRows();
  if(recover)restoreIntent(saved);
  frameReady=false;viewStatus='loading';viewGeneration++;frame.style.visibility='hidden';frame.srcdoc=result.view_html;
  controls();
  return true;
}
function previewTyping(){
  const found=editingNode();if(!found||found[1].kind!=='PartUsage')return{outcome:'refused',error:{code:'element_kind',detail:'Select a native part usage.'}};
  const rows=typingRows(),ids=rows.map(row=>row.type_id);
  if(ids.some(id=>!id||!typeDefinitions().some(def=>def.element_id===id))||new Set(ids).size!==ids.length){const detail='Choose distinct existing part definitions. Replace or remove unavailable and unfinished rows explicitly.';notice(detail);return{outcome:'refused',error:{code:'typing',detail}};}
  return previewChange(request('set_types',{element_id:editTargetId,type_ids:ids}),'Explicit types of '+found[1].element+' → '+(rows.map(row=>typeDefinitions().find(def=>def.element_id===row.type_id).element).join(', ')||'No explicit typing'));
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
function previewCreateUsage(){
  const found=editingNode();if(!found)return;
  let placement=null,multiplicity=null;
  const refuse=(code,detail)=>{notice(detail);return{outcome:'refused',error:{code,detail}};};
  if(byId('usage-multiplicity').value==='finite'){
    const raw=['lower','upper'].map(key=>byId('usage-'+key).value),[lower,upper]=raw.map(Number);
    if(raw.some(value=>!value.trim())||!Number.isInteger(lower)||!Number.isInteger(upper)||lower<0||upper<lower||upper>2147483647)return refuse('multiplicity','Supply both finite integer bounds: 0 ≤ lower ≤ upper ≤ 2147483647.');
    multiplicity={lower,upper};
  }
  if(byId('usage-placement').value==='manual'){
    const fields=['x','y','width','height'],box=Object.fromEntries(fields.map(key=>[key,Number(byId('usage-'+key).value)]));
    const points=byId('usage-points').value.split(/\r?\n/).map(line=>line.split(',').map(value=>value.trim()===''?NaN:Number(value)));
    if(fields.some(key=>byId('usage-'+key).value==='')||!Object.values(box).every(Number.isFinite)||points.length<2||points.length>128||points.some(p=>p.length!==2||!p.every(Number.isFinite)))return refuse('input','Supply frame coordinates and two to 128 finite x,y route points.');
    placement={box,points};
  }
  return previewChange(request('create_usage',{owner_id:editTargetId,element_id:crypto.randomUUID(),new_name:byId('usage-name').value,short_id:byId('usage-short').value||null,type_id:byId('usage-type').value||null,is_composite:byId('usage-kind').value==='composite',multiplicity,view_id:state.projection.id,placement}),'Create part usage '+byId('usage-name').value+' under '+found[1].element);
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
byId('create-usage-form').addEventListener('submit',event=>{event.preventDefault();previewCreateUsage();});
byId('create-definition-form').addEventListener('submit',event=>{event.preventDefault();previewCreateDefinition();});
byId('ownership-form').addEventListener('submit',event=>{event.preventDefault();previewOwnership();});
byId('typing-form').addEventListener('submit',event=>{event.preventDefault();previewTyping();});
byId('multiplicity-form').addEventListener('submit',event=>{event.preventDefault();previewMultiplicity();});
byId('layout-form').addEventListener('submit',event=>{event.preventDefault();previewLayout();});
byId('restore-form').addEventListener('submit',event=>{event.preventDefault();previewRestore();});
byId('edits').addEventListener('input',event=>{if(event.target.id==='drag-action')return;draftKind=formKinds[event.target.closest('form')?.id]||draftKind;creationDraft=['create_definition','create_usage'].includes(draftKind);draftGeneration++;dirty=true;if(pending&&!unknown){pending=null;removeGhost();}controls();});
function discard(){if(unknown||busy)return;draftGeneration++;pending=null;dirty=false;creationDraft=false;draftKind=null;removeGhost();showFields(true);notice('Pending values discarded. Saved state is unchanged.');controls();}
byId('discard').addEventListener('click',discard);
byId('discard-draft').addEventListener('click',discard);
byId('edit-selected').addEventListener('click',discard);
byId('return-target').addEventListener('click',()=>{const found=editingNode();if(!found)return;frame.contentWindow.cseReaderSelection.select(found[0],{reveal:true});selectionChanged();const input=byId({create_definition:'create-name',create_usage:'usage-name',multiplicity:'multiplicity-lower',typing:'typing-add',reparent:'ownership-load',layout:'box-x',restore:'restore-target'}[draftKind]||'rename-name');input.focus({preventScroll:true});input.scrollIntoView({block:'nearest',inline:'nearest'});});
async function refreshSaved(){
  if(busy||gestureActive)return{outcome:'refused',error:{code:'interaction_busy',detail:'Finish the current interaction first.'}};
  if(!initialized)return await start();
  draftGeneration++;busy=true;controls();
  try{const keepValues=dirty||Boolean(pending),target=editTargetId,targetOccurrence=editTargetOccurrenceId;await loadState(true);if(!unknown){pending=null;dirty=keepValues;formRevision=state.revision;formCommit=state.commit;if(keepValues){restoredSelection=target;restoredOccurrence=targetOccurrence;}else showFields(true);}notice(unknown?'Saved state refreshed. Retry the pending save to recover its durable receipt.':'Saved state refreshed. Form values retain their original target; review it, then preview against revision '+state.revision+'.');return{outcome:'refreshed',revision:state.revision,commit:state.commit};}
  catch(error){notice(error.message);return{outcome:'refused',error:{code:error.code||'refresh_unavailable',detail:error.message}};}
  finally{busy=false;controls();}
}
byId('refresh').addEventListener('click',refreshSaved);
async function saveChange(){
  if(!pending||busy||gestureActive||pending.stale||!unknown&&pending.request.operation==='reparent'&&!byId('ownership-candidate-ack').checked)return{outcome:'refused',error:{code:'save_unavailable',detail:'Inspect and preview a current change before saving.'}};
  draftGeneration++;
  busy=true;controls();notice('Saving the checked request…');
  const savedRequest=pending.request;
  let acknowledged=null,dispatched=false;const wasUnknown=unknown;
  try{
    // Native preview/lookup supplies the canonical digest. Reimplementing its
    // JSON number encoding in a browser would make valid layout receipts drift.
    let digest=pending.preview?.request_sha256;
    if(!/^[a-f0-9]{64}$/.test(digest||'')){const lookup=await api('/api/receipt',savedRequest);digest=lookup.request_sha256;pending.preview={...pending.preview,request_sha256:digest};}
    await provider.intentStorage.setItem(key(),JSON.stringify({request:savedRequest,selectedId,selectedOccurrenceId,editTargetId,editTargetOccurrenceId,editTargetName,draftKind,description:pending.description,
      request_sha256:digest,baseCommit:formCommit,fields:Object.fromEntries(editableInputs.map(id=>[id,byId(id).value]))}));
    dispatched=true;
    const result=await api('/api/apply',savedRequest,digest);
    acknowledged=result.receipt;lastReceipt=clone(acknowledged);
    let cleanupError=null;try{await provider.intentStorage.removeItem(key());}catch(error){cleanupError=error;}
    unknown=false;pending=null;dirty=false;creationDraft=false;draftKind=null;removeGhost();
    if(['create_definition','create_usage'].includes(savedRequest.operation)){selectedId=savedRequest.element_id;selectedOccurrenceId=null;}
    await loadState();
    notice('Saved revision '+result.receipt.revision+'. Request '+result.receipt.request_id+'.'+(state.revision!==result.receipt.revision?' The current project is now at revision '+state.revision+'.':'')+(cleanupError?' Pending-intent cleanup failed; reopening may offer the same acknowledged request for recovery.':''));
    return{outcome:'committed',receipt:clone(acknowledged)};
  }catch(error){
    if(acknowledged){notice('Saved revision '+acknowledged.revision+'. Refresh is unavailable: '+error.message);return{outcome:'committed',receipt:clone(acknowledged),refresh_error:{code:error.code||'refresh_unavailable',detail:error.message}};}
    else if(!dispatched){unknown=wasUnknown;notice('Save was not sent: the exact pending intent could not be bound and retained. This attempt made no save request; resolve the failure and retry the same change.');return{outcome:'not_sent',request:clone(savedRequest),error:{code:'intent_retention',detail:error.message}};}
    else if(error.definitiveRefusal){let cleanupError=false;try{await provider.intentStorage.removeItem(key());}catch(cleanup){cleanupError=true;}unknown=false;if(pending)pending.stale=error.code==='stale_revision';notice((error.code==='stale_revision'?'Conflict: ':'Save refused: ')+error.message+' Pending values are retained.'+(cleanupError?' Pending-intent cleanup failed.':''));return{outcome:'refused',error:{code:error.code,detail:error.message},request:clone(savedRequest)};}
    else{unknown=true;notice('Save acknowledgement was not received. Retry with the same request ID to recover its outcome.');return{outcome:'unconfirmed',request:clone(savedRequest),error:{code:'outcome_unknown',detail:'Retry this exact request or look up its durable receipt.'}};}
  }finally{busy=false;controls();}
}
byId('save').addEventListener('click',saveChange);
async function start(){
  if(busy)return{outcome:'refused',error:{code:'interaction_busy',detail:'Initialization is in progress.'}};
  busy=true;controls();
  try{
    if(providerError)throw providerError;
    const access=new URLSearchParams(location.hash.slice(1)).get('access');
    if(access){await api('/session',{access});history.replaceState(null,'',location.pathname);}
    await loadState(false,false,true);initialized=true;
    if(!unknown)notice('Select a saved element to inspect or edit.');
    return{outcome:'loaded',revision:state.revision,commit:state.commit};
  }catch(error){notice(error.message);return{outcome:'unavailable',error:{code:error.code||'initialization',detail:error.message}};}
  finally{busy=false;controls();}
}
function restoreIntent(saved){
    if(saved!==null&&typeof saved!=='string')throw Error('Invalid pending-intent storage response.');
    if(saved){
      const entry=JSON.parse(saved);pending={request:entry.request,description:entry.description,stale:false,preview:entry.request_sha256?{request_sha256:entry.request_sha256}:undefined};
      selectedId=entry.selectedId;selectedOccurrenceId=entry.selectedOccurrenceId||null;editTargetOccurrenceId=entry.editTargetOccurrenceId||null;editTargetName=entry.editTargetName||null;editTargetId=entry.editTargetId||entry.request.owner_id||entry.request.element_id||entry.selectedId;restoredSelection=selectedId;restoredOccurrence=selectedOccurrenceId;
      if(!editTargetOccurrenceId){const found=Object.entries(state.projection.nodes).find(([,n])=>n.element_id===editTargetId);if(found)editTargetOccurrenceId=found[0];}
      formRevision=entry.request.expected_revision;formCommit=entry.baseCommit||null;
      const retainedType=typeof entry.fields?.['usage-type']==='string'?entry.fields['usage-type']:entry.request.operation==='create_usage'?entry.request.type_id:null;
      if(retainedType&&![...byId('usage-type').options].some(option=>option.value===retainedType)){
        const option=document.createElement('option');option.value=retainedType;option.textContent='Unavailable saved type · '+retainedType;byId('usage-type').append(option);
      }
      for(const id of editableInputs)if(typeof entry.fields?.[id]==='string')byId(id).value=entry.fields[id];
      if(!entry.fields&&entry.request.operation==='create_usage')byId('usage-type').value=retainedType||'';
      if(!entry.fields&&entry.request.operation==='set_types')setTypingRows(entry.request.type_ids.map(id=>({type_id:id,native_name:typeDefinitions().find(row=>row.element_id===id)?.element||null})));
      renderTypingRows();
      // Older retained intents still expose the exact typed requested values.
      if(!entry.fields&&entry.request.operation==='set_multiplicity')for(const bound of ['lower','upper'])byId('multiplicity-'+bound).value=entry.request[bound];
      if(!entry.fields&&entry.request.operation==='rename')byId('rename-name').value=entry.request.new_name;
      unknown=true;byId('pending-indicator').textContent='Unacknowledged save';
      draftKind=entry.draftKind||operationKind(entry.request.operation);creationDraft=['create_definition','create_usage'].includes(draftKind);
      byId('summary').textContent=(entry.description||entry.request.operation)+'\nRequest '+entry.request.request_id+' · expected revision '+entry.request.expected_revision;
      notice('A previous save needs acknowledgement. Retry the exact request to recover its receipt.');controls();
    }
}
function workbenchContext(){
  if(!state)return{ready:false,host_transport:provider?.kind||'unavailable',view_status:viewStatus,notice:byId('notice').textContent,claim:'application_context_not_host_qualification'};
  const found=selectedNode(),target=editingNode();
  const navigation=frameReady?frame.contentWindow.cseDiagramNavigation.state():null;
  return clone({ready:frameReady&&initialized,host_transport:provider?.kind||'unavailable',view_status:viewStatus,notice:byId('notice').textContent,last_acknowledged_receipt:lastReceipt,
    guard:{project_id:state.projection.project_id,view_id:state.projection.id,ui_session_id:uiSession,
      model_revision:state.revision,commit:state.commit,bundle_sha256:state.projection.bundle_sha256,
      interaction_revision:draftGeneration,selected_element_id:found?.[1].element_id||null,
      selected_occurrence_id:found?.[0]||null,editing_element_id:editTargetId||null,editing_occurrence_id:editTargetOccurrenceId||null,
      navigation_revision:navigation?.revision||0,viewport_mode:navigation?.mode||'readable',viewport_left:navigation?.scroll_left||0,viewport_top:navigation?.scroll_top||0},
    navigation,
    busy,gesture_active:gestureActive,has_form_draft:dirty,draft_kind:draftKind,unconfirmed_save:unknown,
    selection:found?{occurrence_id:found[0],...found[1],display_label:found[1].frame_id?state.display_labels[found[1].frame_id]:found[1].native?.name||found[1].element,box:found[1].frame_id?state.layout.nodes[found[1].frame_id]:null}:null,
    editing_target:editTargetId?{element_id:editTargetId,occurrence_id:editTargetOccurrenceId,native_name:target?.[1].element||editTargetName,present:Boolean(target),
      base_revision:formRevision,base_commit:formCommit,declared_name:byId('rename-name').value,
      multiplicity:Object.fromEntries(['lower','upper'].map(field=>[field,byId('multiplicity-'+field).value])),
      box:Object.fromEntries(['x','y','width','height'].map(field=>[field,byId('box-'+field).value]))}:null,
    model_sources:state.model_sources,
    source_inspection:sourceReadState?{snapshot:sourceReadState.mode,file:sourceReadState.file,bundle_sha256:sourceReadState.bundle_sha256,request_sha256:sourceReadState.request_sha256,loaded_codepoints:[...sourceReadState.text].length,next_offset:sourceReadState.next_offset}:null,
    pending_change:pending?{...pending,request:clone(pending.request)}:null,
    ownership_draft:{raw_values:byId('ownership-values').value,candidate_reviewed:byId('ownership-candidate-ack').checked},
    typing_draft:{rows:typingRows().map(row=>({...row,available:Boolean(row.type_id&&typeDefinitions().some(def=>def.element_id===row.type_id))}))},
    usage_creation_draft:{declared_name:byId('usage-name').value,short_id:byId('usage-short').value||null,type_id:byId('usage-type').value||null,type_available:!byId('usage-type').value||state.projection.inspection.declarations.some(id=>state.projection.inspection.occurrences[id].element_id===byId('usage-type').value),is_composite:byId('usage-kind').value==='composite',multiplicity_mode:byId('usage-multiplicity').value,multiplicity:Object.fromEntries(['lower','upper'].map(key=>[key,byId('usage-'+key).value])),placement_mode:byId('usage-placement').value,box:Object.fromEntries(['x','y','width','height'].map(key=>[key,byId('usage-'+key).value])),route_text:byId('usage-points').value},
    creation_draft:{declared_name:byId('create-name').value,short_id:byId('create-short').value||null,placement_mode:byId('create-placement').value,
      box:Object.fromEntries(['x','y','width','height'].map(key=>[key,byId('create-'+key).value])),route_text:byId('create-points').value},
    restoration_target_revision:Number(byId('restore-target').value)||null,
    visible_elements:Object.entries(state.projection.nodes).map(([id,node])=>({occurrence_id:id,element_id:node.element_id,native_name:node.element,kind:node.kind})),
    inspection_counts:state.projection.inspection.counts,visible_elements_scope:'diagram_frames; declaration and retained-role occurrences use cse_list_inspection_occurrences',
    history:state.history,configuration_reviews:state.configuration_reviews,reconciliation:state.reconciliation,
    scope:'visible_saved_selection_never_replaces_retained_review_scope',
    claim:'application_context_not_host_qualification'});
}
function orderedOwnership(value) {
  return Array.isArray(value) ? value.map(orderedOwnership) : value && typeof value === 'object' ? Object.fromEntries(Object.keys(value).sort().map(key => [
    key,
    orderedOwnership(value[key])
  ])) : value;
}
function ownershipDraft() {
  return JSON.parse(byId('ownership-values').value || '{}');
}
function retainOwnershipDraft(value, changed = true) {
  byId('ownership-values').value = JSON.stringify(value);
  if (changed)
    byId('ownership-values').dispatchEvent(new Event('input', { bubbles: true }));
}
function resetOwnershipFields() {
  ownershipGeneration++;
  ownershipContext = null;
  ownershipOffset = 0;
  retainOwnershipDraft({}, false);
  byId('ownership-view-effects').replaceChildren();
  byId('ownership-destination').replaceChildren(new Option('Choose a captured native destination', ''));
  byId('ownership-context-status').textContent = 'Inspect source-bound owners before choosing a destination.';
  byId('ownership-destination-detail').textContent = '';
  byId('ownership-composition').textContent = '';
  byId('ownership-transition-label').hidden = true;
  byId('ownership-transition').checked = false;
  byId('ownership-previous').disabled = true;
  byId('ownership-next').disabled = true;
  byId('ownership-target').textContent = editingNode() ? 'Captured native declaration: ' + editingNode()[1].element + ' \xB7 revision ' + formRevision : '';
}
function ownershipTransition(draft) {
  const native = editingNode()?.[1].native;
  if (!draft.destination || editingNode()?.[1].kind !== 'PartUsage')
    return null;
  if (typeof native?.source_span?.authored_reference !== 'boolean')
    throw Error('Native authored declaration form is unavailable; refresh the source-bound inspection.');
  const after = !native.source_span.authored_reference && [
    'PartDefinition',
    'PartUsage'
  ].includes(draft.destination.kind);
  return after === native.is_composite ? null : {
    before: native.is_composite,
    after
  };
}
function ownershipComposition() {
  try {
    const draft = ownershipDraft(), transition = ownershipTransition(draft);
    byId('ownership-transition-label').hidden = !transition;
    byId('ownership-transition').checked = draft.transition_ack === true;
    byId('ownership-composition').textContent = transition ? 'Native composition changes ' + transition.before + ' \u2192 ' + transition.after + '. The authored part/ref part form stays fixed.' : 'This choice does not change the declaration\u2019s native composite value.';
  } catch (error) {
    byId('ownership-composition').textContent = error.message;
  }
}
function ownershipOptions() {
  const select = byId('ownership-destination'), draft = ownershipDraft();
  select.replaceChildren(new Option('Choose a captured native destination', ''));
  for (const row of ownershipContext?.destinations || []) {
    const option = new Option((row.native_name || 'Unnamed namespace') + ' \xB7 ' + row.target.kind + ' \xB7 ' + row.target.file, JSON.stringify(row.target));
    option.dataset.nativeName = row.native_name || '';
    select.append(option);
  }
  const wanted = draft.destination && JSON.stringify(draft.destination);
  if (wanted && ![...select.options].some(option => option.value === wanted)) {
    const option = new Option('Retained destination \xB7 ' + (draft.destination_name || draft.destination.identity) + ' \xB7 review its original bundle', wanted);
    option.dataset.nativeName = draft.destination_name || '';
    select.append(option);
  }
  select.value = wanted || '';
  byId('ownership-destination-detail').textContent = draft.destination ? 'Captured ' + draft.destination.kind + ' identity: ' + draft.destination.identity + ' \xB7 source ' + draft.destination.file + ' \xB7 bundle ' + draft.destination.bundle_sha256 : '';
  ownershipComposition();
}
async function loadOwnershipContext(offset = 0, viewId = null) {
  if (busy || unknown || pending || !editingNode() || dirty && draftKind && draftKind !== 'reparent')
    return {
      outcome: 'refused',
      error: {
        code: 'retained_edit',
        detail: 'Resolve the existing edit before inspecting another ownership draft.'
      }
    };
  const ticket = ++ownershipGeneration, targetId = editTargetId, revision = formRevision, bundle = state.projection.bundle_sha256;
  busy = true;
  controls();
  byId('ownership-context-status').textContent = 'Reading source-bound owners and affected views\u2026';
  try {
    const result = await api('/api/ownership-context', {
      element_id: targetId,
      expected_revision: revision,
      expected_bundle_sha256: bundle,
      offset,
      limit: 25,
      view_id: viewId
    });
    if (ticket !== ownershipGeneration || editTargetId !== targetId || formRevision !== revision || state.projection.bundle_sha256 !== bundle)
      return { outcome: 'superseded' };
    ownershipContext = result;
    ownershipOffset = offset;
    byId('ownership-context-status').textContent = 'Revision ' + result.revision + ' \xB7 ' + result.total_destinations + ' native destination/file choices \xB7 ' + result.affected_views.length + ' affected physical views.';
    byId('ownership-previous').disabled = offset === 0;
    byId('ownership-next').disabled = result.next_offset === null;
    const draft = ownershipDraft();
    if (!Array.isArray(draft.views)) {
      draft.views = result.affected_views.map(row => ({
        view_id: row.view_id,
        action: row.required_action === 'preserve_boundary_or_structure' ? 'preserve_structure' : '',
        parent_node: '',
        points_text: ''
      }));
      retainOwnershipDraft(draft, false);
    }
    ownershipOptions();
    renderOwnershipEffects();
    return {
      outcome: 'observed',
      context: clone(result)
    };
  } catch (error) {
    byId('ownership-context-status').textContent = error.message;
    return {
      outcome: 'refused',
      error: {
        code: error.code || 'ownership_context',
        detail: error.message
      }
    };
  } finally {
    busy = false;
    controls();
  }
}
function renderOwnershipEffects() {
  const container = byId('ownership-view-effects'), draft = ownershipDraft();
  container.replaceChildren();
  for (const impact of ownershipContext?.affected_views || []) {
    const row = draft.views.find(row => row.view_id === impact.view_id);
    if (!row)
      continue;
    const field = document.createElement('fieldset'), title = document.createElement('legend');
    title.textContent = impact.view_id + ' \xB7 ' + (impact.subject_node || 'subtree boundary');
    field.append(title);
    const text = document.createElement('p');
    text.textContent = 'Affected occurrences: ' + impact.affected_nodes.join(', ') + '. Incoming relationship: ' + (impact.incoming_edge || 'none \xB7 view boundary') + '.';
    field.append(text);
    if (impact.required_action === 'preserve_boundary_or_structure') {
      const p = document.createElement('p');
      p.textContent = 'Retain this view boundary and its existing structure explicitly; native bindings update by engineering identity.';
      field.append(p);
    } else {
      const label = document.createElement('label');
      label.textContent = 'Explicit view consequence';
      const action = document.createElement('select');
      for (const [value, name] of [
          [
            '',
            'Choose a consequence'
          ],
          [
            'reparent',
            'Retain subtree with the exact new owner frame and a specified route'
          ],
          [
            'remove_occurrences',
            'Remove these occurrences from this view only'
          ]
        ])
        action.append(new Option(name, value));
      action.value = row.action;
      action.onchange = () => {
        const value = ownershipDraft();
        value.views.find(v => v.view_id === impact.view_id).action = action.value;
        retainOwnershipDraft(value);
        renderOwnershipEffects();
      };
      label.append(action);
      field.append(label);
      const inspect = document.createElement('button');
      inspect.type = 'button';
      inspect.textContent = 'Inspect ' + impact.view_id + ' owner frames and routes';
      inspect.onclick = () => loadOwnershipContext(ownershipOffset, impact.view_id);
      field.append(inspect);
      if (ownershipContext.view_detail?.view_id === impact.view_id) {
        const detail = ownershipContext.view_detail, pre = document.createElement('pre');
        pre.style.cssText = 'white-space:pre-wrap;overflow-wrap:anywhere;max-height:360px;overflow:auto';
        pre.textContent = JSON.stringify({
          view_id: impact.view_id,
          nodes: Object.fromEntries(Object.entries(detail.projection.nodes).map(([id, node]) => [
            id,
            {
              element: node.element,
              element_id: node.element_id,
              parent: node.parent,
              box: detail.current_layout.nodes[id]
            }
          ])),
          routes: detail.current_layout.edges
        }, null, 2);
        field.append(pre);
        if (row.action === 'reparent') {
          const parentLabel = document.createElement('label');
          parentLabel.textContent = 'Exact destination owner occurrence';
          const parent = document.createElement('select');
          parent.append(new Option('Choose the native destination frame', ''));
          for (const [id, node] of Object.entries(detail.projection.nodes))
            if (node.element === draft.destination_name && !impact.affected_nodes.includes(id))
              parent.append(new Option(id + ' \xB7 ' + node.element, id));
          parent.value = row.parent_node;
          parent.onchange = () => {
            const value = ownershipDraft();
            value.views.find(v => v.view_id === impact.view_id).parent_node = parent.value;
            retainOwnershipDraft(value);
          };
          parentLabel.append(parent);
          field.append(parentLabel);
          const routeLabel = document.createElement('label');
          routeLabel.textContent = 'Ownership route (x,y per line; retained boxes stay fixed)';
          const points = document.createElement('textarea');
          points.rows = 5;
          points.cols = 32;
          points.value = row.points_text || '';
          points.oninput = () => {
            const value = ownershipDraft();
            value.views.find(v => v.view_id === impact.view_id).points_text = points.value;
            retainOwnershipDraft(value);
          };
          routeLabel.append(points);
          field.append(routeLabel);
        }
      }
      if (row.action === 'remove_occurrences') {
        const p = document.createElement('p');
        p.textContent = 'Only these diagram occurrences, their incoming routes and corresponding presentation entries are removed. All engineering declarations and UUIDs remain.';
        field.append(p);
      }
    }
    container.append(field);
  }
}
byId('ownership-load').onclick = () => loadOwnershipContext();
byId('ownership-previous').onclick = () => loadOwnershipContext(Math.max(0, ownershipOffset - 25));
byId('ownership-next').onclick = () => {
  if (ownershipContext?.next_offset !== null)
    loadOwnershipContext(ownershipContext.next_offset);
};
byId('ownership-destination').onchange = () => {
  const select = byId('ownership-destination'), draft = ownershipDraft();
  draft.destination = select.value ? JSON.parse(select.value) : null;
  draft.destination_name = select.selectedOptions[0]?.dataset.nativeName || null;
  draft.transition_ack = false;
  for (const row of draft.views || [])
    row.parent_node = '';
  retainOwnershipDraft(draft);
  ownershipOptions();
  renderOwnershipEffects();
};
byId('ownership-transition').onchange = () => {
  const draft = ownershipDraft();
  draft.transition_ack = byId('ownership-transition').checked;
  retainOwnershipDraft(draft);
};
function ownershipPoints(text) {
  const lines = text.split(/\r?\n/).filter(line => line.trim());
  if (lines.length < 2 || lines.length > 128)
    throw Error('Supply 2 through 128 route points.');
  return lines.map(line => {
    const pair = line.split(',');
    if (pair.length !== 2 || pair.some(value => !value.trim() || !Number.isFinite(Number(value))))
      throw Error('Each route point needs exactly two finite coordinates x,y.');
    return pair.map(Number);
  });
}
function previewOwnership() {
  try {
    const draft = ownershipDraft();
    if (!editingNode() || !draft.destination)
      throw Error('Choose a captured native destination.');
    const transition = ownershipTransition(draft);
    if (transition && !draft.transition_ack)
      throw Error('Review and acknowledge the displayed native composition transition.');
    const viewEffects = (draft.views || []).map(row => row.action === 'reparent' ? {
      view_id: row.view_id,
      action: row.action,
      parent_node: row.parent_node,
      points: ownershipPoints(row.points_text)
    } : {
      view_id: row.view_id,
      action: row.action
    });
    return previewChange(request('reparent', {
      element_id: editTargetId,
      destination: draft.destination,
      composition_transition: transition,
      view_effects: viewEffects,
      checked_bundle_sha256: null
    }), 'Native owner of ' + editingNode()[1].element + ' \u2192 ' + (draft.destination_name || 'Unnamed namespace') + ' \xB7 ' + draft.destination.file);
  } catch (error) {
    notice(error.message);
    return {
      outcome: 'refused',
      error: {
        code: error.code || 'ownership_input',
        detail: error.message
      }
    };
  }
}
function prepareOwnershipCandidateViews() {
  const select = byId('ownership-candidate-view');
  select.replaceChildren();
  if (pending?.request.operation !== 'reparent')
    return;
  for (const id of Object.keys(pending.preview.affected_views || {}))
    select.append(new Option(id, id));
  if ([...select.options].some(option => option.value === state.projection.id))
    select.value = state.projection.id;
  byId('ownership-candidate-status').textContent = 'Checked bundle ' + pending.request.checked_bundle_sha256 + '. Inspect every affected view and complete retained findings before saving.';
}
byId('ownership-candidate-view').onchange = () => {
  showCandidate(null);
  byId('ownership-candidate-status').textContent = 'Inspect this affected view to display its checked SVG.';
  controls();
};
byId('ownership-candidate-ack').onchange = () => {
  draftGeneration++;
  controls();
};
byId('ownership-show-candidate').onclick = async () => {
  if (busy || unknown || !pending || pending.stale || pending.request.operation !== 'reparent')
    return;
  const captured = pending, view = byId('ownership-candidate-view').value;
  if (!view)
    return;
  busy = true;
  controls();
  showCandidate(null);
  try {
    const result = await api('/api/preview-view', {
      request: captured.request,
      view_id: view
    });
    if (pending !== captured || unknown || byId('ownership-candidate-view').value !== view)
      return;
    if (result.candidate_bundle_sha256 !== captured.request.checked_bundle_sha256 || result.request_sha256 !== captured.preview.request_sha256 || result.view_id !== view)
      throw Error('Affected drawing does not match the captured candidate request.');
    const actual = [...new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(result.candidate_svg)))].map(v => v.toString(16).padStart(2, '0')).join('');
    if (pending !== captured || unknown || byId('ownership-candidate-view').value !== view)
      return;
    if (actual !== captured.preview.affected_views[view].candidate_svg_sha256)
      throw Error('Affected candidate SVG digest changed.');
    showCandidate(result.candidate_svg);
    byId('ownership-candidate-status').textContent = view + ' \xB7 checked unsaved bundle ' + result.candidate_bundle_sha256;
  } catch (error) {
    byId('ownership-candidate-status').textContent = error.message;
  } finally {
    busy = false;
    controls();
  }
};
function sourceHeaders() {
  return byId('source-mode').value === 'candidate' ? pending?.preview?.candidate_model_sources || [] : state?.model_sources || [];
}
function clearSourceRead() {
  sourceGeneration++;
  sourceReadBusy = false;
  sourceReadState = null;
  byId('source-text').textContent = '';
  byId('source-text').hidden = true;
  byId('source-status').textContent = 'Choose a source snapshot and file. Read chunks without changing the model or retained review scope.';
}
function sourceControls() {
  const mode = byId('source-mode'), select = byId('source-file');
  mode.querySelector('[value=candidate]').disabled = !pending;
  if (mode.value === 'candidate' && !pending)
    mode.value = 'saved';
  const headers = sourceHeaders(), key = JSON.stringify([
      mode.value,
      state?.commit,
      mode.value === 'candidate' ? pending?.preview?.request_sha256 : null,
      headers
    ]);
  if (key !== sourceOptionsKey) {
    const selected = select.value;
    sourceOptionsKey = key;
    clearSourceRead();
    select.replaceChildren();
    for (const row of headers)
      select.append(new Option(row.file + ' \xB7 ' + row.codepoints + ' codepoints', row.file));
    if ([...select.options].some(option => option.value === selected))
      select.value = selected;
  }
  byId('source-read').disabled = !state || !select.value || sourceReadBusy || unknown && mode.value === 'candidate';
  byId('source-next').disabled = !sourceReadState || sourceReadState.next_offset === null || sourceReadBusy || unknown && mode.value === 'candidate';
}
async function sourceHash(text) {
  return [...new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text)))].map(v => v.toString(16).padStart(2, '0')).join('');
}
async function readSource(next = false) {
  if (!state || sourceReadBusy)
    return;
  const mode = byId('source-mode').value, file = byId('source-file').value, header = sourceHeaders().find(row => row.file === file), captured = mode === 'candidate' ? pending : null;
  if (!header || mode === 'candidate' && (!captured || unknown))
    return;
  if (!next) {
    clearSourceRead();
    sourceReadState = {
      mode,
      file,
      text: '',
      next_offset: 0,
      header,
      commit: state.commit,
      request_sha256: captured?.preview?.request_sha256 || null,
      bundle_sha256: captured?.preview?.candidate_bundle_sha256 || state.projection.bundle_sha256
    };
  }
  const retained = sourceReadState;
  if (!retained || retained.next_offset === null)
    return;
  const ticket = sourceGeneration, commit = state.commit, offset = retained.next_offset;
  const current = () => ticket === sourceGeneration && sourceReadState === retained && state.commit === commit && byId('source-mode').value === mode && byId('source-file').value === file && (mode !== 'candidate' || pending === captured);
  sourceReadBusy = true;
  sourceControls();
  byId('source-status').textContent = 'Reading exact ' + mode + ' SysML\u2026';
  try {
    const response = await api('/api/source', {
      expected_revision: state.revision,
      expected_bundle_sha256: state.projection.bundle_sha256,
      request: captured?.request || null,
      file,
      offset,
      limit: 32768
    });
    if (!current())
      return;
    if (response.snapshot !== mode || response.base_commit !== commit || response.bundle_sha256 !== retained.bundle_sha256 || response.request_sha256 !== retained.request_sha256 || response.file !== file || response.file_sha256 !== header.sha256 || response.file_codepoints !== header.codepoints || response.offset !== offset || response.offset_units !== 'unicode_codepoints' || typeof response.text !== 'string')
      throw Error('Source response does not match the captured snapshot/file.');
    const count = [...response.text].length, end = offset + count;
    if (end > header.codepoints || response.next_offset !== (end < header.codepoints ? end : null))
      throw Error('Source page boundaries do not match the exact file.');
    const digest = await sourceHash(response.text);
    if (!current())
      return;
    if (digest !== response.chunk_sha256)
      throw Error('Source chunk bytes changed.');
    const text = retained.text + response.text;
    if (response.next_offset === null) {
      const complete = await sourceHash(text);
      if (!current())
        return;
      if (complete !== header.sha256)
        throw Error('Complete source bytes do not match their file digest.');
    }
    retained.text = text;
    retained.next_offset = response.next_offset;
    byId('source-text').textContent = text;
    byId('source-text').hidden = false;
    byId('source-status').textContent = (mode === 'candidate' ? 'Checked candidate snapshot' : 'Saved revision ' + response.revision) + ' \xB7 ' + file + ' \xB7 ' + end + '/' + header.codepoints + ' codepoints \xB7 ' + header.sha256 + (response.next_offset === null ? ' \xB7 complete exact file' : ' \xB7 more source remains');
    notifyContext();
  } catch (error) {
    if (current())
      byId('source-status').textContent = 'Source read unavailable: ' + error.message;
  } finally {
    if (current()) {
      sourceReadBusy = false;
      sourceControls();
    }
  }
}
byId('source-mode').onchange = () => {
  sourceOptionsKey = null;
  sourceControls();
};
byId('source-file').onchange = () => {
  clearSourceRead();
  sourceControls();
};
byId('source-read').onclick = () => readSource();
byId('source-next').onclick = () => readSource(true);

globalThis.cseWorkbench=Object.freeze({
  context:workbenchContext,
  subscribe(subscriber){if(typeof subscriber!=='function')throw TypeError('Supply a context listener.');contextSubscribers.add(subscriber);notifyContext();return()=>contextSubscribers.delete(subscriber);},
});
setInterval(async()=>{
  if(!initialized||!state||busy||gestureActive||polling)return;polling=true;
  try{const head=await api('/api/head');if(head.commit!==state.commit){if(busy||gestureActive||dirty||pending)notice('The project changed elsewhere. Your pending values are retained; refresh and review before another preview.');else await loadState(false,true);}}
  catch(error){notice('Refresh unavailable: '+error.message);}
  finally{polling=false;}
},1500);
start();
