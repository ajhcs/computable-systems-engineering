'use strict';
// The embedded reader remains the exact saved native artifact. This controller
// submits existing typed project operations; it supplies no engineering verdict.
const byId=id=>document.getElementById(id), frame=byId('view');
const uiSession=crypto.randomUUID();
let state, csrf, selectedId, selectedOccurrenceId, busy=false, dirty=false, pending=null, unknown=false, polling=false, ghost=null;
let formRevision, formCommit, restoredSelection, restoredNavigation, restoredInspection, restoredOccurrence, restoredInspectionOccurrence;
let editTargetId, editTargetOccurrenceId, editTargetName, draftGeneration=0, loadGeneration=0, gestureActive=false, frameReady=false, creationDraft=false, draftKind=null;
let chosenView=new URLSearchParams(location.search).get('view');
let removalCapture=null;
let frameMasterDraft=null,connectorStyleDraft=null,connectorOptionsKey,viewKeyDraft=null;
const checkedOperation=operation=>['reparent','delete','remove_occurrence'].includes(operation);
const presentationOperation=operation=>['set_layout','set_frame_master','set_connector_style','set_view_key','set_display_alias'].includes(operation);
const removalOperation=operation=>operation==='delete'||operation==='remove_occurrence';
const savedViewAvailable=()=>state?.view_available!==false;
let candidateSvg=null,candidateMode='readable',candidateFontGeneration=0;
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
    kind:'loopback',localArtifacts:true,viewSelection:true,
    rememberView(view){
      const address=new URL(location.href);
      address.searchParams.set('view',view);
      history.replaceState(null,'',address);
    },
    intentStorage:{getItem:key=>sessionStorage.getItem(key),setItem:(key,value)=>sessionStorage.setItem(key,value),removeItem:key=>sessionStorage.removeItem(key)},
    request:async({operation,payload,viewId})=>{
      const path={session:'/session',state:'/api/state',head:'/api/head',inspection:'/api/inspection',ownership_context:'/api/ownership-context',removal_context:'/api/removal-context',source:'/api/source',model_review:'/api/retained-review',catalog_search:'/api/catalog-search',catalog_inspect:'/api/catalog-inspect',catalog_selection:'/api/catalog-selection',preview_view:'/api/preview-view',preview:'/api/preview',apply:'/api/apply',receipt:'/api/receipt',artifact:'/api/artifact'}[operation];
      const options={credentials:'same-origin',cache:'no-store'};
      if(payload!==undefined)Object.assign(options,{method:'POST',headers:{'Content-Type':'application/json','X-CSE-CSRF':csrf||''},body:JSON.stringify(payload)});
      if(viewId)options.headers={...options.headers,'X-CSE-View':viewId};
      const response=await fetch(path,options);return{status:response.status,body:await response.json()};
    },openArtifact:openLoopbackArtifact,
  };
  const supplied=globalThis.cseCompositionHost;
  if(!supplied||supplied.version!=='cse-composition-host-1'||typeof supplied.kind!=='string'||!supplied.kind||typeof supplied.request!=='function'||
      !supplied.intentStorage||['getItem','setItem','removeItem'].some(name=>typeof supplied.intentStorage[name]!=='function')||
      supplied.openArtifact!==null&&typeof supplied.openArtifact!=='function')throw Error('Unsupported or incomplete physical-composition host provider.');
  return Object.freeze({kind:supplied.kind,localArtifacts:false,viewSelection:supplied.viewSelection===true,request:supplied.request.bind(supplied),
    rememberView:typeof supplied.rememberView==='function'?supplied.rememberView.bind(supplied):null,
    refreshIntervalMs:Number.isSafeInteger(supplied.refreshIntervalMs)&&supplied.refreshIntervalMs>=1500&&supplied.refreshIntervalMs<=60000
      ?supplied.refreshIntervalMs:1500,
    intentStorage:Object.freeze(Object.fromEntries(['getItem','setItem','removeItem'].map(name=>[name,supplied.intentStorage[name].bind(supplied.intentStorage)]))),
    openArtifact:supplied.openArtifact?.bind(supplied)||null,
    downloadCatalogSelection:typeof supplied.downloadCatalogSelection==='function'?supplied.downloadCatalogSelection.bind(supplied):null});
}
function notifyContext(){
  if(contextQueued||!contextSubscribers.size)return;
  contextQueued=true;queueMicrotask(()=>{contextQueued=false;for(const subscriber of contextSubscribers){
    const failed=()=>console.warn('CSE context subscriber failed; saved outcome is unchanged.');
    try{const result=subscriber(workbenchContext());if(result&&typeof result.then==='function')Promise.resolve(result).catch(failed);}catch(error){failed();}
  }});
}
const formKinds={'rename-form':'rename','display-alias-form':'set_display_alias','multiplicity-form':'multiplicity','typing-form':'typing','layout-form':'layout','restore-form':'restore','create-definition-form':'create_definition','create-usage-form':'create_usage','ownership-form':'reparent','removal-form':'removal','frame-master-form':'set_frame_master','connector-style-form':'set_connector_style','view-key-form':'set_view_key'};
const operationKind=operation=>({delete:'removal',remove_occurrence:'removal',set_layout:'layout',set_multiplicity:'multiplicity',set_types:'typing'}[operation]||operation);
const editableInputs=['display-alias','view-key-legend','connector-style-legend','frame-master-legend','removal-values','ownership-values','typing-values','rename-name','multiplicity-lower','multiplicity-upper','box-x','box-y','box-width','box-height','restore-target','create-name','create-short','create-placement','create-x','create-y','create-width','create-height','create-points','usage-name','usage-short','usage-type','usage-kind','usage-multiplicity','usage-lower','usage-upper','usage-placement','usage-x','usage-y','usage-width','usage-height','usage-points'];
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
async function loadOriginalDiagramFonts(doc){
  const faces=[...(doc?.fonts||[])];
  const expected=new Set(['DejaVu Sans:400','DejaVu Sans:700','DejaVu Sans Mono:400','DejaVu Sans Mono:700']);
  if(faces.length!==expected.size||faces.some(face=>!expected.delete(face.family.replace(/["']/g,'')+':'+face.weight)))
    throw Error('Original engineering fonts are missing.');
  let deadline;
  try{
    await Promise.race([Promise.all(faces.map(face=>face.load())),
      new Promise((_,reject)=>{deadline=setTimeout(()=>reject(Error('Original-font loading timed out.')),10000);})]);
  }finally{clearTimeout(deadline);}
}
function showCandidate(svg,mode='readable'){
  candidateSvg=svg;candidateMode=mode;
  const candidate=byId('candidate-diagram'), generation=++candidateFontGeneration;
  candidate.hidden=!svg;byId('candidate-navigation').hidden=!svg;
  candidate.style.visibility='hidden';
  if(presentationDrawingExpected()&&!unknown)byId('save').disabled=true;
  if(!svg){candidate.srcdoc='';return;}
  const parsed=new DOMParser().parseFromString(svg,'image/svg+xml').documentElement;
  const width=Number(parsed.getAttribute('width')),height=Number(parsed.getAttribute('height'));
  if(parsed.localName!=='svg'||!Number.isFinite(width)||!Number.isFinite(height)||width<=0||height<=0)
    throw Error('Invalid native candidate drawing');
  const scale=mode==='overview'?Math.min(1,candidate.clientWidth/width,candidate.clientHeight/height):1;
  byId('candidate-scale').textContent='Loading the original candidate fonts…';
  candidate.srcdoc='<!doctype html><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{margin:0;font:16px "DejaVu Sans",sans-serif}svg{display:block;width:'+width*scale+'px;height:'+height*scale+'px}</style><body data-candidate-generation="'+generation+'">'+svg;
}
byId('candidate-diagram').addEventListener('load',async event=>{
  const candidate=event.currentTarget, doc=candidate.contentDocument;
  if(!candidateSvg)return;
  if(!doc){
    byId('candidate-scale').textContent='Unsupported candidate drawing: this host prevents verification of the original fonts.';
    return;
  }
  if(doc.body?.dataset.candidateGeneration!==String(candidateFontGeneration))return;
  const generation=candidateFontGeneration;
  const current=()=>generation===candidateFontGeneration&&doc===candidate.contentDocument;
  try{
    await loadOriginalDiagramFonts(doc);
    if(!current())return;
    candidate.style.visibility='visible';
    byId('candidate-scale').textContent=candidateMode==='overview'?'Overview · use readable size for labels':'Readable size · 100%';
    if(presentationDrawingExpected())controls();
  }catch(error){
    if(!current())return;
    byId('candidate-scale').textContent='Unsupported candidate drawing: the original fonts could not load. Review the checked source and findings.';
  }
});
byId('candidate-overview').addEventListener('click',()=>showCandidate(candidateSvg,'overview'));
byId('candidate-readable').addEventListener('click',()=>showCandidate(candidateSvg,'readable'));
window.addEventListener('resize',()=>{if(candidateSvg&&candidateMode==='overview')showCandidate(candidateSvg,'overview');});
function controls(){
  sourceControls();
  frameMasterControls();
  connectorStyleControls();
  viewKeyControls();
  byId('display-alias-form').hidden=!editingNode()?.[1].frame_id;
  for(const input of byId('display-alias-form').elements)input.disabled=Boolean(draftKind&&draftKind!=='set_display_alias');
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
  byId('ownership-candidate-controls').hidden=!checkedOperation(pending?.request.operation);
  byId('restore-form').querySelectorAll('button,select').forEach(input=>input.disabled=
    busy||unknown||gestureActive||Boolean(pending)||!initialized||Boolean(draftKind&&draftKind!=='restore')||
    savedViewAvailable()&&!frameReady);
  byId('open-saved-view').disabled=busy||gestureActive||unknown||dirty||Boolean(pending)||!byId('saved-view-picker').value;
  renderRemovalControls();
  byId('save').disabled=busy||!pending||Boolean(pending.stale)||(!frameReady&&savedViewAvailable()&&!unknown)||!presentationDrawingReady()||(!unknown&&checkedOperation(pending?.request.operation)&&!byId('ownership-candidate-ack').checked);
  byId('ownership-candidate-ack').disabled=busy||unknown;
  byId('ownership-show-candidate').disabled=busy||unknown||Boolean(pending?.stale)||!byId('ownership-candidate-view').value;
  byId('save').textContent=unknown?'Retry save with the same request ID':'Save change';
  byId('discard').disabled=busy||unknown;
  byId('refresh').disabled=busy||gestureActive;
  byId('preview').hidden=!pending;
  if(!pending&&candidateSvg)showCandidate(null);
  if(pending)byId('pending-indicator').textContent=unknown?'Unacknowledged save · retain this exact request':pending.stale?'Stale candidate · current saved model is separate':'Unsaved change · the saved revision remains authoritative';
  byId('return-target').hidden=!different;byId('return-target').disabled=busy||gestureActive||!frameReady||!editingNode();
  byId('edit-selected').hidden=!different;
  byId('edit-selected').disabled=busy||unknown||Boolean(pending);
  byId('discard-draft').hidden=!dirty||Boolean(pending);
  byId('discard-draft').disabled=busy||unknown;
  notifyContext();
}
async function api(path,body,requestDigest,routeView=chosenView){
  if(providerError)throw providerError;
  const operation={'/session':'session','/api/state':'state','/api/head':'head','/api/inspection':'inspection','/api/ownership-context':'ownership_context','/api/removal-context':'removal_context','/api/source':'source','/api/retained-review':'model_review','/api/catalog-search':'catalog_search','/api/catalog-inspect':'catalog_inspect','/api/catalog-selection':'catalog_selection','/api/preview-view':'preview_view','/api/preview':'preview','/api/apply':'apply','/api/receipt':'receipt'}[path];
  if(!operation)throw Error('Unsupported physical-composition operation.');
  const response=await provider.request({operation,payload:body,...(provider.viewSelection&&routeView?{viewId:routeView}:{})}),result=response?.body;
  if(!Number.isInteger(response?.status)||response.status<100||response.status>599||!result||typeof result!=='object'||Array.isArray(result))throw Error('Invalid physical-composition transport response.');
  if(response.status<200||response.status>=300){const error=new Error(result.error?.detail||'Request failed');error.code=result.error?.code;error.definitiveRefusal=result.error?.definitive_refusal===true;throw error;}
  if(operation==='receipt'&&!/^[a-f0-9]{64}$/.test(result.request_sha256||''))throw Error('The exact native request digest was not received.');
  if(operation==='apply'||operation==='receipt'&&result.receipt!==null){
    const receipt=result.receipt;
    if(!receipt||receipt.request_id!==body.request_id||receipt.operation!==body.operation||receipt.revision!==body.expected_revision+1||
        receipt.project_id!==state.projection.project_id||receipt.request_sha256!==(operation==='receipt'?result.request_sha256:requestDigest)||
        typeof receipt.commit!=='string'||!/^[a-f0-9]{40}$/.test(receipt.commit)||
        body.operation==='restore'&&receipt.restored_from_revision!==body.target_revision||
        checkedOperation(body.operation)&&receipt.bundle_sha256!==body.checked_bundle_sha256)
      throw Error('A matching durable transaction receipt was not received.');
  }
  return result;
}
function selectedNode(){const rows=state?.projection.inspection.occurrences,node=rows&&Object.hasOwn(rows,selectedOccurrenceId)?rows[selectedOccurrenceId]:null;return node&&node.element_id===(selectedId||null)?[selectedOccurrenceId,node]:undefined;}
function editingNode(){const rows=state?.projection.inspection.occurrences,node=rows&&Object.hasOwn(rows,editTargetOccurrenceId)?rows[editTargetOccurrenceId]:null;return editTargetId&&node?.element_id===editTargetId?[editTargetOccurrenceId,node]:undefined;}
function savedDisplayAlias(node){
  const aliases=state?.display_aliases;
  return node.frame_id&&aliases&&Object.hasOwn(aliases,node.frame_id)?aliases[node.frame_id]:null;
}
function showFields(force=false){
  const found=selectedNode();
  if(!found)return;
  const [id,node]=found;
  byId('selected').textContent='Selected saved element: '+node.element+' · revision '+state.revision;
  if(force||!dirty&&!pending){
    editTargetId=selectedId||null;editTargetOccurrenceId=id;editTargetName=node.element;
    byId('rename-name').value=node.native?.name||'';
    byId('display-alias').value=savedDisplayAlias(node)??'';
    setTypingRows((node.native?.types||[]).map(name=>({type_id:typeDefinitions().find(row=>row.element===name)?.element_id||null,native_name:name})));
    const quantity=node.native?.multiplicity;
    for(const bound of ['lower','upper'])byId('multiplicity-'+bound).value=node.kind==='PartUsage'&&['default','literal'].includes(quantity?.status)?quantity[bound]:'';
    for(const field of ['x','y','width','height'])byId('box-'+field).value=node.frame_id?state.layout.nodes[node.frame_id][field]:'';
    formRevision=state.revision;formCommit=state.commit;
    resetOwnershipFields();resetRemovalFields();
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
const validSha256=value=>typeof value==='string'&&/^[a-f0-9]{64}$/.test(value);
const sameFields=(first,second)=>JSON.stringify(orderedOwnership(first))===JSON.stringify(orderedOwnership(second));
async function checkCandidateDrawing(svg,digest){
  if(typeof svg!=='string'||!svg||!validSha256(digest)||await sourceHash(svg)!==digest)
    throw Error('The displayed drawing does not match the checked candidate.');
}
async function checkCandidateEffects(checked,metadata,svg){
  if(metadata.candidate_bundle_sha256!==checked.checked_bundle_sha256)
    throw Error('The preview does not match the checked bundle.');
  const effects=checked.view_effects, affected=metadata.affected_views;
  if(!affected||typeof affected!=='object'||Array.isArray(affected)||Object.keys(affected).length!==effects.length)
    throw Error('The affected views do not match the checked request.');
  for(const effect of effects){
    const row=Object.hasOwn(affected,effect.view_id)?affected[effect.view_id]:null;
    if(!row||!sameFields(row.view_effect,effect)||
        (effect.action==='close_view'?row.candidate_svg_sha256!==null:!validSha256(row.candidate_svg_sha256)))
      throw Error('An affected view does not match the checked request.');
  }
  if(removalOperation(checked.operation)){
    const reported=metadata.removal?.views;
    const keys=['view_id','action','node_ids','edge_ids'];
    if(!Array.isArray(reported)||reported.length!==effects.length||
      !sameFields(reported.map(row=>Object.fromEntries(keys.map(name=>[name,row[name]]))).sort((a,b)=>a.view_id.localeCompare(b.view_id)),
                  [...effects].sort((a,b)=>a.view_id.localeCompare(b.view_id))))
      throw Error('The removal summary does not match the checked view effects.');
  }
  const selected=state.projection.id;
  const current=Object.hasOwn(affected,selected)?affected[selected]:null;
  const close=current?.view_effect.action==='close_view';
  if(removalOperation(checked.operation)&&metadata.current_view_closed!==close)
    throw Error('The current view closure does not match the checked request.');
  if(close||!current&&!savedViewAvailable()){
    if(svg!==null||metadata.candidate_svg_sha256!==null)
      throw Error('The checked candidate has no drawing for the current view.');
    return;
  }
  const digest=metadata.candidate_svg_sha256;
  if(current&&current.candidate_svg_sha256!==digest)
    throw Error('The current view digest does not match its checked effect.');
  await checkCandidateDrawing(svg,digest);
}
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
    if(checkedOperation(change.operation)&&(JSON.stringify(orderedOwnership({...checked,checked_bundle_sha256:null}))!==JSON.stringify(orderedOwnership(change))||!/^[a-f0-9]{64}$/.test(checked.checked_bundle_sha256||'')))throw Error('The preview returned a different request or missing candidate binding.');
    if(checkedOperation(change.operation))await checkCandidateEffects(checked,metadata,candidate_svg);
    if(change.operation==='restore'){
      const views=metadata.candidate_available_views;
      if(metadata.restored_from_revision!==change.target_revision||!Array.isArray(views)||
          views.some(view=>typeof view!=='string'||!/^[A-Za-z_][A-Za-z0-9_.-]{0,127}$/.test(view))||
          new Set(views).size!==views.length)
        throw Error('The preview does not match the requested saved revision and views.');
      if(views.includes(state.projection.id))
        await checkCandidateDrawing(candidate_svg,metadata.candidate_svg_sha256);
      else if(candidate_svg!==null||metadata.candidate_svg_sha256!==null)
        throw Error('The saved revision does not contain the requested drawing.');
    }
    if(change.operation==='set_layout'){
      if(!sameFields(metadata.candidate_layout,change.layout))
        throw Error('The preview does not match the requested geometry.');
      await checkCandidateDrawing(candidate_svg,metadata.candidate_svg_sha256);
    }
    if(change.operation==='set_frame_master'){
      if(!sameFields(metadata.frame_artwork,frameMasterBinding(change)))
        throw Error('The preview does not match the requested frame artwork.');
      if(change.style&&!sameFields(metadata.frame_style,change.style))
        throw Error('The preview does not match the requested frame swatches and alignment.');
      await checkCandidateDrawing(candidate_svg,metadata.candidate_svg_sha256);
    }
    if(change.operation==='set_connector_style'){
      if(!sameFields(metadata.connector_style,connectorStyleBinding(change)))
        throw Error('The preview does not match the requested connector and swatch.');
      await checkCandidateDrawing(candidate_svg,metadata.candidate_svg_sha256);
    }
    if(change.operation==='set_view_key'){
      if(!sameFields(metadata.view_key,viewKeyBinding(change)))
        throw Error('The preview does not match the requested local key.');
      await checkCandidateDrawing(candidate_svg,metadata.candidate_svg_sha256);
    }
    if(change.operation==='set_display_alias'){
      if(!sameFields(metadata.display_alias,displayAliasBinding(change)))
        throw Error('The preview does not match the requested view label.');
      await checkCandidateDrawing(candidate_svg,metadata.candidate_svg_sha256);
    }
    pending={request:checked,request_view_id:state.projection.id,description,preview:metadata,stale:false};
    byId('ownership-candidate-ack').checked=false;
    prepareOwnershipCandidateViews();
    const affected=result.preview.affected_views||{},showCurrent=change.operation!=='reparent'||!Object.keys(affected).length||Object.hasOwn(affected,state.projection.id);
    showCandidate(showCurrent?candidate_svg||null:null);
    if(!showCurrent)byId('ownership-candidate-status').textContent='The current saved view does not show the moved declaration. Inspect the selected affected candidate view explicitly.';
    const reviewLines=result.preview.configuration_reviews.map(review=>review.file+': '+review.report.status);
    byId('summary').textContent=description+'\nBase revision: '+result.preview.base_revision+'\nChanged model files: '+(result.preview.changed_model_files.join(', ')||'none')+'\nChanged companion files: '+(result.preview.changed_linked_records.join(', ')||'none')+(reviewLines.length?'\nRetained configuration reviews:\n'+reviewLines.join('\n'):'');
    if(change.operation==='restore'){
      const views=metadata.candidate_available_views;
      byId('summary').textContent+='\nViews in revision '+change.target_revision+': '+(views.join(', ')||'none');
      if(!views.includes(state.projection.id))byId('summary').textContent+='\nThis revision has no drawing for '+state.projection.id+'.';
    }
    showConfigurationReviews('candidate',result.preview.configuration_reviews,
      'Candidate from saved revision '+result.preview.base_revision,
      result.preview.candidate_bundle_sha256 ?? checked.checked_bundle_sha256);
    const edited=result.preview.edited_element;if(edited)byId('summary').textContent+='\nCandidate native declaration: '+edited.element+'\nNative owner: '+(edited.native.owner||(edited.native.owner_kind==='Namespace'?'Unnamed namespace':'Unresolved'))+(edited.kind==='PartDefinition'?'\nDeclared supertypes: '+((edited.native.supertypes||[]).join(', ')||'None'):'\nExplicit types: '+((edited.native.types||[]).join(', ')||'No explicit typing'));
    if(result.preview.removal)appendRemovalSummary(result.preview);
    if(result.preview.ownership_change)byId('summary').textContent+='\nOwnership/source/view consequences:\n'+JSON.stringify(result.preview.ownership_change,null,2);
    const created=result.preview.created_element;if(created){const native=created.native;byId('summary').textContent+='\nNew native declaration: '+created.element+'\nNative owner: '+native.owner;if(created.kind==='PartUsage')byId('summary').textContent+='\nDeclaration kind: '+(native.is_composite?'composite part':'reference part')+'\nExplicit type: '+(native.type||'none')+'\nMultiplicity: '+native.multiplicity.status+' ['+native.multiplicity.lower+'..'+native.multiplicity.upper+']';}
    byId('pending-indicator').textContent='Unsaved change · the saved revision remains authoritative';
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
function downloadLocalFile({name,mediaType,text}){
  const url=URL.createObjectURL(new Blob([text],{type:mediaType}));
  const link=document.createElement('a');
  link.href=url;link.download=name;
  document.body.append(link);link.click();link.remove();
  setTimeout(()=>URL.revokeObjectURL(url),1000);
}
async function openLoopbackArtifact(artifact){
  const project=state.projection.project_id;
  const {capturedArtifact,checkedArtifactFile}=await import('/artifact-bytes.mjs');
  const capture=capturedArtifact(state.projection.id,false,artifact);
  const response=await provider.request({operation:'artifact',payload:capture.payload,viewId:capture.view_id});
  if(response.body?.error){
    const {code,detail}=response.body.error;
    throw Object.assign(Error(detail),{code});
  }
  downloadLocalFile(await checkedArtifactFile(response,project,capture));
  return {isError:false};
}
function savedArtifact(kind){
  return {kind,commit:state.commit,revision:state.revision,view_id:state.projection.id,
    bundle_sha256:state.projection.bundle_sha256,expected_sha256:state.artifact_hashes?.[kind]};
}
function canTransferArtifact(artifact){
  return Boolean(provider.openArtifact&&/^[a-f0-9]{64}$/.test(artifact.expected_sha256||''));
}
async function transferSavedArtifact(artifact){
  if(!canTransferArtifact(artifact)){
    const error=new Error('This saved view has no source-bound transfer for the requested artifact.');
    error.code='artifact_unavailable';
    throw error;
  }
  const current=savedArtifact(artifact.kind);
  if(Object.keys(current).some(key=>current[key]!==artifact[key])){
    const error=new Error('The saved view changed. Read its context again before exporting.');
    error.code='stale_context';
    throw error;
  }
  notice('Verifying the saved artifact…');
  try{
    const result=await provider.openArtifact(artifact);
    if(typeof result?.isError!=='boolean')throw Error('A transfer outcome was not returned.');
    notice(result.isError?'Artifact transfer was refused or cancelled.':'Artifact transfer requested.');
    return {outcome:result.isError?'transfer_refused_or_cancelled':'transfer_requested',artifact};
  }catch(error){
    notice('Artifact transfer unavailable: '+error.message);
    throw error;
  }
}
frame.addEventListener('load',async()=>{
  const doc=frame.contentDocument;if(!doc?.querySelector('#cse-data'))return;
  let saved;try{saved=JSON.parse(doc.querySelector('#cse-data').textContent);}catch(error){return;}
  if(saved.commit!==state.commit||saved.revision!==state.revision)return;
  const ticket=viewGeneration,commit=state.commit,revision=state.revision,source=frame.srcdoc;
  const current=()=>ticket===viewGeneration&&doc===frame.contentDocument&&source===frame.srcdoc&&commit===state.commit&&revision===state.revision;
  viewStatus='checking_fonts';frameReady=false;frame.style.visibility='hidden';controls();
  for(const link of doc.querySelectorAll('a')){
    const kind=link.getAttribute('href');
    const artifact=savedArtifact(kind);
    link.removeAttribute('href');
    if(!canTransferArtifact(artifact)){
      link.setAttribute('aria-disabled','true');
      link.title='This host does not support source-bound artifact transfer.';
      continue;
    }
    link.href='#';
    link.addEventListener('click',async event=>{
      event.preventDefault();
      try {
        await transferSavedArtifact(artifact);
      } catch(error) {
        notice('Artifact transfer unavailable: '+error.message);
      }
    });
  }
  try{
    await loadOriginalDiagramFonts(doc);
  }catch(error){
    if(!current())return;
    viewStatus='unsupported_fonts';const drawing=doc.querySelector('.diagram');if(drawing)drawing.style.display='none';frame.style.visibility='visible';
    notice('Unsupported view: the original engineering fonts could not load. The saved model remains available; this drawing is not qualified.');controls();return;
  }
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
  if(provider.viewSelection&&chosenView&&result.state.projection.id!==chosenView)throw Error('The saved response does not match the selected view.');
  state=result.state;csrf=result.csrf;updateSavedViews();
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
  frameReady=false;viewGeneration++;frame.style.visibility='hidden';
  byId('edits').hidden=!savedViewAvailable();
  frame.hidden=!savedViewAvailable();
  viewStatus=savedViewAvailable()?'loading':'view_unavailable';
  frame.srcdoc=result.view_html||'';
  if(!savedViewAvailable()){
    selectedId=null;selectedOccurrenceId=null;
    byId('selected').textContent='No physical drawing is open.';
    byId('edit-target').textContent='';
    if(!preserve){editTargetId=null;editTargetOccurrenceId=null;editTargetName=null;resetRemovalFields();}
  }
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
function displayAliasBinding({view_id,node_id,element_id,alias}){
  return {view_id,node_id,element_id,alias};
}
function previewDisplayAlias(){
  const node=editingNode()?.[1];
  if(!node?.frame_id)return{outcome:'refused',error:{code:'target',detail:'Select a saved physical frame.'}};
  const fields={view_id:state.projection.id,node_id:node.frame_id,element_id:node.element_id,alias:byId('display-alias').value||null};
  return previewChange(request('set_display_alias',fields),'Display alias · '+node.element);
}
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
byId('display-alias-form').addEventListener('submit',event=>{event.preventDefault();void previewDisplayAlias();});
byId('rename-form').addEventListener('submit',event=>{event.preventDefault();previewRename();});
byId('create-usage-form').addEventListener('submit',event=>{event.preventDefault();previewCreateUsage();});
byId('create-definition-form').addEventListener('submit',event=>{event.preventDefault();previewCreateDefinition();});
byId('ownership-form').addEventListener('submit',event=>{event.preventDefault();previewOwnership();});
byId('typing-form').addEventListener('submit',event=>{event.preventDefault();previewTyping();});
byId('multiplicity-form').addEventListener('submit',event=>{event.preventDefault();previewMultiplicity();});
byId('layout-form').addEventListener('submit',event=>{event.preventDefault();previewLayout();});
byId('restore-form').addEventListener('submit',event=>{event.preventDefault();previewRestore();});
function retainFormInput(event){if(event.target.id==='drag-action')return;draftKind=formKinds[event.target.closest('form')?.id]||draftKind;creationDraft=['create_definition','create_usage'].includes(draftKind);draftGeneration++;dirty=true;if(pending&&!unknown){pending=null;removeGhost();}controls();}
byId('edits').addEventListener('input',retainFormInput);
byId('restore-form').addEventListener('input',retainFormInput);
function discard(){if(unknown||busy)return;draftGeneration++;pending=null;dirty=false;creationDraft=false;draftKind=null;removeGhost();showFields(true);notice('Pending values discarded. Saved state is unchanged.');controls();}
byId('discard').addEventListener('click',discard);
byId('discard-draft').addEventListener('click',discard);
byId('edit-selected').addEventListener('click',discard);
byId('return-target').addEventListener('click',()=>{const found=editingNode();if(!found)return;frame.contentWindow.cseReaderSelection.select(found[0],{reveal:true});selectionChanged();const input=byId({create_definition:'create-name',create_usage:'usage-name',multiplicity:'multiplicity-lower',typing:'typing-add',reparent:'ownership-load',layout:'box-x',restore:'restore-target',removal:'remove-diagram',set_frame_master:'frame-master-legend',set_connector_style:'connector-style-swatch',set_view_key:'view-key-legend',set_display_alias:'display-alias'}[draftKind]||'rename-name');if(draftKind==='set_frame_master')byId('catalog-panel').open=true;if(draftKind==='set_connector_style')byId('connector-style-panel').open=true;if(draftKind==='set_view_key')byId('view-key-panel').open=true;input.focus({preventScroll:true});input.scrollIntoView({block:'nearest',inline:'nearest'});});
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
  if(!pending||busy||gestureActive||pending.stale||!presentationDrawingReady()||!unknown&&checkedOperation(pending.request.operation)&&!byId('ownership-candidate-ack').checked)return{outcome:'refused',error:{code:'save_unavailable',detail:'Inspect and preview a current change before saving.'}};
  const savedRequest=pending.request;
  const requestView=pending.request_view_id;
  if(requestView!==state.projection.id&&!provider.viewSelection){
    const detail='Reopen '+requestView+' to retry this retained save.';
    notice(detail);
    return{outcome:'not_sent',request:clone(savedRequest),error:{code:'view_unavailable',detail}};
  }
  draftGeneration++;
  busy=true;controls();notice('Saving the checked request…');
  let acknowledged=null,dispatched=false;const wasUnknown=unknown;
  try{
    // Native preview/lookup supplies the canonical digest. Reimplementing its
    // JSON number encoding in a browser would make valid layout receipts drift.
    let digest=pending.preview?.request_sha256;
    if(!/^[a-f0-9]{64}$/.test(digest||'')){const lookup=await api('/api/receipt',savedRequest);digest=lookup.request_sha256;pending.preview={...pending.preview,request_sha256:digest};}
    await provider.intentStorage.setItem(key(),JSON.stringify({request:savedRequest,request_view_id:requestView,selectedId,selectedOccurrenceId,editTargetId,editTargetOccurrenceId,editTargetName,draftKind,description:pending.description,
      request_sha256:digest,baseCommit:formCommit,fields:Object.fromEntries(editableInputs.map(id=>[id,byId(id).value]))}));
    dispatched=true;
    const result=await api('/api/apply',savedRequest,digest,requestView);
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
    if(access){await api('/session',{access});history.replaceState(null,'',location.pathname+location.search);}
    await loadState(false,false,true);initialized=true;
    if(!unknown)notice(savedViewAvailable()?'Select a saved element to inspect or edit.':'Open an available view or inspect or restore the saved project.');
    return{outcome:'loaded',revision:state.revision,commit:state.commit};
  }catch(error){notice(error.message);return{outcome:'unavailable',error:{code:error.code||'initialization',detail:error.message}};}
  finally{busy=false;controls();}
}
function restoreIntent(saved){
    if(saved!==null&&typeof saved!=='string')throw Error('Invalid pending-intent storage response.');
    if(saved){
      const entry=JSON.parse(saved);
      const originView=entry.request_view_id??entry.request.layout?.view??entry.request.view_id??state.projection.id;
      if(typeof originView!=='string'||!/^[A-Za-z_][A-Za-z0-9_.-]{0,127}$/.test(originView))
        throw Error('The retained save has an invalid physical view.');
      pending={request:entry.request,request_view_id:originView,description:entry.description,stale:false,preview:entry.request_sha256?{request_sha256:entry.request_sha256}:undefined};
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
      if(!entry.fields&&entry.request.operation==='set_display_alias')byId('display-alias').value=entry.request.alias??'';
      if(!entry.fields&&entry.request.operation==='rename')byId('rename-name').value=entry.request.new_name;
      if(entry.request.operation==='set_frame_master'){
        frameMasterDraft=frameMasterBinding(entry.request);
        byId('frame-master-legend').value=entry.request.legend?.join('\n')||'';
        setFrameMasterStyle(entry.request.style||state.frame_styles?.[entry.request.node_id]);
      }
      if(entry.request.operation==='set_connector_style')beginConnectorStyle(entry.request);
      if(entry.request.operation==='set_view_key')beginViewKey(entry.request);
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
  const hiddenFrames=new Set(navigation?.hidden_node_ids);
  return clone({ready:frameReady&&initialized,host_transport:provider?.kind||'unavailable',view_status:viewStatus,notice:byId('notice').textContent,last_acknowledged_receipt:lastReceipt,
    guard:{project_id:state.projection.project_id,view_id:state.projection.id,ui_session_id:uiSession,
      model_revision:state.revision,commit:state.commit,bundle_sha256:state.projection.bundle_sha256,
      interaction_revision:draftGeneration,selected_element_id:found?.[1].element_id||null,
      selected_occurrence_id:found?.[0]||null,editing_element_id:editTargetId||null,editing_occurrence_id:editTargetOccurrenceId||null,
      navigation_revision:navigation?.revision||0,viewport_mode:navigation?.mode||'readable',viewport_left:navigation?.scroll_left||0,viewport_top:navigation?.scroll_top||0},
    navigation,
    busy,gesture_active:gestureActive,has_form_draft:dirty,draft_kind:draftKind,unconfirmed_save:unknown,
    selection:found?{occurrence_id:found[0],...found[1],display_label:found[1].frame_id?state.display_labels[found[1].frame_id]:found[1].native?.name||found[1].element,display_alias:savedDisplayAlias(found[1]),box:found[1].frame_id?state.layout.nodes[found[1].frame_id]:null}:null,
    editing_target:editTargetId?{element_id:editTargetId,occurrence_id:editTargetOccurrenceId,native_name:target?.[1].element||editTargetName,present:Boolean(target),
      base_revision:formRevision,base_commit:formCommit,declared_name:byId('rename-name').value,
      multiplicity:Object.fromEntries(['lower','upper'].map(field=>[field,byId('multiplicity-'+field).value])),
      box:Object.fromEntries(['x','y','width','height'].map(field=>[field,byId('box-'+field).value]))}:null,
    model_sources:state.model_sources,
    catalog_selection:catalogSelection,
    saved_frame_master:state.frame_masters?.[found?.[1].frame_id]||null,
    saved_frame_style:state.frame_styles?.[found?.[1].frame_id]||null,
    appearance_palette:state.appearance_palette||null,
    view_key:state.view_key||null,
    view_key_draft:draftKind==='set_view_key'?{...viewKeyDraft,legend:appearanceLegend('view-key-legend')}:null,
    selected_connector:observedConnector(byId('connector-style-edge').value),
    connector_styles:state.connector_styles||{},
    connector_style_draft:draftKind==='set_connector_style'?{
      ...connectorStyleDraft,swatch:byId('connector-style-swatch').value,legend:byId('connector-style-legend').value,
    }:null,
    artwork_placement_draft:draftKind==='set_frame_master'?{...frameMasterDraft,legend:byId('frame-master-legend').value,style:frameMasterStyle()}:null,
    source_inspection:sourceReadState?{snapshot:sourceReadState.mode,file:sourceReadState.file,bundle_sha256:sourceReadState.bundle_sha256,request_sha256:sourceReadState.request_sha256,loaded_codepoints:[...sourceReadState.text].length,next_offset:sourceReadState.next_offset}:null,
    pending_change:pending?{...pending,request:clone(pending.request)}:null,
    available_views:state.available_views||[state.projection.id],view_available:savedViewAvailable(),
    removal_draft:removalCapture?{operation:removalCapture.operation,element_id:removalCapture.impact.element_id,
      view_id:removalCapture.impact.view_id||null,node_id:removalCapture.impact.node_id||null,latest_values:byId('removal-values').value}:null,
    ownership_draft:{raw_values:byId('ownership-values').value,candidate_reviewed:byId('ownership-candidate-ack').checked},
    typing_draft:{rows:typingRows().map(row=>({...row,available:Boolean(row.type_id&&typeDefinitions().some(def=>def.element_id===row.type_id))}))},
    usage_creation_draft:{declared_name:byId('usage-name').value,short_id:byId('usage-short').value||null,type_id:byId('usage-type').value||null,type_available:!byId('usage-type').value||state.projection.inspection.declarations.some(id=>state.projection.inspection.occurrences[id].element_id===byId('usage-type').value),is_composite:byId('usage-kind').value==='composite',multiplicity_mode:byId('usage-multiplicity').value,multiplicity:Object.fromEntries(['lower','upper'].map(key=>[key,byId('usage-'+key).value])),placement_mode:byId('usage-placement').value,box:Object.fromEntries(['x','y','width','height'].map(key=>[key,byId('usage-'+key).value])),route_text:byId('usage-points').value},
    creation_draft:{declared_name:byId('create-name').value,short_id:byId('create-short').value||null,placement_mode:byId('create-placement').value,
      box:Object.fromEntries(['x','y','width','height'].map(key=>[key,byId('create-'+key).value])),route_text:byId('create-points').value},
    restoration_target_revision:Number(byId('restore-target').value)||null,
    visible_elements:navigation?Object.entries(state.projection.nodes).filter(([id])=>!hiddenFrames.has(id))
      .map(([id,node])=>({occurrence_id:id,element_id:node.element_id,native_name:node.element,kind:node.kind})):[],
    inspection_counts:state.projection.inspection.counts,visible_elements_scope:'unfolded_diagram_frames; use cse_list_inspection_occurrences for all saved occurrences',
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
  if (!checkedOperation(pending?.request.operation))
    return;
  for (const id of Object.keys(pending.preview.affected_views || {}))
    select.append(new Option(id, id));
  if ([...select.options].some(option => option.value === state.projection.id))
    select.value = state.projection.id;
  byId('candidate-review-label').textContent=removalOperation(pending.request.operation)?'I reviewed this removal, affected views and retained configuration findings.':'I reviewed the ownership change and all affected view consequences for this exact candidate.';
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
  if (busy || unknown || !pending || pending.stale || !checkedOperation(pending.request.operation))
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
    const expected=captured.preview.affected_views[view];
    if(expected.view_effect.action==='close_view'){
      if(result.closed!==true||result.candidate_svg!==null)
        throw Error('View closure does not match the checked candidate.');
      byId('ownership-candidate-status').textContent=view+' closes in this exact candidate.';
      return;
    }
    if(result.closed!==undefined&&result.closed!==false)
      throw Error('The checked candidate requires a drawing for this view.');
    await checkCandidateDrawing(result.candidate_svg,expected.candidate_svg_sha256);
    if (pending !== captured || unknown || byId('ownership-candidate-view').value !== view)
      return;
    showCandidate(result.candidate_svg);
    byId('ownership-candidate-status').textContent = view + ' \xB7 checked unsaved bundle ' + result.candidate_bundle_sha256;
  } catch (error) {
    byId('ownership-candidate-status').textContent = error.message;
  } finally {
    busy = false;
    controls();
  }
};
function updateSavedViews(){
  const picker=byId('saved-view-picker'), current=state.projection.id;
  const views=(state.available_views||[current]).filter(view=>view!==current);
  picker.replaceChildren(...views.map(view=>new Option(view,view)));
  byId('saved-view-controls').hidden=!provider.viewSelection||!views.length;
  const message=byId('closed-view-message');
  message.hidden=savedViewAvailable();
  message.textContent=state.available_views?.length
    ? current+' is unavailable in this saved revision. Open an available physical view or restore a prior revision.'
    : 'There are no saved physical views. Source, retained review and revision history are still available.';
  showConfigurationReviews('closed',state.configuration_reviews,
    'Saved revision '+state.revision,state.projection.bundle_sha256);
}
function showConfigurationReviews(panel, reviews, revisionLabel, bundle) {
  const details = byId(panel+'-retained-reviews');
  const findings = byId(panel+'-retained-findings');
  details.hidden = !reviews.length;
  findings.replaceChildren();
  if (details.hidden) return;
  removalSummary(findings,[revisionLabel,bundle].filter(Boolean).join(' · '));
  for (const {file,scope_sha256,report} of reviews) {
    const heading = document.createElement('h2');
    heading.textContent = file+' · '+report.status;
    findings.append(heading);
    removalSummary(findings,'Retained scope '+scope_sha256);
    removalSummary(findings,'Selected native configuration reconciliation · Behavior not run · Engineering acceptance not evaluated');
    const view = report.view;
    if (view?.root) {
      removalSummary(findings,'Current context '+view.root.native_name+' : '+view.root.type);
      for (const [id,role] of Object.entries(view.selected_roles))
        removalSummary(findings,id+' · '+role.native_name+' : '+role.type+' · Parent '+role.parent);
      for (const [id,peer] of Object.entries(view.external_roles||{}))
        removalSummary(findings,'External '+id+' · '+peer.native_name+' : '+peer.type);
      for (const [id,connection] of Object.entries(view.connections||{})) {
        const end = endpoint => endpoint.role+'.'+endpoint.port;
        removalSummary(findings,'Native adjacency '+id+' · '+end(connection.from)+' ↔ '+end(connection.to));
      }
    }
    for (const name of view?.open_alternatives||[])
      removalSummary(findings,'Open library alternative '+name);
    for (const omission of report.system_view?.omissions||[])
      removalSummary(findings,omission.id+' · '+omission.status+' · '+omission.reason);
    for (const finding of report.findings)
      removalSummary(findings,[finding.id,finding.rule,finding.status,finding.detail].filter(Boolean).join(' · '));
  }
}
async function switchSavedView(view){
  if(busy||gestureActive)
    return{outcome:'refused',error:{code:'interaction_busy',detail:'Finish the current interaction before switching views.'}};
  if(unknown||dirty||pending)
    return{outcome:'refused',error:{code:'retained_edit',detail:'Resolve the current edit before switching views.'}};
  if(!provider?.viewSelection||view===state?.projection.id||!state?.available_views?.includes(view))
    return{outcome:'refused',error:{code:'view_unavailable',detail:'Choose another available physical view in this project.'}};
  const previous=chosenView;
  chosenView=view;busy=true;controls();
  try{
    if(!await loadState())throw Error('The selected view did not finish opening.');
    let message='Opened '+view+' at saved revision '+state.revision+'.';
    try{provider.rememberView?.(view);}
    catch{message+=' This host could not update the address for reopening.';}
    notice(message);
    return{outcome:'opened',view_id:view};
  }catch(error){
    chosenView=previous;notice(error.message);
    return{outcome:'refused',error:{code:error.code||'view_unavailable',detail:error.message}};
  }finally{busy=false;controls();}
}
byId('saved-view-picker').onchange=controls;
byId('open-saved-view').onclick=async()=>{
  await switchSavedView(byId('saved-view-picker').value);
};
function resetRemovalFields(){
  removalCapture=null;
  byId('removal-values').value='{}';
  byId('removal-target').textContent=editingNode()?'Captured '+editingNode()[1].element+' · '+editTargetId+' · revision '+formRevision:'Select an element or framed occurrence to remove.';
  byId('removal-status').textContent='';
  byId('removal-consequences').replaceChildren();
}
function renderRemovalControls(){
  const fieldset=byId('removal-fields'), node=editingNode()?.[1];
  fieldset.disabled=!node||Boolean(draftKind&&draftKind!=='removal');
  byId('remove-diagram').disabled=!node?.frame_id;
  byId('delete-native').disabled=!node;
  const values=JSON.parse(byId('removal-values').value);
  const impact=removalCapture?.impact;
  byId('preview-removal').disabled=!impact||busy||Boolean(impact.owned_blockers?.length)||
    (impact.incoming||[]).some((row,index)=>!row.typing_owner_id||!Object.hasOwn(values.references,index))||
    impact.views.some((row,index)=>!values.views?.includes(index));
}
function removalSummary(parent, text){
  const line=document.createElement('p');
  line.textContent=text;
  parent.append(line);
}
function renderRemovalConsequences(impact){
  const panel=byId('removal-consequences');
  panel.replaceChildren();
  if(impact.part_ids)removalSummary(panel,'Native declarations to delete '+Object.entries(impact.part_ids).map(([id,name])=>name+' ('+id+')').join(', '));
  for(const blocker of impact.owned_blockers||[])removalSummary(panel,'Requires explicit disposition: '+blocker.owner+' · '+(blocker.member_kinds.join(', ')||blocker.relationship)+(blocker.source_location?' · '+blocker.source_location.file+' at '+blocker.source_location.offset:''));
  for(const [index,row]of (impact.incoming||[]).entries()){
    removalSummary(panel,row.location.file+' at '+row.location.offset+' · '+row.spelling+' resolves to '+row.target);
    if(!row.typing_owner_id){removalSummary(panel,'This incoming reference needs a supported source effect before deletion.');continue;}
    const label=document.createElement('label'), select=document.createElement('select');
    label.textContent='Effect for '+row.spelling+' at '+row.location.offset;
    select.append(new Option('Choose an explicit effect',''),new Option('Remove explicit typing','remove'));
    for(const definition of typeDefinitions().filter(row=>!Object.hasOwn(impact.part_ids,row.element_id)))
      select.append(new Option('Use '+definition.element,definition.element_id));
    select.onchange=()=>{
      const next=JSON.parse(byId('removal-values').value);
      if(select.value)next.references[index]=select.value==='remove'?null:select.value;
      else delete next.references[index];
      writeRemovalValues(next);
    };
    label.append(select);panel.append(label);
  }
  for(const [index,view]of impact.views.entries()){
    const label=document.createElement('label'), check=document.createElement('input');
    check.type='checkbox';check.dataset.removalView=view.view_id;
    label.append(check,document.createTextNode((view.action==='close_view'?'Close ':'Remove occurrences from ')+view.view_id));
    check.onchange=()=>{
      const values=JSON.parse(byId('removal-values').value);
      values.views=values.views.filter(value=>value!==index);
      if(check.checked)values.views.push(index);
      writeRemovalValues(values);
    };
    panel.append(label);
    removalSummary(panel,'Nodes '+view.node_ids.join(', ')+' · routes '+(view.edge_ids.join(', ')||'none'));
    if(view.removed_templates.length&&view.retained_authored_legend.length)
      removalSummary(panel,'Last use removed for '+view.removed_templates.join(', ')+'. Authored key retained: '+view.retained_authored_legend.join(' · '));
  }
}
function writeRemovalValues(values){
  byId('removal-values').value=JSON.stringify(values);
  draftKind='removal';dirty=true;draftGeneration++;controls();
}
async function inspectRemoval(operation){
  const node=editingNode()?.[1];
  if(!node||busy||unknown||pending||formRevision!==state.revision||
      dirty&&draftKind!=='removal'||operation==='remove_occurrence'&&!node.frame_id)return;
  const target={expected_revision:formRevision,expected_bundle_sha256:state.projection.bundle_sha256,
    ...(operation==='delete'?{element_id:editTargetId}:{view_id:state.projection.id,node_id:node.frame_id})};
  const capturedId=editTargetId, capturedOccurrence=editTargetOccurrenceId;
  busy=true;controls();byId('removal-status').textContent='Reading removal effects…';
  try{
    const impact=await api('/api/removal-context',target);
    if(impact.revision!==target.expected_revision||impact.bundle_sha256!==target.expected_bundle_sha256||
      impact.project_id!==state.projection.project_id||impact.commit!==state.commit||impact.element_id!==capturedId||
      editTargetId!==capturedId||editTargetOccurrenceId!==capturedOccurrence||
      (operation==='remove_occurrence'&&(impact.view_id!==target.view_id||impact.node_id!==target.node_id)))
      throw Error('The returned removal effects do not match the captured selection.');
    removalCapture={operation,impact};
    writeRemovalValues({references:{},views:[]});
    renderRemovalConsequences(impact);
    byId('removal-status').textContent=operation==='delete'?'Review native deletion and affected source and views.':'Review the captured view and its affected occurrences.';
    byId('removal-target').textContent=node.element+' · '+capturedId+' · revision '+impact.revision+
      (operation==='remove_occurrence'?' · '+impact.view_id+' / '+impact.node_id:'');
  }catch(error){byId('removal-status').textContent=error.message;}
  finally{busy=false;controls();}
}
function previewRemoval(){
  const capture=removalCapture;
  if(!capture||!editingNode()||byId('preview-removal').disabled)return;
  const {operation,impact}=capture, values=JSON.parse(byId('removal-values').value);
  if(impact.revision!==formRevision||impact.bundle_sha256!==state.projection.bundle_sha256){
    notice('The captured effects belong to an earlier revision. Inspect the removal again.');return;
  }
  const view_effects=impact.views.map(({view_id,action,node_ids,edge_ids})=>({view_id,action,node_ids,edge_ids}));
  const fields=operation==='delete'
    ?{element_id:impact.element_id,reference_effects:impact.incoming.map((row,index)=>({location:row.location,replacement_id:values.references[index]}))}
    :{view_id:impact.view_id,node_id:impact.node_id};
  return previewRemovalRequest(operation,fields,view_effects);
}
function previewRemovalRequest(operation, fields, view_effects){
  return previewChange(request(operation,{...fields,view_effects,checked_bundle_sha256:null}),
    (operation==='delete'?'Delete native part ':'Remove diagram occurrence ')+editTargetName);
}
function appendRemovalSummary(preview){
  const lines=[];
  for(const view of preview.removal.views)lines.push(view.view_id+' · '+(view.action==='close_view'?'closes':'removes '+view.node_ids.join(', '))+' · routes '+(view.edge_ids.join(', ')||'none'));
  for(const review of preview.configuration_reviews)for(const finding of review.report.findings)
    lines.push(review.file+' · '+finding.rule+' · '+finding.status+' · '+finding.detail);
  if(lines.length)byId('summary').textContent+='\n'+lines.join('\n');
}
byId('remove-diagram').onclick=()=>inspectRemoval('remove_occurrence');
byId('delete-native').onclick=()=>inspectRemoval('delete');
byId('removal-form').onsubmit=event=>{event.preventDefault();previewRemoval();};
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

let catalogPage, catalogInspected, catalogSelection=null;
let catalogGeneration=0, catalogDetailGeneration=0, catalogSelectionGeneration=0;
const catalogLimit=6;
const catalogSelectionSchema='cse.component-selection/1';
async function fetchCatalogPage(filters, limit, cursor){
  return api('/api/catalog-search',{...filters,limit,cursor});
}
async function inspectCatalog(component_id,catalog_sha256,include_svg){
  const result=await api('/api/catalog-inspect',{component_id,catalog_sha256,include_svg});
  if(result.catalog_sha256!==catalog_sha256||result.component?.id!==component_id)
    throw Error('The component does not match the requested catalog revision and ID.');
  if(include_svg){
    const raw=Uint8Array.from(atob(result.svg_base64),character=>character.charCodeAt(0));
    const digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',raw)),
      byte=>byte.toString(16).padStart(2,'0')).join('');
    if(digest!==result.component.sha256)throw Error('The SVG bytes do not match the catalog digest.');
  }
  return result;
}
async function showCatalogComponent(componentId,revision){
  const generation=++catalogDetailGeneration,status=byId('catalog-status'),panel=byId('catalog-inspection');
  status.textContent='Inspecting '+componentId+'…';catalogInspected=null;panel.hidden=true;frameMasterControls();
  try{
    const {component,svg_base64}=await inspectCatalog(componentId,revision,true);
    if(generation!==catalogDetailGeneration)return;
    const artwork=byId('catalog-artwork'),metadata=byId('catalog-metadata');
    byId('catalog-title').textContent=component.name;
    artwork.alt=component.name;artwork.src='data:image/svg+xml;base64,'+svg_base64;
    const mapping=component.mapping;
    const facts={'Component ID':component.id,'Family':component.family,'Treatment':component.treatment,
      'Source file':component.source_file,'Source element':component.source_element_id,
      'Approval state':component.approval_state,'Applicable context':mapping?.principle,
      'SysML v2 context':mapping?.sysml_v2?.join(', '),'Applicability':mapping?.rationale,
      'SVG SHA-256':component.sha256,'Catalog SHA-256':revision};
    metadata.replaceChildren(...Object.entries(facts).flatMap(([label,value])=>{
      if(value===undefined||value===null||value==='')return [];
      const term=document.createElement('dt'),description=document.createElement('dd');
      term.textContent=label;description.textContent=value;
      description.style.overflowWrap='anywhere';
      return[term,description];
    }));
    catalogInspected={componentId,revision,svgSha:component.sha256};
    renderCatalogSelection();
    frameMasterControls();
    panel.hidden=false;status.textContent='Showing '+componentId;
  }catch(error){if(generation===catalogDetailGeneration)status.textContent=error.message;}
}
async function showCatalogPage(next=false){
  if(next&&!catalogPage?.next_cursor)return;
  const generation=++catalogGeneration,status=byId('catalog-status'),more=byId('catalog-more');
  const filters=next?catalogPage.filters:{query:byId('catalog-query').value,
    family:byId('catalog-family').value.trim()||null,sysml:byId('catalog-sysml').value.trim()||null};
  const cursor=next?catalogPage.next_cursor:null;
  if(!next){
    catalogDetailGeneration++;catalogPage=null;catalogInspected=null;
    byId('catalog-results').replaceChildren();
    byId('catalog-inspection').hidden=true;
    frameMasterControls();
  }
  more.disabled=true;status.textContent='Searching the catalog…';
  try{
    const result=await fetchCatalogPage(filters,catalogLimit,cursor);
    if(generation!==catalogGeneration)return;
    const results=byId('catalog-results');
    results.append(...result.items.map(component=>{
      const row=document.createElement('li'),button=document.createElement('button');
      button.type='button';button.textContent=component.name+' · '+component.id;
      button.addEventListener('click',()=>showCatalogComponent(component.id,result.catalog_sha256));
      row.append(button);return row;
    }));
    catalogPage=result;
    status.textContent=result.total?results.children.length+' of '+result.total+' components':'No components found';
  }catch(error){if(generation===catalogGeneration)status.textContent=error.message;}
  finally{if(generation===catalogGeneration){more.hidden=!catalogPage?.next_cursor;more.disabled=more.hidden;}}
}
byId('catalog-form').onsubmit=event=>{event.preventDefault();void showCatalogPage();};
byId('catalog-more').onclick=()=>showCatalogPage(true);

async function validateCatalogSelection(record){
  const received=await api('/api/catalog-selection',record);
  if(Object.keys(received).length!==3||received.schema!==catalogSelectionSchema||
      received.catalog_sha256!==record.catalog_sha256||
      !Array.isArray(received.component_ids)||received.component_ids.length!==record.component_ids.length||
      received.component_ids.some((id,index)=>id!==record.component_ids[index]))
    throw Error('The validated record does not match the requested artwork selection.');
  return received;
}
function setCatalogSelection(record){
  catalogSelection=record;catalogSelectionGeneration++;
  renderCatalogSelection();notifyContext();
}
function removeCatalogSelection(id){
  const ids=catalogSelection.component_ids.filter(selected=>selected!==id);
  setCatalogSelection(ids.length?{...catalogSelection,component_ids:ids}:null);
  byId('catalog-selection-status').textContent=ids.length+' selected';
}
function renderCatalogSelection(){
  const ids=catalogSelection?.component_ids||[];
  byId('catalog-selection-toggle').textContent=ids.includes(catalogInspected?.componentId)
    ?'Remove from artwork selection':'Add to artwork selection';
  byId('catalog-selected-ids').replaceChildren(...ids.map(id=>{
    const item=document.createElement('li'),button=document.createElement('button');
    button.type='button';button.textContent='Remove '+id;
    button.onclick=()=>removeCatalogSelection(id);item.append(button);
    return item;
  }));
  byId('catalog-selection-open').disabled=ids.length>0;
  byId('catalog-selection-download').disabled=!ids.length;
}
byId('catalog-selection-toggle').onclick=()=>{
  if(!catalogInspected)return;
  const {componentId,revision}=catalogInspected,ids=catalogSelection?.component_ids||[];
  if(catalogSelection&&catalogSelection.catalog_sha256!==revision){
    byId('catalog-status').textContent='The selected artwork belongs to another catalog revision. Remove its entries before adding new artwork.';
  }else if(ids.includes(componentId)){
    removeCatalogSelection(componentId);
    byId('catalog-status').textContent='Removed '+componentId+' from the artwork selection';
  }else if(ids.length<50){
    setCatalogSelection({schema:catalogSelectionSchema,catalog_sha256:revision,component_ids:[...ids,componentId]});
    byId('catalog-status').textContent='Added '+componentId+' to the artwork selection';
    byId('catalog-selection-status').textContent=catalogSelection.component_ids.length+' selected';
  }else{
    byId('catalog-status').textContent='The artwork selection can hold up to 50 IDs.';
  }
};
byId('catalog-selection-open').onchange=async event=>{
  const file=event.target.files[0],status=byId('catalog-selection-status');
  event.target.value='';
  if(!file||catalogSelection)return;
  const generation=++catalogSelectionGeneration;
  try{
    if(file.size>65536)throw Error('Selection JSON exceeds 64 KiB.');
    const record=await validateCatalogSelection(JSON.parse(await file.text()));
    if(generation!==catalogSelectionGeneration)return;
    setCatalogSelection(record);status.textContent='Opened '+record.component_ids.length+' selected artwork IDs';
  }catch(error){if(generation===catalogSelectionGeneration)status.textContent=error.message;}
};
byId('catalog-selection-download').onclick=async()=>{
  if(!catalogSelection)return;
  const status=byId('catalog-selection-status'),record=catalogSelection;
  try{
    const checked=await validateCatalogSelection(record);
    const text=JSON.stringify(checked,null,2)+'\n';
    if(provider.downloadCatalogSelection){
      const response=await provider.downloadCatalogSelection(text);
      if(response?.isError)throw Error('The host declined the selection download.');
    }else if(provider.localArtifacts||provider.kind==='private_web'){
      downloadLocalFile({name:'cse-component-selection.json',mediaType:'application/json',text});
    }else throw Error('This host does not support selection downloads.');
    status.textContent='Selection download requested';
  }catch(error){status.textContent=error.message;}
};

function frameMasterBinding({view_id,node_id,element_id,component_id,catalog_sha256,svg_sha256}){
  return {view_id,node_id,element_id,component_id,catalog_sha256,svg_sha256};
}
function presentationDrawingExpected(){
  return presentationOperation(pending?.request.operation)||
    pending?.request.operation==='restore'&&Boolean(pending.preview?.candidate_svg_sha256);
}
function presentationDrawingReady(){
  return unknown||!presentationDrawingExpected()||byId('candidate-diagram').style.visibility==='visible';
}
function frameMasterControls(){
  const begin=byId('begin-frame-master'),form=byId('frame-master-form');
  const row=editingNode()?.[1],same=Boolean(row?.frame_id&&selectedId===editTargetId&&selectedOccurrenceId===editTargetOccurrenceId);
  const selected=selectedNode()?.[1],saved=state?.frame_masters?.[selected?.frame_id],label=byId('saved-frame-master');
  const editStyle=byId('edit-saved-frame-style');
  label.hidden=!saved;
  if(saved)label.textContent='Saved frame master for '+selected.frame_id+' · '+saved.component_id;
  begin.hidden=!/^palette-rectangle-(white|grey|reverse)-(plain|dots|diagonal)$/.test(catalogInspected?.componentId||'');
  begin.disabled=!initialized||!frameReady||busy||gestureActive||!same||dirty||Boolean(pending)||unknown;
  editStyle.hidden=!saved||!state?.appearance_palette;
  editStyle.disabled=begin.disabled;
  form.hidden=draftKind!=='set_frame_master'||!frameMasterDraft;
  if(!form.hidden)
    byId('frame-master-target').textContent=frameMasterDraft.component_id+' → '+frameMasterDraft.view_id+' / '+frameMasterDraft.node_id;
  for(const field of form.querySelectorAll('button,textarea,select'))
    field.disabled=!initialized||!frameReady||busy||gestureActive||!same||Boolean(pending)||unknown;
}
function setFrameMasterStyle(style){
  const swatches=state.appearance_palette?.swatches;
  byId('frame-style-fields').hidden=!swatches||!style;
  if(!swatches||!style)return;
  for(const key of ['fill','stroke','text']){
    const select=byId('frame-style-'+key);
    select.replaceChildren(...Object.entries(swatches).map(([id,hex])=>new Option(id+' · '+hex,id)));
    select.value=style[key];
  }
  byId('frame-style-align').value=style.align;
}
function frameMasterStyle(){
  if(byId('frame-style-fields').hidden)return null;
  return Object.fromEntries(['fill','stroke','text','align'].map(key=>[key,byId('frame-style-'+key).value]));
}
function beginFrameMaster(binding,legend,style){
  frameMasterDraft=frameMasterBinding(binding);
  setFrameMasterStyle(style||state.frame_styles?.[binding.node_id]);
  byId('frame-master-legend').value=legend?.join('\n')||'';
  byId('catalog-panel').open=true;
  draftKind='set_frame_master';dirty=true;draftGeneration++;
  controls();
}
function previewFrameMaster(){
  if(!frameMasterDraft||byId('preview-frame-master').disabled)
    return{outcome:'refused',error:{code:'target',detail:'Return to the captured frame artwork draft before previewing.'}};
  const legend=appearanceLegend('frame-master-legend');
  const style=frameMasterStyle();
  return previewChange(request('set_frame_master',{...frameMasterDraft,legend,...(style?{style}:{})}),
    'Frame artwork '+frameMasterDraft.component_id+' → '+frameMasterDraft.view_id+' / '+frameMasterDraft.node_id);
}
byId('begin-frame-master').onclick=()=>{
  beginFrameMaster({view_id:state.projection.id,node_id:editingNode()[1].frame_id,element_id:editTargetId,
    component_id:catalogInspected.componentId,catalog_sha256:catalogInspected.revision,svg_sha256:catalogInspected.svgSha},null);
  byId('frame-master-legend').focus();
};
byId('edit-saved-frame-style').onclick=()=>{
  const node_id=editingNode()[1].frame_id,master=state.frame_masters[node_id];
  beginFrameMaster({view_id:state.projection.id,node_id,element_id:editTargetId,component_id:master.component_id,
    catalog_sha256:state.appearance_palette.catalog_sha256,svg_sha256:master.svg_sha256},null);
  byId('frame-style-fill').focus();
};
byId('frame-master-form').addEventListener('input',retainFormInput);
byId('frame-master-form').onsubmit=event=>{event.preventDefault();void previewFrameMaster();};

function appearanceLegend(id){
  const text=byId(id).value.trim();
  return text?text.split('\n').map(line=>line.trim()):null;
}
function connectorStyleBinding({view_id,edge_id,source_id,target_id,swatch,palette_sha256}){
  return {view_id,edge_id,source_id,target_id,swatch,palette_sha256};
}
function observedConnector(edge_id){
  const edge=state?.projection.edges[edge_id],palette=state?.appearance_palette;
  if(!edge||!palette||!Object.hasOwn(state.projection.edges,edge_id))return null;
  const nodes=state.projection.nodes;
  return {view_id:state.projection.id,edge_id,source_id:nodes[edge.source].element_id,target_id:nodes[edge.target].element_id,
    swatch:state.connector_styles?.[edge_id]||'N100',palette_sha256:palette.swatches_sha256};
}
function connectorStyleControls(){
  const chooser=byId('connector-style-edge'),form=byId('connector-style-form');
  const key=state?.commit+'/'+state?.projection.id;
  if(key!==connectorOptionsKey){
    connectorOptionsKey=key;
    const chosen=chooser.value;
    const options=Object.entries(state?.projection.edges||{}).map(([id,edge])=>
      new Option(id+' · '+edge.source+' → '+edge.target,id));
    chooser.replaceChildren(new Option('Choose a connector',''),...options);
    if(options.some(option=>option.value===chosen))chooser.value=chosen;
  }
  const current=observedConnector(chooser.value);
  const label=byId('saved-connector-style');
  label.hidden=!current;
  if(current)label.textContent='Saved connector swatch · '+current.swatch;
  const unavailable=!initialized||!frameReady||busy||gestureActive||Boolean(pending)||unknown;
  chooser.disabled=unavailable||draftKind==='set_connector_style';
  byId('edit-connector-style').disabled=unavailable||dirty||!current;
  form.hidden=draftKind!=='set_connector_style'||!connectorStyleDraft;
  if(form.hidden)return;
  const captured=connectorStyleDraft,retained=observedConnector(captured.edge_id);
  const matches=retained&&['view_id','edge_id','source_id','target_id','palette_sha256'].every(key=>retained[key]===captured[key]);
  byId('connector-style-target').textContent=captured.view_id+' / '+captured.edge_id;
  for(const field of form.querySelectorAll('button,textarea,select'))field.disabled=unavailable||!matches;
}
function beginConnectorStyle(binding){
  connectorStyleDraft=connectorStyleBinding(binding);
  const swatch=byId('connector-style-swatch');
  swatch.replaceChildren(...Object.entries(state.appearance_palette?.swatches||{}).map(([id,hex])=>new Option(id+' · '+hex,id)));
  swatch.value=binding.swatch;
  byId('connector-style-edge').value=binding.edge_id;
  byId('connector-style-legend').value=binding.legend?.join('\n')||'';
  byId('connector-style-panel').open=true;
  draftKind='set_connector_style';dirty=true;draftGeneration++;
  controls();
  byId('connector-style-edge').value=binding.edge_id;
  connectorStyleControls();
}
function previewConnectorStyle(){
  if(!connectorStyleDraft||byId('preview-connector-style').disabled)
    return{outcome:'refused',error:{code:'target',detail:'Return to the captured connector draft before previewing.'}};
  const swatch=byId('connector-style-swatch').value;
  return previewChange(request('set_connector_style',{...connectorStyleDraft,swatch,legend:appearanceLegend('connector-style-legend')}),
    'Connector '+connectorStyleDraft.edge_id+' · '+swatch);
}
byId('connector-style-edge').onchange=controls;
byId('edit-connector-style').onclick=()=>{
  beginConnectorStyle(observedConnector(byId('connector-style-edge').value));
  byId('connector-style-swatch').focus();
};
byId('connector-style-form').addEventListener('input',retainFormInput);
byId('connector-style-form').onsubmit=event=>{event.preventDefault();void previewConnectorStyle();};

function viewKeyBinding({view_id,master_sha256,legend}){
  return {view_id,master_sha256,legend};
}
function viewKeyControls(){
  const saved=state?.view_key,panel=byId('view-key-panel'),form=byId('view-key-form');
  panel.hidden=!saved;
  if(!saved)return;
  const lines=byId('saved-view-key-lines');
  lines.replaceChildren(...saved.legend.map(line=>{
    const item=document.createElement('li');
    item.textContent=line;return item;
  }));
  const unavailable=!initialized||!frameReady||busy||gestureActive||Boolean(pending)||unknown;
  byId('edit-view-key').disabled=unavailable||dirty;
  form.hidden=draftKind!=='set_view_key'||!viewKeyDraft;
  const exact=viewKeyDraft?.view_id===saved.view_id&&viewKeyDraft?.master_sha256===saved.master_sha256;
  for(const field of form.querySelectorAll('textarea,button'))field.disabled=unavailable||!exact;
}
function beginViewKey(binding){
  viewKeyDraft={view_id:binding.view_id,master_sha256:binding.master_sha256};
  byId('view-key-panel').open=true;
  byId('view-key-legend').value=binding.legend.join('\n');
  draftKind='set_view_key';dirty=true;draftGeneration++;
  controls();
}
function previewViewKey(){
  if(!viewKeyDraft||byId('preview-view-key').disabled)
    return{outcome:'refused',error:{code:'target',detail:'Return to the captured local key draft before previewing.'}};
  const legend=appearanceLegend('view-key-legend');
  return previewChange(request('set_view_key',{...viewKeyDraft,legend}),'Local key · '+viewKeyDraft.view_id);
}
byId('edit-view-key').onclick=()=>{
  beginViewKey(state.view_key);
  byId('view-key-legend').focus();
};
byId('view-key-form').addEventListener('input',retainFormInput);
byId('view-key-form').onsubmit=event=>{event.preventDefault();void previewViewKey();};

globalThis.cseWorkbench=Object.freeze({
  context:workbenchContext,
  subscribe(subscriber){if(typeof subscriber!=='function')throw TypeError('Supply a context listener.');contextSubscribers.add(subscriber);notifyContext();return()=>contextSubscribers.delete(subscriber);},
});
setInterval(async()=>{
  if(!initialized||!state||busy||gestureActive||polling||(!provider?.localArtifacts&&document.hidden))return;polling=true;
  try{const head=await api('/api/head');if(head.commit!==state.commit){if(busy||gestureActive||dirty||pending)notice('The project changed elsewhere. Your pending values are retained; refresh and review before another preview.');else await loadState(false,true);}}
  catch(error){notice('Refresh unavailable: '+error.message);}
  finally{polling=false;}
},provider?.refreshIntervalMs||1500);
start();
