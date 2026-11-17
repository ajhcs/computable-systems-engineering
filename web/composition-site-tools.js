'use strict';
// Host adapter only. Saved artwork and engineering decisions stay in the native
// reader/backend; all edits use the same controller as the visible controls.
// Contract: https://learn.chatgpt.com/docs/webmcp (2026-11-17).
(()=>{
  const object=properties=>({type:'object',properties,required:Object.keys(properties),additionalProperties:false});
  const text={type:'string'}, nullableText={type:['string','null']}, integer={type:'integer',minimum:1};
  const guardSchema=object({project_id:text,view_id:text,ui_session_id:text,model_revision:integer,
    commit:text,bundle_sha256:text,interaction_revision:{type:'integer',minimum:0},
    selected_element_id:nullableText,selected_occurrence_id:nullableText,editing_element_id:nullableText,editing_occurrence_id:nullableText,
    navigation_revision:{type:'integer',minimum:0},viewport_mode:{enum:['overview','readable']},viewport_left:{type:'number'},viewport_top:{type:'number'}});
  const boxSchema=object(Object.fromEntries(['x','y','width','height'].map(key=>[key,{type:'number'}])));
  const placementSchema={anyOf:[{type:'null'},object({box:boxSchema,points:{type:'array',minItems:2,maxItems:128,items:{type:'array',minItems:2,maxItems:2,items:{type:'number'}}}})]};
  const changeFields={operation:text,request_id:text,expected_revision:integer};
  const multiplicityBound={type:'integer',minimum:0,maximum:2147483647};
  const usageMultiplicitySchema={anyOf:[{type:'null'},object({lower:multiplicityBound,upper:multiplicityBound})]};
  const requestSchema={oneOf:[
    object({...changeFields,operation:{const:'rename'},element_id:text,new_name:text}),
    object({...changeFields,operation:{const:'create_definition'},owner_id:text,element_id:text,new_name:text,short_id:nullableText,view_id:text,placement:placementSchema}),
    object({...changeFields,operation:{const:'create_usage'},owner_id:text,element_id:text,new_name:text,short_id:nullableText,type_id:nullableText,is_composite:{type:'boolean'},multiplicity:usageMultiplicitySchema,view_id:text,placement:placementSchema}),
    object({...changeFields,operation:{const:'set_multiplicity'},element_id:text,lower:multiplicityBound,upper:multiplicityBound}),
    object({...changeFields,operation:{const:'set_layout'},layout:{type:'object'}}),
    object({...changeFields,operation:{const:'restore'},target_revision:integer}),
  ]};
  const fail=(code,message)=>{const error=new Error(message);error.code=code;throw error;};
  function exact(value,keys){
    if(!value||typeof value!=='object'||Array.isArray(value)||Object.keys(value).length!==keys.length||keys.some(key=>!Object.hasOwn(value,key)))fail('input','Supply exactly the documented fields.');
  }
  const context=()=>globalThis.cseWorkbench.context();
  function checkGuard(expected){
    const actual=context();
    if(!actual.ready)fail('view_not_ready','Wait for the saved view, then read its context.');
    exact(expected,Object.keys(actual.guard));
    if(Object.keys(actual.guard).some(key=>expected[key]!==actual.guard[key]))fail('stale_context','The project, view, selection or retained edit changed. Read context again.');
    if(busy||gestureActive)fail('interaction_busy','A human or agent operation is in progress. Read context after it finishes.');
  }
  function cleanTarget(element){
    if(unknown||pending||dirty)fail('retained_edit','An existing draft, checked change or unconfirmed save must be resolved explicitly.');
    if(!selectedId||element!==selectedId||element!==editTargetId||selectedOccurrenceId!==editTargetOccurrenceId||!editingNode())fail('target','Inspect and select the exact editing target before preparing this change.');
  }
  function select(element,occurrence){
    const rows=state.projection.inspection.occurrences,row=Object.hasOwn(rows,occurrence)?rows[occurrence]:null;
    if(!row||row.element_id!==element)fail('target','Native UUID (or null) and occurrence must identify the same saved inspection.');
    if(!frame.contentWindow.cseReaderSelection.select(occurrence,{reveal:true,focus:true}))fail('interaction_busy','Finish the active gesture first.');
    selectionChanged();frame.scrollIntoView({block:'nearest',inline:'nearest'});return{outcome:'selected'};
  }
  const definitions=[
    ['cse_get_context','Read the visible saved physical model, native selection, fixed edit target, draft, history and separately retained configuration findings. Does not refresh or mutate.',{},true,async()=>{
      const head=await api('/api/head');return{outcome:'observed',latest_observed_commit:head.commit};
    }],
    ['cse_select_element','Select an exact saved frame, declaration row or retained-role occurrence. Supply its native UUID, or null for an unresolved logical role. Retains draft target and review scope; inspection never accepts a new selection.',{guard:guardSchema,element_id:nullableText,occurrence_id:text},false,args=>{
      checkGuard(args.guard);return select(args.element_id,args.occurrence_id);
    }],
    ['cse_list_inspection_occurrences','Read a bounded page of source-bound frames, declarations or retained roles from this exact saved revision. This never narrows complete retained review scope. Use an exact returned occurrence and native UUID/null for inspection.',{guard:guardSchema,origin:{enum:[null,'frame','declaration','configuration_root','selected_role','external_role']},offset:{type:'integer',minimum:0},limit:{type:'integer',minimum:1,maximum:100}},true,async args=>{
      checkGuard(args.guard);const result=await api('/api/inspection',{expected_revision:state.revision,expected_bundle_sha256:state.projection.bundle_sha256,origin:args.origin,offset:args.offset,limit:args.limit});return{outcome:'observed',...result};
    }],
    ['cse_set_view_mode','Show the complete saved SVG overview or reveal the selection at readable size (100%). Changes this browser viewport only; retains drafts, native source, saved layout, identities and review scope.',{guard:guardSchema,mode:{enum:['overview','readable']}},false,args=>{
      checkGuard(args.guard);return{outcome:'navigated',navigation:frame.contentWindow.cseDiagramNavigation.mode(args.mode)};
    }],
    ['cse_preview_rename','Prepare an unsaved declared-name change on the selected editing target using the native validator. Supply the name itself; spaces, punctuation and literal quotes are retained, and source quoting is automatic. Refuses to replace any existing draft. Save separately after reviewing impact and retained configuration findings.',{guard:guardSchema,element_id:text,new_name:{type:'string',minLength:1,maxLength:64}},false,async args=>{
      checkGuard(args.guard);cleanTarget(args.element_id);
      if(typeof args.new_name!=='string')fail('input','Declared name must be text.');
      const input=byId('rename-name'),probe=input.cloneNode(false);probe.value=args.new_name;
      if(probe.value!==args.new_name)fail('name','The declared name must be a single line. The requested text was not changed or applied.');
      byId('rename-name').value=args.new_name;dirty=true;
      return await previewRename();
    }],
    ['cse_preview_create_definition','Prepare one native part definition owned by the selected definition, with a candidate diagram. Supply decoded name/optional short ID and automatic (null) or exact frame/route placement. Preserves existing geometry and retained scope. Save separately.',{guard:guardSchema,owner_id:text,new_name:{type:'string',minLength:1,maxLength:64},short_id:nullableText,placement:placementSchema},false,async args=>{
      checkGuard(args.guard);cleanTarget(args.owner_id);
      if(state.projection.mode!=='definitions'||editingNode()?.[1].kind!=='PartDefinition'||!Object.values(state.projection.nodes).some(n=>n.element_id===args.owner_id))fail('element_kind','Select an owner in a definition hierarchy.');
      const values={'create-name':args.new_name,'create-short':args.short_id===null?'':args.short_id};
      if(typeof args.new_name!=='string'||args.short_id!==null&&(typeof args.short_id!=='string'||args.short_id===''))fail('name','Supply name text and either a nonempty short ID or null.');
      for(const [id,value]of Object.entries(values)){const probe=byId(id).cloneNode(false);probe.value=value;if(probe.value!==value)fail('name','Creation names must be single-line text; no values were changed.');}
      if(args.placement!==null){exact(args.placement,['box','points']);exact(args.placement.box,['x','y','width','height']);if(!Object.values(args.placement.box).every(Number.isFinite)||!Array.isArray(args.placement.points)||args.placement.points.length<2||args.placement.points.length>128||args.placement.points.some(p=>!Array.isArray(p)||p.length!==2||!p.every(Number.isFinite)))fail('input','Supply finite frame coordinates and route points.');}
      for(const [id,value]of Object.entries(values))byId(id).value=value;
      byId('create-placement').value=args.placement===null?'automatic':'manual';
      if(args.placement!==null){for(const [key,value]of Object.entries(args.placement.box))byId('create-'+key).value=value;byId('create-points').value=args.placement.points.map(p=>p.join(',')).join('\n');}
      dirty=true;return await previewCreateDefinition();
    }],
    ['cse_preview_create_usage','Prepare one native part usage under the selected native owner. Choose composite/reference, an existing definition UUID or null for no explicit typing, and native default or finite multiplicity. Owned usage frames and declaration-only rows remain distinct; retained configuration scope is unchanged. Save separately.',{guard:guardSchema,owner_id:text,new_name:{type:'string',minLength:1,maxLength:64},short_id:nullableText,type_id:nullableText,is_composite:{type:'boolean'},multiplicity:usageMultiplicitySchema,placement:placementSchema},false,async args=>{
      checkGuard(args.guard);cleanTarget(args.owner_id);
      if(typeof args.new_name!=='string'||args.short_id!==null&&(typeof args.short_id!=='string'||args.short_id===''))fail('name','Supply name text and either a nonempty short ID or null.');
      const values={'usage-name':args.new_name,'usage-short':args.short_id===null?'':args.short_id};
      for(const [id,value]of Object.entries(values)){const probe=byId(id).cloneNode(false);probe.value=value;if(probe.value!==value)fail('name','Creation names must be single-line text; no values were changed.');}
      if(typeof args.is_composite!=='boolean')fail('input','Choose composite or reference explicitly.');
      if(args.type_id!==null&&(typeof args.type_id!=='string'||!state.projection.inspection.declarations.some(id=>{const row=state.projection.inspection.occurrences[id];return row.element_id===args.type_id&&row.kind==='PartDefinition'})))fail('identity','Choose an existing part-definition UUID or null for no explicit typing.');
      if(args.multiplicity!==null){exact(args.multiplicity,['lower','upper']);const {lower,upper}=args.multiplicity;if(!Number.isInteger(lower)||!Number.isInteger(upper)||lower<0||upper<lower||upper>2147483647)fail('multiplicity','Supply finite integer bounds 0 <= lower <= upper <= 2147483647.');}
      if(args.placement!==null){exact(args.placement,['box','points']);exact(args.placement.box,['x','y','width','height']);if(!Object.values(args.placement.box).every(Number.isFinite)||!Array.isArray(args.placement.points)||args.placement.points.length<2||args.placement.points.length>128||args.placement.points.some(p=>!Array.isArray(p)||p.length!==2||!p.every(Number.isFinite)))fail('input','Supply finite frame coordinates and route points.');}
      for(const [id,value]of Object.entries(values))byId(id).value=value;
      byId('usage-type').value=args.type_id||'';byId('usage-kind').value=args.is_composite?'composite':'reference';byId('usage-multiplicity').value=args.multiplicity===null?'default':'finite';
      for(const bound of ['lower','upper'])byId('usage-'+bound).value=args.multiplicity===null?'':args.multiplicity[bound];
      byId('usage-placement').value=args.placement===null?'automatic':'manual';
      if(args.placement!==null){for(const [key,value]of Object.entries(args.placement.box))byId('usage-'+key).value=value;byId('usage-points').value=args.placement.points.map(p=>p.join(',')).join('\n');}
      dirty=true;return await previewCreateUsage();
    }],
    ['cse_preview_multiplicity','Prepare explicit finite lower/upper bounds on the selected native part usage. Uses the visible bounds controller and native validator; retains names, ownership, identities and required configuration scope. Definitions have no usage multiplicity. Save separately after reviewing findings.',{guard:guardSchema,element_id:text,lower:multiplicityBound,upper:multiplicityBound},false,async args=>{
      checkGuard(args.guard);cleanTarget(args.element_id);
      if(editingNode()?.[1].kind!=='PartUsage')fail('element_kind','Multiplicity belongs to a part usage.');
      if(!Number.isInteger(args.lower)||!Number.isInteger(args.upper)||args.lower<0||args.upper<args.lower||args.upper>2147483647)fail('multiplicity','Supply integer bounds 0 <= lower <= upper <= 2147483647.');
      byId('multiplicity-lower').value=args.lower;byId('multiplicity-upper').value=args.upper;dirty=true;
      return await previewMultiplicity();
    }],
    ['cse_preview_layout','Prepare unsaved x/y/width/height for the selected frame. Calls the visible layout controller and native geometry checks. Changes presentation only; never changes native ownership.',{guard:guardSchema,element_id:text,box:boxSchema},false,async args=>{
      checkGuard(args.guard);cleanTarget(args.element_id);if(!editingNode()?.[1].frame_id)fail('not_framed','This inspection row has no frame geometry.');exact(args.box,['x','y','width','height']);
      if(Object.values(args.box).some(value=>typeof value!=='number'||!Number.isFinite(value)))fail('input','Bounds must be finite numbers.');
      for(const field of Object.keys(args.box))byId('box-'+field).value=args.box[field];
      dirty=true;return await previewLayout();
    }],
    ['cse_preview_restore','Prepare restoration of all model, identity and presentation state from a saved revision into a NEW monotonic revision. Refuses to replace existing drafts. This is whole-project snapshot restoration.',{guard:guardSchema,target_revision:integer},false,async args=>{
      checkGuard(args.guard);if(unknown||pending||dirty)fail('retained_edit','Resolve the existing draft, checked change or unconfirmed save explicitly.');
      if(!Number.isInteger(args.target_revision)||!state.history.some(row=>row.revision===args.target_revision))fail('input','Select a saved revision of this project.');
      byId('restore-target').value=args.target_revision;return await previewRestore();
    }],
    ['cse_preview_current_edit','Check the existing visible form values on their retained editing target. Does not replace or retarget a human draft. Choose owned-definition creation, declared-name, multiplicity, frame-layout or whole-project restoration explicitly; save separately.',{guard:guardSchema,kind:{enum:['create_definition','create_usage','rename','multiplicity','layout','restore']}},false,async args=>{
      checkGuard(args.guard);
      if(unknown||pending||!editingNode()&&args.kind!=='restore')fail('retained_edit','Resolve the pending change or unconfirmed save before another preview.');
      if(dirty&&draftKind&&draftKind!==args.kind)fail('retained_edit','Check the existing draft in its own form, or explicitly discard it first.');
      const previews={create_definition:previewCreateDefinition,create_usage:previewCreateUsage,rename:previewRename,multiplicity:previewMultiplicity,layout:previewLayout,restore:previewRestore};
      if(typeof args.kind!=='string'||!Object.hasOwn(previews,args.kind))fail('input','Choose create_definition, create_usage, rename, multiplicity, layout or restore.');
      const preview=previews[args.kind];
      return await preview();
    }],
    ['cse_save_change','Durably save or retry the exact checked request ID already visible in this tab. Uses the same native Git transaction as the Save button. Returns a durable receipt, definite refusal, or unconfirmed outcome; never infer success from a preview.',{guard:guardSchema,request_id:text},false,async args=>{
      checkGuard(args.guard);
      if(!pending||pending.request.request_id!==args.request_id)fail('pending_request','The requested change is not the exact retained preview or retry.');
      return await saveChange();
    }],
    ['cse_discard_change','Explicitly discard the current unsaved form/checked change. Saved project is unchanged. Refuses to discard an unconfirmed save.',{guard:guardSchema},false,args=>{
      checkGuard(args.guard);if(unknown)fail('outcome_unknown','Resolve the exact unconfirmed save before discarding.');
      discard();return{outcome:'discarded'};
    }],
    ['cse_refresh_project','Refresh the saved view while retaining form values on their original target. A confirmed preview must be checked again; an unconfirmed save retains its exact retry request.',{guard:guardSchema},false,async args=>{
      checkGuard(args.guard);return await refreshSaved();
    }],
    ['cse_lookup_receipt','Read the durable receipt for an EXACT prior request, including after a lost tool response or page reload. Never reapplies it. Null receipt means absent only at the returned observed head; it does not prove a concurrent save will never publish.',{request:requestSchema},true,async args=>{
      try{const result=await api('/api/receipt',args.request);return{outcome:result.receipt?'committed':'not_observed',...result};}
      catch(error){return{outcome:'unconfirmed',request:clone(args.request),error:{code:error.code||'receipt_unavailable',detail:error.message}};}
    }],
  ];
  const registration={status:'unsupported',registered:[],errors:[],claim:'registration_is_not_actual_host_qualification'};
  globalThis.cseSiteTools=registration;
  if(typeof document.modelContext?.registerTool!=='function')return;
  registration.status='registering';
  (async()=>{
    for(const [name,description,properties,readOnly,execute]of definitions){
      try{
        await document.modelContext.registerTool({name,description,inputSchema:object(properties),annotations:{readOnlyHint:readOnly},
          execute:async args=>{
            try{exact(args,Object.keys(properties));const result=await execute(args);return{action:name,...result,context:context()};}
            catch(error){return{action:name,outcome:'refused',error:{code:error.code||'unavailable',detail:error.message},context:context()};}
          }});
        registration.registered.push(name);
      }catch(error){registration.errors.push({name,detail:String(error)});}
    }
    registration.status=registration.errors.length?'partial':'registered';
  })();
})();
