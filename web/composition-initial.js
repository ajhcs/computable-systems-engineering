'use strict';
// A prospective authoring session never supplies a simulated saved projection.
// Native source, glyph checks, initial Git publication and receipts are shared
// with the CLI. Supplied application hosts own their transport and persistence.
(()=>{
  const $=id=>document.getElementById(id),clone=value=>JSON.parse(JSON.stringify(value));
  const uiSession=crypto.randomUUID(),subscribers=new Set();
  let state,provider,csrf,builtinProvider=false,disposed=false,busy=false,dirty=false,pending=null,acknowledged=null,unknown=false,connected=false,interaction=0;
  let candidate=null,candidateMode='readable',candidateReady=false,candidateGeneration=0,storageReady=true;
  let storageQueue=Promise.resolve();
  const notice=text=>{if(disposed)return;$('notice').textContent=text;publish()};
  function fail(code,message){const error=new Error(message);error.code=code;throw error}
  let retainedRaw;
  function raw(){if(disposed)return clone(retainedRaw);const value={root_kind:$('root-kind').value,new_name:$('root-name').value,short_id:$('root-short').value,namespace_mode:$('namespace-mode').value,namespace_name:$('package-name').value};retainedRaw=clone(value);return value}
  raw();
  function fields(value){exact(value,['root_kind','new_name','short_id','namespace_mode','namespace_name']);if(Object.values(value).some(v=>typeof v!=='string')||!['','definition','usage'].includes(value.root_kind)||!['','global','package'].includes(value.namespace_mode))fail('intent_storage','Invalid retained initial form.');for(const [id,text]of [['root-name',value.new_name],['root-short',value.short_id],['package-name',value.namespace_name]]){const probe=$(id).cloneNode(false);probe.value=text;if(probe.value!==text)fail('intent_storage','Retained names cannot be restored without changing their bytes.')} $('root-kind').value=value.root_kind;$('root-name').value=value.new_name;$('root-short').value=value.short_id;$('namespace-mode').value=value.namespace_mode;$('package-name').value=value.namespace_name;meaning()}
  function meaning(){const kind=$('root-kind').value,usage=kind==='usage';$('root-meaning').textContent=!kind?'Choose the native root kind.':usage?'No explicit typing. Native default multiplicity 1..1. A namespace/package-owned root is noncomposite and has no physical parent.':'A part definition declares a type; it does not assert an installed part.';$('package-field').hidden=$('namespace-mode').value!=='package';$('package-name').required=$('namespace-mode').value==='package'}
  const key=()=> 'cse-initial:'+state.project_id+':'+state.root_element_id+':'+state.view_id;
  function persist(){
    const value=JSON.stringify({version:1,project_id:state.project_id,root_element_id:state.root_element_id,view_id:state.view_id,raw:raw(),dirty,pending,acknowledged,unknown,observed_head:state.current_saved});
    const storageKey=key();
    const operation=storageQueue.then(async()=>{
      await provider.intentStorage.setItem(storageKey,value);
      if(await provider.intentStorage.getItem(storageKey)!==value)fail('intent_storage','The exact initial request could not be retained.');
      storageReady=true;
    }).catch(error=>{storageReady=false;throw error});
    storageQueue=operation.catch(()=>{});
    return operation;
  }
  async function retainOutcome(){try{await persist();return ''}catch{storageReady=false;return ' Session state could not be retained. Keep the original checked request for recovery.'}}
  function controls(){
    if(disposed)return;
    $('initial-fields').disabled=!connected||busy||unknown||Boolean(acknowledged)||Boolean(pending);
    $('create-initial').disabled=!connected||busy||!pending||Boolean(acknowledged)||!storageReady||!unknown&&!candidateReady;
    $('create-initial').textContent=unknown?'Retry same creation':'Create model';
    $('edit-draft').disabled=!connected||busy||!pending||pending.dispatched||Boolean(acknowledged);
    $('recover-initial').hidden=!pending?.dispatched||Boolean(acknowledged);$('recover-initial').disabled=!connected||busy;
    $('open-saved').hidden=!acknowledged;$('open-saved').disabled=!connected||busy;
    $('candidate-title').textContent=acknowledged?'Initial creation acknowledged':unknown?'Creation unconfirmed':'Unsaved initial candidate';
    if(connected){$('saved-state').textContent=acknowledged?'Initial creation acknowledged. Open the current saved model to continue.':unknown?'Initial creation is unconfirmed. Retain and recover the exact request.':pending?'Unsaved checked initial candidate. No publication has been acknowledged.':state.current_saved?'A saved project is present. This draft has no acknowledged first receipt.':'Unsaved initial session. No acknowledged model has been opened.';if(candidate)$('candidate-status').textContent=acknowledged?'This is the checked initial source from revision 1. The current saved model may have later changes.':unknown?'Checked initial source. Its publication is unconfirmed.':'Native source and diagram checks passed. The candidate is unsaved.'}
  }
  function context(){if(disposed)return{ready:false,phase:'closed',last_acknowledged_receipt:acknowledged?clone(acknowledged):null};return{ready:connected&&!busy,phase:'initial',host_transport:provider?.kind||'unavailable',
    guard:state?{project_id:state.project_id,root_element_id:state.root_element_id,view_id:state.view_id,model_revision:0,ui_session_id:uiSession,interaction_revision:interaction}:null,
    initial_state:state?clone(state):null,raw_draft:raw(),has_form_draft:dirty,
    pending_change:pending?clone(pending):null,candidate_ready:candidateReady,
    unconfirmed_save:unknown,last_acknowledged_receipt:acknowledged?clone(acknowledged):null,notice:$('notice').textContent,
    scope:'initial_root_authoring_never_implies_installed_presence_or_retained_review_scope'};}
  function publish(){if(disposed)return;controls();for(const callback of subscribers){try{Promise.resolve(callback(context())).catch(()=>{})}catch{}}}
  function host(){
    if(!Object.hasOwn(globalThis,'cseInitialHost')){builtinProvider=true;return{version:'cse-initial-host-1',kind:'loopback',
      intentStorage:{getItem:key=>sessionStorage.getItem(key),setItem:(key,value)=>sessionStorage.setItem(key,value),removeItem:key=>sessionStorage.removeItem(key)},
      request:async({operation,payload})=>{const path={session:'/session',initial_state:'/startup/state',initial_preview:'/startup/preview',initial_apply:'/startup/apply',initial_receipt:'/startup/receipt',initial_open:'/startup/open'}[operation];if(!path)fail('transport','Unsupported initial operation');const options={credentials:'same-origin',cache:'no-store'};if(payload!==undefined)Object.assign(options,{method:'POST',headers:{'Content-Type':'application/json','X-CSE-CSRF':csrf||''},body:JSON.stringify(payload)});const result=await fetch(path,options);return{status:result.status,body:await result.json()}},openSaved:async()=>location.assign('/')};}
    const value=globalThis.cseInitialHost;
    if(!value||value.version!=='cse-initial-host-1'||typeof value.kind!=='string'||!value.kind||typeof value.request!=='function'||typeof value.openSaved!=='function'||!value.intentStorage||['getItem','setItem','removeItem'].some(key=>typeof value.intentStorage[key]!=='function'))fail('transport','Incomplete supplied initial-project host.');
    exact(value.grant,['project_id','root_element_id','view_id']);if(!uuid(value.grant.project_id)||!uuid(value.grant.root_element_id)||!viewId(value.grant.view_id))fail('transport','Invalid supplied initial grant.');
    return Object.freeze({version:value.version,kind:value.kind,grant:Object.freeze(clone(value.grant)),request:value.request.bind(value),openSaved:value.openSaved.bind(value),intentStorage:Object.freeze(Object.fromEntries(['getItem','setItem','removeItem'].map(key=>[key,value.intentStorage[key].bind(value.intentStorage)])))});
  }
  async function api(operation,payload){if(disposed)fail('closed','The initial controller is closed.');const response=await provider.request({operation,payload:payload===undefined?undefined:clone(payload)});if(!response||!Number.isInteger(response.status)||!response.body)fail('transport','Invalid initial response');const body=clone(response.body);if(response.status<200||response.status>=300){const error=new Error(body.error?.detail||'Initial operation unavailable');error.code=body.error?.code||'unavailable';error.definitive_refusal=body.error?.definitive_refusal===true;throw error}return body}
  async function run(action){if(!connected||disposed)fail('not_connected','The initial session is unavailable.');if(busy)fail('interaction_busy','An initial operation is already in progress.');busy=true;interaction++;publish();try{return await action()}finally{busy=false;interaction++;publish()}}
  function exact(value,keys){if(!value||typeof value!=='object'||Array.isArray(value)||Object.keys(value).length!==keys.length||keys.some(key=>!Object.hasOwn(value,key)))fail('input','Supply exactly the documented fields.')}
  const uuid=value=>typeof value==='string'&&/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(value);
  const viewId=value=>typeof value==='string'&&/^[A-Za-z_][A-Za-z0-9_.-]{0,127}$/.test(value);
  const digest=value=>typeof value==='string'&&/^[0-9a-f]{64}$/.test(value);
  const commitId=value=>typeof value==='string'&&/^[0-9a-f]{40}$/.test(value);
  const canonical=value=>JSON.stringify(function sort(item){if(Array.isArray(item))return item.map(sort);if(item&&typeof item==='object')return Object.fromEntries(Object.keys(item).sort().map(key=>[key,sort(item[key])]));return item}(value));
  async function sha256(text){if(!crypto.subtle)fail('transport','This host cannot verify initial source hashes.');return [...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text)))].map(n=>n.toString(16).padStart(2,'0')).join('')}
  function validateState(value){
    if(!value||value.phase!=='initial'||value.revision!==0||value.projection!==null||!uuid(value.project_id)||!uuid(value.root_element_id)||value.project_id===value.root_element_id||!viewId(value.view_id)||!['absent','occupied','unavailable','saved_project'].includes(value.target_observation))fail('state','Invalid prospective initial state.');
    const expected=state||provider.grant;if(expected&&['project_id','root_element_id','view_id'].some(key=>value[key]!==expected[key]))fail('state','Initial response cannot replace the granted project, root or view.');
    if(value.current_saved!==null&&(!value.current_saved||!Number.isInteger(value.current_saved.revision)||value.current_saved.revision<1||!commitId(value.current_saved.commit)))fail('state','Invalid saved-head observation.');
    if(state?.current_saved&&value.current_saved&&(value.current_saved.revision<state.current_saved.revision||value.current_saved.revision===state.current_saved.revision&&value.current_saved.commit!==state.current_saved.commit))fail('response_binding','Saved-head observation moved backwards or changed at the same revision.');
    if(state?.current_saved&&!value.current_saved)value.current_saved=clone(state.current_saved);
    return value;
  }
  function observeHead(revision,commit){
    if(state.current_saved&&(revision<state.current_saved.revision||revision===state.current_saved.revision&&commit!==state.current_saved.commit))fail('response_binding','Saved-head observation moved backwards or changed at the same revision.');
    if(revision>0){state.current_saved={revision,commit};state.target_observation='saved_project'}
  }
  function verifyReceipt(receipt,retained=pending){
    exact(receipt,['project_id','request_id','request_sha256','revision','operation','bundle_sha256','parent_commit','restored_from_revision','storage','commit']);
    if(!retained||receipt.request_id!==retained.request.request_id||receipt.project_id!==state.project_id||receipt.operation!=='initialize_physical_project'||receipt.revision!==1||receipt.bundle_sha256!==retained.request.expected_bundle_sha256||receipt.request_sha256!==retained.request_sha256||receipt.parent_commit!==null||receipt.restored_from_revision!==null||receipt.storage!=='local_git_fsync'||!commitId(receipt.commit))fail('receipt','The initial receipt does not match the checked request.');
  }
  function receiptObservation(receipt,revision,commit){if(revision<1||revision===1&&commit!==receipt.commit)fail('response_binding','First receipt and observed head disagree.')}
  function svgBinding(svg,preview){
    const root=preview.candidate.elements[0],groups=[...svg.querySelectorAll('g[data-node-id]')],group=groups[0],texts=[...svg.querySelectorAll('text')];
    const labels=[...group?.querySelectorAll('text')||[]];
    // Initial roots have no native annotations or display aliases. The original
    // compositor wraps the exact name without dropping spaces; never reflow it.
    if(svg.localName!=='svg'||groups.length!==1||!group||group.getAttribute('data-element-id')!==state.root_element_id||group.getAttribute('data-native-name')!==root.qualified_name||group.getAttribute('data-native-owner')!==(root.owner||'')||texts.length<2||!labels.length||labels.map(t=>t.textContent).join('')!==root.name||labels.some(t=>t.getAttribute('font-family')!=='DejaVu Sans'||t.getAttribute('font-size')!=='28'||t.getAttribute('font-weight')!=='700')||texts.some(t=>!t.textContent))fail('presentation','The rendered initial SVG does not match the requested root and required text.');
  }
  async function verifyPreview(preview,request){
    if(!preview||preview.base_revision!==0||preview.base_commit!==null)fail('response_binding','Initial preview cannot claim a saved revision.');
    exact(preview.request,Object.keys(request));
    if(Object.keys(request).some(key=>key!=='expected_bundle_sha256'&&preview.request[key]!==request[key])||!digest(preview.request.expected_bundle_sha256)||request.expected_bundle_sha256!==null&&preview.request.expected_bundle_sha256!==request.expected_bundle_sha256||preview.candidate_bundle_sha256!==preview.request.expected_bundle_sha256||await sha256(canonical(preview.request))!==preview.request_sha256)fail('response_binding','Initial preview request differs from the submitted draft.');
    exact(preview.files,['model.sysml','views.sysml']);exact(preview.linked_records,[]);exact(preview.registry,[state.root_element_id]);
    const manifest=[];for(const name of Object.keys(preview.files).sort()){if(typeof preview.files[name]!=='string')fail('response_binding','Initial source must be exact text.');manifest.push({path:name,sha256:await sha256(preview.files[name])})}
    if(await sha256(canonical(manifest))!==preview.candidate_bundle_sha256)fail('response_binding','Initial source bytes do not match the checked bundle.');
    const rows=preview.candidate?.elements;if(preview.candidate?.project_id!==state.project_id||preview.candidate?.bundle_sha256!==preview.candidate_bundle_sha256||!Array.isArray(rows)||rows.length!==1)fail('response_binding','Initial native inventory differs from the checked bundle.');
    const root=rows[0],usage=request.root_kind==='usage';if(root.element_id!==state.root_element_id||root.name!==request.new_name||(root.id??null)!==request.short_id||root.kind!==(usage?'parts':'part_definitions')||root.qualified_name!==preview.registry[state.root_element_id]||root.owner_kind!==(request.namespace_name===null?'Namespace':'Package')||request.namespace_name===null&&root.owner!==undefined&&root.owner!==null||root.source_location?.file!=='model.sysml'||!Array.isArray(preview.candidate.configuration_reviews)||preview.candidate.configuration_reviews.length)fail('response_binding','Initial native root differs from the requested meaning.');
    const spelling=preview.source_spelling;exact(spelling,['new_name','short_id','namespace_name']);
    for(const key of Object.keys(spelling)){if(request[key]===null){if(spelling[key]!==null)fail('response_binding','Unexpected initial source name.')}else{exact(spelling[key],['name','source_token','qualified_segment']);if(spelling[key].name!==request[key]||typeof spelling[key].source_token!=='string'||!spelling[key].source_token||typeof spelling[key].qualified_segment!=='string'||!spelling[key].qualified_segment)fail('response_binding','Missing native name serialization.')}}
    const namespace=spelling.namespace_name,name=spelling.new_name,short=spelling.short_id,owner=namespace?.qualified_segment??null;
    const qualified=(namespace?owner+'::':'')+name.qualified_segment;
    const declaration=(usage?'part ':'part def ')+(short?'<'+short.source_token+'> ':'')+name.source_token+';\n';
    const model=namespace?'package '+namespace.source_token+' {\n'+declaration+'}\n':declaration;
    if((root.owner??null)!==owner||root.qualified_name!==qualified||preview.files['model.sysml']!==model)fail('response_binding','Native owner/name metadata differs from the checked source spelling.');
    if(usage&&(root.is_composite!==false||root.nested!==false||canonical(root.types)!=='[]'||canonical(root.multiplicity)!==canonical({status:'default',lower:1,upper:1})))fail('response_binding','Initial usage must be noncomposite, untyped and default 1..1.');
    if(root.is_variation!==false||usage&&(root.is_variant!==false||root.has_native_value!==false||canonical(root.redefines)!=='[]'||canonical(root.subsets)!=='[]'||root.has_non_typing_specialization!==false)||!usage&&(root.has_specialization!==false||canonical(root.supertypes)!=='[]'))fail('response_binding','Initial root unexpectedly adds native annotations or specialization.');
    svgBinding(new DOMParser().parseFromString(preview.candidate_svg,'image/svg+xml').documentElement,preview);
  }
  function verifyOpen(result){
    verifyReceipt(result.initial_receipt);if(canonical(result.initial_receipt)!==canonical(acknowledged))fail('response_binding','Saved handoff does not match the acknowledged first receipt.');
    const saved=result.state,projection=saved?.projection,roots=Object.values(projection?.nodes||{}).filter(n=>n.level===0);
    if(!Number.isInteger(saved?.revision)||saved.revision<1||!commitId(saved.commit)||projection?.project_id!==state.project_id||projection.id!==state.view_id||roots.length!==1||roots[0].element_id!==state.root_element_id||typeof result.view_html!=='string')fail('response_binding','Saved handoff cannot replace the project, root, view or revision.');
    if(saved.revision===1&&(saved.commit!==acknowledged.commit||projection.bundle_sha256!==acknowledged.bundle_sha256))fail('response_binding','Revision-one view differs from the acknowledged first commit or source bundle.');
    if(state.current_saved&&(saved.revision<state.current_saved.revision||saved.revision===state.current_saved.revision&&saved.commit!==state.current_saved.commit))fail('response_binding','Saved handoff is older than the observed project head.');
    const first=saved.history?.find(row=>row.revision===1);if(first&&(first.operation!=='initialize_physical_project'||Object.hasOwn(first,'commit')&&first.commit!==acknowledged.commit||Object.hasOwn(first,'bundle_sha256')&&first.bundle_sha256!==acknowledged.bundle_sha256||Object.hasOwn(first,'request_sha256')&&first.request_sha256!==acknowledged.request_sha256))fail('response_binding','Saved history does not retain the acknowledged first revision.');
    const doc=new DOMParser().parseFromString(result.view_html,'text/html'),data=JSON.parse(doc.getElementById('cse-data')?.textContent||'null');
    if(data?.revision!==saved.revision||data.commit!==saved.commit||canonical(data.projection)!==canonical(projection)||!doc.querySelector('svg g[data-element-id="'+state.root_element_id+'"]'))fail('response_binding','Saved handoff view is stale or bound to another model.');
  }
  async function restoreRetained(retained){
    exact(retained,['version','project_id','root_element_id','view_id','raw','dirty','pending','acknowledged','unknown',...(Object.hasOwn(retained,'observed_head')?['observed_head']:[])]);
    if(retained.version!==1||['project_id','root_element_id','view_id'].some(key=>retained[key]!==state[key])||typeof retained.dirty!=='boolean'||typeof retained.unknown!=='boolean')fail('intent_storage','Retained intent does not match this granted session.');
    const value=retained.pending;
    if(value!==null){
      exact(value,['request','request_sha256','raw','dispatched',...(Object.hasOwn(value,'refused')?['refused']:[])]);
      exact(value.request,Object.keys(requestSchema.properties));const request=value.request;
      if(typeof value.dispatched!=='boolean'||Object.hasOwn(value,'refused')&&typeof value.refused!=='boolean'||canonical(value.raw)!==canonical(retained.raw)||!retained.dirty||request.operation!=='initialize_physical_project'||request.expected_revision!==0||!uuid(request.request_id)||request.request_id===state.root_element_id||!['definition','usage'].includes(request.root_kind)||typeof request.new_name!=='string'||!request.new_name||[request.short_id,request.namespace_name].some(name=>name!==null&&(typeof name!=='string'||!name))||['project_id','root_element_id','view_id'].some(key=>request[key]!==state[key])||!digest(request.expected_bundle_sha256)||await sha256(canonical(request))!==value.request_sha256)fail('intent_storage','The exact retained initial request is invalid.');
      const form=retained.raw;if(request.root_kind!==form.root_kind||request.new_name!==form.new_name||request.short_id!==(form.short_id===''?null:form.short_id)||!['global','package'].includes(form.namespace_mode)||request.namespace_name!==(form.namespace_mode==='global'?null:form.namespace_name))fail('intent_storage','Retained raw fields differ from the checked initial request.');
    }else if(retained.acknowledged!==null||retained.unknown)fail('intent_storage','Initial outcome has no retained request.');
    if(retained.acknowledged!==null){if(!value?.dispatched)fail('intent_storage','Acknowledgement has no dispatched request.');verifyReceipt(retained.acknowledged,value)}
    if(retained.unknown!==Boolean(value?.dispatched&&!retained.acknowledged))fail('intent_storage','Retained dispatch and outcome state disagree.');
    if(retained.observed_head!==undefined&&retained.observed_head!==null){exact(retained.observed_head,['revision','commit']);const head=retained.observed_head;if(!Number.isInteger(head.revision)||head.revision<1||!commitId(head.commit))fail('intent_storage','Invalid retained saved-head observation.');if(state.current_saved&&(state.current_saved.revision<head.revision||state.current_saved.revision===head.revision&&state.current_saved.commit!==head.commit))fail('response_binding','Startup head is older than this session previously observed.');if(!state.current_saved)state.current_saved=clone(head)}
    fields(retained.raw);dirty=retained.dirty;pending=value;acknowledged=retained.acknowledged;unknown=retained.unknown;
  }
  function exactPending(request){if(!pending)fail('retained_request','There is no checked initial request.');exact(request,Object.keys(pending.request));if(Object.keys(pending.request).some(key=>request[key]!==pending.request[key]))fail('retained_request','Use the exact retained request, including its checked candidate digest.')}
  function guard(expected){if(!connected||busy)fail('interaction_busy','Wait for the initial session.');const current=context().guard;exact(expected,Object.keys(current));if(Object.keys(current).some(key=>expected[key]!==current[key]))fail('stale_context','The initial session or draft changed. Read context again.')}
  async function discardPreview(){if(pending?.dispatched||unknown||acknowledged)fail('unconfirmed_save','Recover the retained initial creation before editing.');return run(async()=>{pending=null;candidate=null;candidateReady=false;candidateGeneration++;$('candidate').hidden=true;$('initial-diagram').srcdoc='';dirty=true;await persist();notice('Draft retained. Preview again before creating the model.')})}
  function makeRequest(){if(!['definition','usage'].includes($('root-kind').value)||!['global','package'].includes($('namespace-mode').value))fail('input','Choose the native root kind and its namespace explicitly.');if(!$('initial-form').reportValidity())fail('input','Complete the root kind, declared name and namespace choice.');const value=raw();return{operation:'initialize_physical_project',request_id:crypto.randomUUID(),project_id:state.project_id,root_element_id:state.root_element_id,view_id:state.view_id,expected_revision:0,root_kind:value.root_kind,new_name:value.new_name,short_id:value.short_id===''?null:value.short_id,namespace_name:value.namespace_mode==='global'?null:value.namespace_name,expected_bundle_sha256:null}}
  function showCandidate(value){
    if(disposed)return;
    candidate=value;candidateReady=false;const generation=++candidateGeneration,frame=$('initial-diagram'),svg=new DOMParser().parseFromString(value.candidate_svg,'image/svg+xml').documentElement;
    if(svg.localName!=='svg')fail('presentation','Invalid native initial SVG');const width=Number(svg.getAttribute('width')),height=Number(svg.getAttribute('height'));if(!Number.isFinite(width)||!Number.isFinite(height)||width<=0||height<=0)fail('presentation','Invalid initial drawing bounds');
    $('candidate').hidden=false;const scale=candidateMode==='overview'?Math.min(1,frame.clientWidth/width,frame.clientHeight/height):1;
    $('font-status').textContent='Loading original diagram fonts…';
    frame.onload=async()=>{
      let timer;
      try{
        const loading=(async()=>{
          const doc=frame.contentDocument,actual=doc?.querySelector('svg');
          if(!actual)throw Error('The initial SVG did not load');
          svgBinding(actual,value);
          await doc.fonts.ready;
          for(const text of actual.querySelectorAll('text')){
            const style=doc.defaultView.getComputedStyle(text),family=style.fontFamily.replace(/^["']|["']$/g,'');
            const faces=await doc.fonts.load(style.fontWeight+' '+style.fontSize+' '+style.fontFamily,text.textContent);
            if(!['DejaVu Sans','DejaVu Sans Mono'].includes(family)||!faces.length||faces.some(face=>face.status!=='loaded'||face.family.replace(/^["']|["']$/g,'')!==family))throw Error('Original diagram fonts are unavailable');
          }
          svgBinding(actual,value);
        })();
        await Promise.race([loading,new Promise((_,reject)=>{timer=setTimeout(()=>reject(Error('Original diagram fonts did not become ready')),15000)})]);
        if(disposed||generation!==candidateGeneration)return;
        candidateReady=true;$('font-status').textContent=candidateMode==='overview'?'Overview · original fonts ready':'Readable size · original fonts ready';publish();
      }catch(error){if(disposed||generation!==candidateGeneration)return;candidateReady=false;notice('Unsupported view: '+error.message+'. The draft is retained; creation is disabled.')}
      finally{clearTimeout(timer)}
    };
    frame.srcdoc='<!doctype html><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{margin:0}svg{display:block;width:'+width*scale+'px;height:'+height*scale+'px}</style>'+value.candidate_svg;
    const root=value.candidate.elements[0];$('native-properties').textContent=root.kind==='parts'?'Part usage '+root.qualified_name+'; native owner '+(root.owner||'unnamed namespace')+'; noncomposite; no explicit typing; default 1..1.':'Part definition '+root.qualified_name+'; native owner '+(root.owner||'unnamed namespace')+'.';
    $('candidate-source').textContent=Object.entries(value.files).map(([name,text])=>name+'\n'+text).join('\n');$('candidate-identity').textContent='Engineering UUID '+root.element_id+' · checked bundle '+value.candidate_bundle_sha256;
    $('candidate-status').textContent='Native source and diagram checks passed. The candidate is unsaved.';
  }
  async function preview(){if(unknown||acknowledged||pending?.dispatched)fail('unconfirmed_save','Recover the initial creation before making another candidate.');const request=pending?.request||makeRequest();return run(async()=>{await persist();const result=await api('initial_preview',request);await verifyPreview(result.preview,request);pending={request:result.preview.request,request_sha256:result.preview.request_sha256,raw:raw(),dispatched:false};dirty=true;await persist();showCandidate(result.preview);notice('Unsaved candidate checked. Review it before creating the model.');return{outcome:'previewed',request:clone(pending.request)}})}
  async function acknowledge(receipt){verifyReceipt(receipt);if(!state.current_saved)state.current_saved={revision:1,commit:receipt.commit};acknowledged=clone(receipt);unknown=false;const storage=await retainOutcome();if(!disposed)$('receipt-summary').textContent='Created at revision 1. Opening the saved model reads its current revision.';notice('Model creation acknowledged. Open the same saved model to continue.'+storage)}
  async function save(){if(!pending||acknowledged||!unknown&&!candidateReady)fail('candidate_not_ready','A checked candidate with original fonts is required.');return run(async()=>{const wasDispatched=pending.dispatched,wasUnknown=unknown;pending.dispatched=true;unknown=true;try{await persist()}catch(error){pending.dispatched=wasDispatched;unknown=wasUnknown;storageReady=false;notice((wasDispatched||wasUnknown?'This attempt was not sent. The earlier creation remains unconfirmed. ':'This attempt was not sent. Retain the checked draft and repair intent storage. ')+error.message);return{outcome:'not_sent',request:clone(pending.request),unconfirmed_save:unknown,error:{code:error.code||'intent_storage',detail:error.message}}}if(disposed){pending.dispatched=wasDispatched;unknown=wasUnknown;await retainOutcome();return{outcome:'not_sent',request:clone(pending.request),unconfirmed_save:unknown,error:{code:'closed',detail:'Initial controller closed before dispatch.'}}}notice('Creating the checked model; the exact request is retained.');try{const result=await api('initial_apply',pending.request);verifyReceipt(result.receipt);const next=validateState(result.startup_state);if(next.current_saved)receiptObservation(result.receipt,next.current_saved.revision,next.current_saved.commit);state=next;await acknowledge(result.receipt);return{outcome:'committed',receipt:clone(acknowledged)}}catch(error){if(error.definitive_refusal){unknown=false;pending.dispatched=false;pending.refused=true;const storage=await retainOutcome();notice('Creation refused. The draft is retained. '+error.message+storage);return{outcome:'refused',error:{code:error.code||'refused',detail:error.message}}}unknown=true;const storage=await retainOutcome();notice('Creation unconfirmed. Recover or retry this exact request. '+error.message+storage);return{outcome:'unconfirmed',request:clone(pending.request),error:{code:error.code||'transport',detail:error.message}}}})}
  async function recover(){
    if(!pending?.dispatched)fail('retained_request','No dispatched initial request is retained.');
    return run(async()=>{
      try{
        const result=await api('initial_receipt',pending.request);
        if(result.request_sha256!==pending.request_sha256||!Number.isInteger(result.observed_revision)||result.observed_revision<0||result.observed_revision===0&&result.observed_commit!==null||result.observed_revision>0&&!commitId(result.observed_commit))fail('response_binding','Receipt observation does not match the retained initial request.');
        if(result.receipt){
          verifyReceipt(result.receipt);
          receiptObservation(result.receipt,result.observed_revision,result.observed_commit);
          observeHead(result.observed_revision,result.observed_commit);await acknowledge(result.receipt);return{outcome:'committed',...result};
        }
        if(acknowledged)fail('response_binding','The previously acknowledged first receipt is unavailable.');
        observeHead(result.observed_revision,result.observed_commit);unknown=true;const storage=await retainOutcome();notice('No matching receipt observed at revision '+result.observed_revision+'. This does not reserve the target. Retry the same creation.'+storage);return{outcome:'not_observed',...result};
      }catch(error){
        unknown=!acknowledged;const storage=await retainOutcome();notice((acknowledged?'The first receipt remains acknowledged; its current lookup is unavailable. ':'Creation remains unconfirmed. ')+error.message+storage);
        return{outcome:acknowledged?'receipt_unavailable':'unconfirmed',error:{code:error.code||'transport',detail:error.message}};
      }
    });
  }
  async function openSaved(){if(!acknowledged||!pending)fail('receipt','Recover a matching initial receipt before opening the saved project.');return run(async()=>{const result=await api('initial_open',pending.request);verifyOpen(result);observeHead(result.state.revision,result.state.commit);await retainOutcome();if(disposed)fail('closed','The initial controller closed before the saved-model handoff.');await provider.openSaved(result);return{outcome:'opened',receipt:clone(acknowledged)}})}
  $('initial-form').onsubmit=event=>{event.preventDefault();preview().catch(error=>notice(error.message))};
  for(const id of ['root-kind','root-name','root-short','namespace-mode','package-name'])$(id).addEventListener('input',async()=>{dirty=true;meaning();interaction++;try{await persist()}catch(error){storageReady=false;notice(error.message)}publish()});
  $('create-initial').onclick=()=>save().catch(error=>notice(error.message));$('recover-initial').onclick=()=>recover().catch(error=>notice(error.message));$('open-saved').onclick=()=>openSaved().catch(error=>notice(error.message));$('edit-draft').onclick=async()=>{try{await discardPreview()}catch(error){notice(error.message)}};
  for(const mode of ['readable','overview'])$('candidate-'+mode).onclick=()=>{candidateMode=mode;if(candidate)showCandidate(candidate)};
  const resized=()=>{if(!disposed&&candidate&&candidateMode==='overview')showCandidate(candidate)};addEventListener('resize',resized);
  globalThis.cseInitialWorkbench=Object.freeze({context,async dispose(){if(disposed)return;raw();disposed=true;connected=false;candidateGeneration++;candidate=null;removeEventListener('resize',resized);$('initial-diagram').onload=null;subscribers.clear();registration.status='disposed';for(const name of [...registration.registered])await retireTool(name)},subscribe(callback){subscribers.add(callback);return()=>subscribers.delete(callback)},preview,save,recover,openSaved});
  const registration={status:'unsupported',registered:[],errors:[],claim:'registration_is_not_actual_host_qualification'};globalThis.cseInitialSiteTools=registration;
  async function retireTool(name){if(typeof document.modelContext?.unregisterTool!=='function'){registration.status='disposed_cleanup_unavailable';registration.errors.push({name,detail:'This host cannot unregister the closed initial tool.'});return}try{await document.modelContext.unregisterTool(name);registration.registered=registration.registered.filter(value=>value!==name)}catch(error){registration.status='disposed_cleanup_unavailable';registration.errors.push({name,detail:String(error)})}}
  const object=properties=>({type:'object',properties,required:Object.keys(properties),additionalProperties:false}),text={type:'string'},nullable={type:['string','null']},guardSchema=object({project_id:text,root_element_id:text,view_id:text,model_revision:{const:0},ui_session_id:text,interaction_revision:{type:'integer',minimum:0}}),requestSchema=object({operation:{const:'initialize_physical_project'},request_id:text,project_id:text,root_element_id:text,view_id:text,expected_revision:{const:0},root_kind:{enum:['definition','usage']},new_name:text,short_id:nullable,namespace_name:nullable,expected_bundle_sha256:text});
  const tools=[
    ['cse_get_initial_context','Read the prospective root, exact draft, candidate and recovery state. No saved projection or engineering acceptance is inferred.',{},true,async()=>({outcome:'observed'})],
    ['cse_preview_initial_model','Preview the first native physical root using the visible form and shared native operation. Refuses to replace an existing draft. Save separately.',{guard:guardSchema,root_kind:{enum:['definition','usage']},new_name:text,short_id:nullable,namespace_name:nullable},false,async args=>{guard(args.guard);if(dirty||pending||unknown||acknowledged)fail('retained_draft','The initial form already has retained work.');if(!['definition','usage'].includes(args.root_kind)||typeof args.new_name!=='string'||!args.new_name||args.short_id!==null&&(typeof args.short_id!=='string'||!args.short_id)||args.namespace_name!==null&&(typeof args.namespace_name!=='string'||!args.namespace_name))fail('input','Supply root kind and decoded name fields, with null for omitted short ID/package.');for(const [id,value]of [['root-name',args.new_name],['root-short',args.short_id||''],['package-name',args.namespace_name||'']]){const probe=$(id).cloneNode(false);probe.value=value;if(probe.value!==value)fail('name','Names must be single-line text. No form values were changed.')}fields({root_kind:args.root_kind,new_name:args.new_name,short_id:args.short_id||'',namespace_mode:args.namespace_name===null?'global':'package',namespace_name:args.namespace_name||''});dirty=true;interaction++;return preview()}],
    ['cse_preview_current_initial_draft','Preview the retained visible initial form without replacing its raw fields.',{guard:guardSchema},false,async args=>{guard(args.guard);return preview()}],
    ['cse_save_initial_model','Create the exact checked initial model. The typed request and preview digest must match the retained candidate; returns a durable first receipt or unconfirmed outcome.',{guard:guardSchema,request:requestSchema},false,async args=>{guard(args.guard);exactPending(args.request);return save()}],
    ['cse_recover_initial_creation','Look up the exact dispatched first request. Absence is an observation, never a reservation or proof that another attempt cannot finish.',{guard:guardSchema,request:requestSchema},true,async args=>{guard(args.guard);exactPending(args.request);return recover()}],
    ['cse_open_initialized_project','Open the existing saved-model editor after recovering the matching first receipt. Reads the current saved revision without reinitializing.',{guard:guardSchema,request:requestSchema},false,async args=>{guard(args.guard);exactPending(args.request);return openSaved()}],
    ['cse_edit_initial_draft','Return an undispatched candidate to its retained raw form. Dispatched or unconfirmed creations must be recovered.',{guard:guardSchema},false,async args=>{guard(args.guard);await discardPreview();return{outcome:'draft_retained'}}],
  ];
  if(typeof document.modelContext?.registerTool==='function'){registration.status='registering';(async()=>{for(const [name,description,properties,readOnly,execute]of tools){if(disposed)break;try{await document.modelContext.registerTool({name,description,inputSchema:object(properties),annotations:{readOnlyHint:readOnly},execute:async args=>{try{if(disposed)fail('closed','The initial controller is closed.');exact(args,Object.keys(properties));return{action:name,...await execute(args),context:context()}}catch(error){return{action:name,outcome:'refused',error:{code:error.code||'unavailable',detail:error.message},context:context()}}}});registration.registered.push(name);if(disposed){await retireTool(name);break}}catch(error){registration.errors.push({name,detail:String(error)})}}if(!disposed)registration.status=registration.errors.length?'partial':'registered'})()}
  (async()=>{
    try{
      provider=host();
      if(builtinProvider){
        const access=new URLSearchParams(location.hash.slice(1)).get('access');
        if(access){await api('session',{access});history.replaceState(null,'',location.pathname)}
      }
      const result=await api('initial_state');state=validateState(result.state);csrf=result.csrf;
      const value=await provider.intentStorage.getItem(key());
      if(disposed)return;
      if(value!==null)await restoreRetained(JSON.parse(value));
      if(disposed)return;
      connected=true;meaning();publish();
      if(acknowledged){$('receipt-summary').textContent='First receipt retained. Opening revalidates the current saved model.';notice('Initial receipt retained. Open saved model to continue.')}
      else if(unknown)notice('A dispatched creation is unconfirmed. Recover or retry the exact request.');
      else if(pending){
        notice('Checked initial draft retained. Restoring its exact candidate.');
        try{await preview()}catch(error){notice('Retained candidate could not be refreshed. Edit the retained draft explicitly. '+error.message)}
      }else notice(state.target_observation==='unavailable'?'Target storage is unavailable. The initial draft remains editable; no save is acknowledged.':'Define the first native root, then preview it.');
    }catch(error){connected=false;candidateReady=false;notice('Initial session unavailable: '+error.message)}
  })();
})();
