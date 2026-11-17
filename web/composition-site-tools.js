'use strict';
// Host adapter only. Saved artwork and engineering decisions stay in the native
// reader/backend; all edits use the same controller as the visible controls.
// Contract: https://learn.chatgpt.com/docs/webmcp (2026-11-17).
(()=>{
  const object=properties=>({type:'object',properties,required:Object.keys(properties),additionalProperties:false});
  const text={type:'string'}, nullableText={type:['string','null']}, integer={type:'integer',minimum:1};
  const guardSchema=object({project_id:text,view_id:text,ui_session_id:text,model_revision:integer,
    commit:text,bundle_sha256:text,interaction_revision:{type:'integer',minimum:0},
    selected_element_id:nullableText,selected_occurrence_id:nullableText,editing_element_id:nullableText,
    navigation_revision:{type:'integer',minimum:0},viewport_mode:{enum:['overview','readable']},viewport_left:{type:'number'},viewport_top:{type:'number'}});
  const boxSchema=object(Object.fromEntries(['x','y','width','height'].map(key=>[key,{type:'number'}])));
  const changeFields={operation:text,request_id:text,expected_revision:integer};
  const requestSchema={oneOf:[
    object({...changeFields,operation:{const:'rename'},element_id:text,new_name:text}),
    object({...changeFields,operation:{const:'set_layout'},layout:{type:'object'}}),
    object({...changeFields,operation:{const:'restore'},target_revision:integer}),
  ]};
  const fail=(code,message)=>{const error=new Error(message);error.code=code;throw error;};
  function exact(value,keys){
    if(!value||typeof value!=='object'||Array.isArray(value)||Object.keys(value).length!==keys.length||keys.some(key=>!Object.hasOwn(value,key)))fail('input','Supply exactly the documented fields.');
  }
  function context(){
    if(!state)return{ready:false,claim:'local_site_adapter_not_application_qualified'};
    const found=selectedNode(),target=editingNode();
    const navigation=frameReady?frame.contentWindow.cseDiagramNavigation.state():null;
    return clone({ready:frameReady,
      guard:{project_id:state.projection.project_id,view_id:state.projection.id,ui_session_id:uiSession,
        model_revision:state.revision,commit:state.commit,bundle_sha256:state.projection.bundle_sha256,
        interaction_revision:draftGeneration,selected_element_id:found?.[1].element_id||null,
        selected_occurrence_id:found?.[0]||null,editing_element_id:editTargetId||null,
        navigation_revision:navigation?.revision||0,viewport_mode:navigation?.mode||'readable',viewport_left:navigation?.scroll_left||0,viewport_top:navigation?.scroll_top||0},
      navigation,
      busy,gesture_active:gestureActive,has_form_draft:dirty,unconfirmed_save:unknown,
      selection:found?{occurrence_id:found[0],...found[1],display_label:state.display_labels[found[0]],box:state.layout.nodes[found[0]]}:null,
      editing_target:target?{element_id:editTargetId,occurrence_id:target[0],native_name:target[1].element,
        base_revision:formRevision,base_commit:formCommit,declared_name:byId('rename-name').value,
        box:Object.fromEntries(['x','y','width','height'].map(field=>[field,byId('box-'+field).value]))}:null,
      pending_change:pending?{...pending,request:clone(pending.request)}:null,
      restoration_target_revision:Number(byId('restore-target').value)||null,
      visible_elements:Object.entries(state.projection.nodes).map(([id,node])=>({occurrence_id:id,element_id:node.element_id,native_name:node.element,kind:node.kind})),
      history:state.history,configuration_reviews:state.configuration_reviews,reconciliation:state.reconciliation,
      scope:'visible_saved_selection_never_replaces_retained_review_scope',
      claim:'local_site_adapter_not_application_qualified'});
  }
  function checkGuard(expected){
    const actual=context();
    if(!actual.ready)fail('view_not_ready','Wait for the saved view, then read its context.');
    exact(expected,Object.keys(actual.guard));
    if(Object.keys(actual.guard).some(key=>expected[key]!==actual.guard[key]))fail('stale_context','The project, view, selection or retained edit changed. Read context again.');
    if(busy||gestureActive)fail('interaction_busy','A human or agent operation is in progress. Read context after it finishes.');
  }
  function cleanTarget(element){
    if(unknown||pending||dirty)fail('retained_edit','An existing draft, checked change or unconfirmed save must be resolved explicitly.');
    if(!selectedId||element!==selectedId||element!==editTargetId)fail('target','Inspect and select the exact editing target before preparing this change.');
  }
  function select(element,occurrence){
    const node=state.projection.nodes[occurrence];
    if(!node||node.element_id!==element)fail('target','Element and occurrence must identify the same saved frame.');
    const group=[...frame.contentDocument.querySelectorAll('g[data-node-id]')].find(item=>item.dataset.nodeId===occurrence);
    if(!group)fail('view_not_ready','The saved frame is unavailable.');
    group.dispatchEvent(new MouseEvent('click',{bubbles:true}));
    frame.contentWindow.cseDiagramNavigation.reveal(occurrence);
    selectionChanged();
    return{outcome:'selected'};
  }
  const definitions=[
    ['cse_get_context','Read the visible saved physical model, native selection, fixed edit target, draft, history and separately retained configuration findings. Does not refresh or mutate.',{},true,async()=>{
      const head=await api('/api/head');return{outcome:'observed',latest_observed_commit:head.commit};
    }],
    ['cse_select_element','Select and reveal an exact engineering UUID and diagram occurrence in the saved view. Retains existing edits and review scope; changes inspection only.',{guard:guardSchema,element_id:text,occurrence_id:text},false,args=>{
      checkGuard(args.guard);return select(args.element_id,args.occurrence_id);
    }],
    ['cse_set_view_mode','Show the complete saved SVG overview or reveal the selection at readable size (100%). Changes this browser viewport only; retains drafts, native source, saved layout, identities and review scope.',{guard:guardSchema,mode:{enum:['overview','readable']}},false,args=>{
      checkGuard(args.guard);return{outcome:'navigated',navigation:frame.contentWindow.cseDiagramNavigation.mode(args.mode)};
    }],
    ['cse_preview_rename','Prepare an unsaved declared-name change on the selected editing target using the native validator. Refuses to replace any existing draft. Save separately after reviewing impact and retained configuration findings.',{guard:guardSchema,element_id:text,new_name:{type:'string',minLength:1,maxLength:64}},false,async args=>{
      checkGuard(args.guard);cleanTarget(args.element_id);
      if(typeof args.new_name!=='string')fail('input','Declared name must be text.');
      byId('rename-name').value=args.new_name;dirty=true;
      return await previewRename();
    }],
    ['cse_preview_layout','Prepare unsaved x/y/width/height for the selected frame. Calls the visible layout controller and native geometry checks. Changes presentation only; never changes native ownership.',{guard:guardSchema,element_id:text,box:boxSchema},false,async args=>{
      checkGuard(args.guard);cleanTarget(args.element_id);exact(args.box,['x','y','width','height']);
      if(Object.values(args.box).some(value=>typeof value!=='number'||!Number.isFinite(value)))fail('input','Bounds must be finite numbers.');
      for(const field of Object.keys(args.box))byId('box-'+field).value=args.box[field];
      dirty=true;return await previewLayout();
    }],
    ['cse_preview_restore','Prepare restoration of all model, identity and presentation state from a saved revision into a NEW monotonic revision. Refuses to replace existing drafts. This is whole-project snapshot restoration.',{guard:guardSchema,target_revision:integer},false,async args=>{
      checkGuard(args.guard);cleanTarget(selectedId);
      if(!Number.isInteger(args.target_revision)||!state.history.some(row=>row.revision===args.target_revision))fail('input','Select a saved revision of this project.');
      byId('restore-target').value=args.target_revision;return await previewRestore();
    }],
    ['cse_preview_current_edit','Check the existing visible form values on their retained editing target. Does not replace or retarget a human draft. Choose declared-name, frame-layout or whole-project restoration explicitly; save separately.',{guard:guardSchema,kind:{enum:['rename','layout','restore']}},false,async args=>{
      checkGuard(args.guard);
      if(unknown||pending||!editingNode())fail('retained_edit','Resolve the pending change or unconfirmed save before another preview.');
      const previews={rename:previewRename,layout:previewLayout,restore:previewRestore};
      if(typeof args.kind!=='string'||!Object.hasOwn(previews,args.kind))fail('input','Choose rename, layout or restore.');
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
