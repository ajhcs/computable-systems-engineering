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
  const artworkIds={type:'array',minItems:1,maxItems:50,uniqueItems:true,items:text};
  const catalogDigest={type:'string',pattern:'^[a-f0-9]{64}$'};
  const frameStyleSchema=object({fill:text,stroke:text,text,align:{enum:['center','left']}});
  const frameArtworkFields={view_id:text,node_id:text,element_id:text,component_id:text,
    catalog_sha256:catalogDigest,svg_sha256:catalogDigest,
    legend:{anyOf:[{type:'null'},{type:'array',minItems:1,maxItems:5,items:{type:'string',minLength:1,maxLength:256}}]}};
  const connectorStyleFields={view_id:text,edge_id:text,source_id:text,target_id:text,swatch:text,
    palette_sha256:catalogDigest,legend:frameArtworkFields.legend};
  const viewKeyFields={view_id:text,master_sha256:catalogDigest,legend:frameArtworkFields.legend.anyOf[1]};
  const displayAliasFields={view_id:text,node_id:text,element_id:text,
    alias:{anyOf:[{type:'null'},{type:'string',minLength:1,maxLength:256}]}};
  const boxSchema=object(Object.fromEntries(['x','y','width','height'].map(key=>[key,{type:'number'}])));
  const placementSchema={anyOf:[{type:'null'},object({box:boxSchema,points:{type:'array',minItems:2,maxItems:128,items:{type:'array',minItems:2,maxItems:2,items:{type:'number'}}}})]};
  const ownerTarget=object({kind:{enum:['PartDefinition','PartUsage','Package','Namespace']},identity:text,file:text,bundle_sha256:text});
  const compositionTransition={anyOf:[{type:'null'},object({before:{type:'boolean'},after:{type:'boolean'}})]};
  const ownershipEffects={type:'array',maxItems:128,items:{oneOf:[object({view_id:text,action:{enum:['preserve_structure','remove_occurrences']}}),object({view_id:text,action:{const:'reparent'},parent_node:text,points:{type:'array',minItems:2,maxItems:128,items:{type:'array',minItems:2,maxItems:2,items:{type:'number'}}}})]}};
  const removalEffects={type:'array',maxItems:128,items:object({view_id:text,action:{enum:['close_view','remove_occurrences']},
    node_ids:{type:'array',maxItems:128,uniqueItems:true,items:text},edge_ids:{type:'array',maxItems:128,uniqueItems:true,items:text}})};
  const referenceEffects={type:'array',maxItems:16384,items:object({
    location:object({file:text,offset:{type:'integer',minimum:0},length:integer,encoding:{const:'codepoints'}}),replacement_id:nullableText})};
  const changeFields={operation:text,request_id:text,expected_revision:integer};
  const frameArtworkRequest=object({...changeFields,operation:{const:'set_frame_master'},...frameArtworkFields});
  frameArtworkRequest.properties.style=frameStyleSchema;
  const multiplicityBound={type:'integer',minimum:0,maximum:2147483647};
  const usageMultiplicitySchema={anyOf:[{type:'null'},object({lower:multiplicityBound,upper:multiplicityBound})]};
  const requestSchema={oneOf:[
    object({...changeFields,operation:{const:'rename'},element_id:text,new_name:text}),
    object({...changeFields,operation:{const:'create_definition'},owner_id:text,element_id:text,new_name:text,short_id:nullableText,view_id:text,placement:placementSchema}),
    object({...changeFields,operation:{const:'create_usage'},owner_id:text,element_id:text,new_name:text,short_id:nullableText,type_id:nullableText,is_composite:{type:'boolean'},multiplicity:usageMultiplicitySchema,view_id:text,placement:placementSchema}),
    object({...changeFields,operation:{const:'reparent'},element_id:text,destination:ownerTarget,composition_transition:compositionTransition,view_effects:ownershipEffects,checked_bundle_sha256:nullableText}),
    object({...changeFields,operation:{const:'delete'},element_id:text,reference_effects:referenceEffects,view_effects:removalEffects,checked_bundle_sha256:nullableText}),
    object({...changeFields,operation:{const:'remove_occurrence'},view_id:text,node_id:text,view_effects:removalEffects,checked_bundle_sha256:nullableText}),
    object({...changeFields,operation:{const:'set_types'},element_id:text,type_ids:{type:'array',maxItems:128,uniqueItems:true,items:text}}),
    object({...changeFields,operation:{const:'set_multiplicity'},element_id:text,lower:multiplicityBound,upper:multiplicityBound}),
    object({...changeFields,operation:{const:'set_layout'},layout:{type:'object'}}),
    frameArtworkRequest,
    object({...changeFields,operation:{const:'set_connector_style'},...connectorStyleFields}),
    object({...changeFields,operation:{const:'set_view_key'},...viewKeyFields}),
    object({...changeFields,operation:{const:'set_display_alias'},...displayAliasFields}),
    object({...changeFields,operation:{const:'restore'},target_revision:integer}),
  ]};
  const fail=(code,message)=>{const error=new Error(message);error.code=code;throw error;};
  function exact(value,keys){
    if(!value||typeof value!=='object'||Array.isArray(value)||Object.keys(value).length!==keys.length||keys.some(key=>!Object.hasOwn(value,key)))fail('input','Supply exactly the documented fields.');
  }
  const context=()=>globalThis.cseWorkbench.context();
  function checkGuard(expected,allowNoView=false){
    const actual=context();
    if(!actual.ready&&!(allowNoView&&initialized&&actual.view_available===false))fail('view_not_ready','Wait for the saved view, then read its context.');
    exact(expected,Object.keys(actual.guard));
    if(Object.keys(actual.guard).some(key=>expected[key]!==actual.guard[key]))fail('stale_context','The project, view, selection or retained edit changed. Read context again.');
    if(busy||gestureActive)fail('interaction_busy','A human or agent operation is in progress. Read context after it finishes.');
  }
  function cleanTarget(element){
    if(unknown||pending||dirty)fail('retained_edit','An existing draft, checked change or unconfirmed save must be resolved explicitly.');
    if(!selectedId||element!==selectedId||element!==editTargetId||selectedOccurrenceId!==editTargetOccurrenceId||!editingNode())fail('target','Inspect and select the exact editing target before preparing this change.');
  }
  async function previewFrameArtwork(args,style){
    checkGuard(args.guard);cleanTarget(args.element_id);
    if(!editingNode()[1].frame_id||editingNode()[1].frame_id!==args.node_id||state.projection.id!==args.view_id)
      fail('target','Choose the exact physical frame occurrence and its saved view.');
    if(args.legend!==null&&(!Array.isArray(args.legend)||args.legend.some(line=>typeof line!=='string'||line.includes('\n')||line.includes('\r')||line!==line.trim())))
      fail('input','Supply each key entry as exact single-line text.');
    if(style!==undefined){
      exact(style,['fill','stroke','text','align']);
      if(!state.appearance_palette||!['center','left'].includes(style.align)||
          ['fill','stroke','text'].some(key=>typeof style[key]!=='string'||!Object.hasOwn(state.appearance_palette.swatches,style[key])))
        fail('input','Choose exact saved swatches and an alignment.');
    }
    beginFrameMaster(args,args.legend,style);
    return await previewFrameMaster();
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
    ['cse_export_saved_view','Request an SVG or source-binding JSON download from the exact open saved view. The JSON includes complete saved configuration findings and the exact retained scope text. Uses the same verified transfer as the diagram links and preserves any pending edit.',{guard:guardSchema,kind:{enum:['view.svg','view.json']}},false,async args=>{
      checkGuard(args.guard);
      if(!['view.svg','view.json'].includes(args.kind))fail('input','Choose an SVG or source-binding JSON artifact.');
      return await transferSavedArtifact(savedArtifact(args.kind));
    }],
    ['cse_select_element','Select an exact saved frame, declaration row or retained-role occurrence. Supply its native UUID, or null for an unresolved logical role. Retains draft target and review scope; inspection never accepts a new selection.',{guard:guardSchema,element_id:nullableText,occurrence_id:text},false,args=>{
      checkGuard(args.guard);return select(args.element_id,args.occurrence_id);
    }],
    ['cse_list_inspection_occurrences','Read a bounded page of source-bound frames, declarations or retained roles from this exact saved revision. This never narrows complete retained review scope. Use an exact returned occurrence and native UUID/null for inspection.',{guard:guardSchema,origin:{enum:[null,'frame','declaration','configuration_root','selected_role','external_role']},offset:{type:'integer',minimum:0},limit:{type:'integer',minimum:1,maximum:100}},true,async args=>{
      checkGuard(args.guard,true);const result=await api('/api/inspection',{expected_revision:state.revision,expected_bundle_sha256:state.projection.bundle_sha256,origin:args.origin,offset:args.offset,limit:args.limit});return{outcome:'observed',...result};
    }],
    ['cse_read_retained_review','Read a bounded page of saved configuration findings using the exact review file and scope digest from context. Use next_offset for more findings. The selected element and any checked candidate remain separate.',{guard:guardSchema,file:text,scope_sha256:{type:'string',pattern:'^[a-f0-9]{64}$'},offset:{type:'integer',minimum:0},limit:{type:'integer',minimum:1,maximum:100}},true,async args=>{
      checkGuard(args.guard,true);
      const {guard:{project_id,model_revision:revision,commit,bundle_sha256},file,scope_sha256,offset,limit}=args;
      const result=await api('/api/retained-review',{revision,bundle_sha256,file,scope_sha256,offset,limit});
      const binding={project_id,revision,commit,bundle_sha256,file,scope_sha256,offset};
      if(Object.entries(binding).some(([key,value])=>result[key]!==value))
        fail('review_binding','The retained findings do not match the captured saved revision and scope.');
      return{...result,outcome:'observed'};
    }],
    ['cse_search_component_catalog','Search CSE artwork by name or ID. Use the same filters with the returned cursor.',{
      query:{type:'string',maxLength:256},family:nullableText,sysml:nullableText,
      limit:{type:'integer',minimum:1,maximum:50},cursor:nullableText,
    },true,async({query,family,sysml,limit,cursor})=>({
      ...await fetchCatalogPage({query,family,sysml},limit,cursor),outcome:'observed',
    })],
    ['cse_inspect_component_catalog','Inspect treatment, provenance and applicability for an exact artwork ID from a catalog page.',{
      component_id:text,catalog_sha256:{type:'string',pattern:'^[a-f0-9]{64}$'},
    },true,async({component_id,catalog_sha256})=>({
      ...await inspectCatalog(component_id,catalog_sha256,false),outcome:'observed',
    })],
    ['cse_validate_component_selection','Validate an explicit portable artwork selection against the packaged catalog.',{
      catalog_sha256:catalogDigest,component_ids:artworkIds,
    },true,async args=>({
      selection:await validateCatalogSelection({schema:catalogSelectionSchema,...args}),outcome:'observed',
    })],
    ['cse_get_component_selection','Read the artwork selection in this workbench session.',{},true,()=>({
      selection:catalogSelection?clone(catalogSelection):null,selection_revision:catalogSelectionGeneration,outcome:'observed',
    })],
    ['cse_set_component_selection','Replace the current artwork selection with an explicit exact-ID list, or clear it with null.',{
      guard:guardSchema,selection_revision:{type:'integer',minimum:0},
      selection:{anyOf:[{type:'null'},object({catalog_sha256:catalogDigest,component_ids:artworkIds})]},
    },false,async args=>{
      checkGuard(args.guard,true);
      if(args.selection_revision!==catalogSelectionGeneration)fail('stale_selection','Read the current artwork selection first.');
      const record=args.selection===null?null:await validateCatalogSelection({schema:catalogSelectionSchema,...args.selection});
      checkGuard(args.guard,true);
      if(args.selection_revision!==catalogSelectionGeneration)fail('stale_selection','The artwork selection changed. Read it again.');
      setCatalogSelection(record);
      byId('catalog-selection-status').textContent=(record?.component_ids.length||0)+' selected';
      return{selection:record,selection_revision:catalogSelectionGeneration,outcome:'selected'};
    }],
    ['cse_preview_frame_master','Preview the exact catalog rectangle master on the captured physical frame. Supply one to five key lines for a new appearance.',
      {guard:guardSchema,...frameArtworkFields},false,args=>previewFrameArtwork(args)],
    ['cse_preview_frame_style','Preview pinned frame artwork with exact fill, boundary and text swatches and label alignment.',
      {guard:guardSchema,...frameArtworkFields,style:frameStyleSchema},false,args=>previewFrameArtwork(args,args.style)],
    ['cse_preview_connector_style','Preview a saved swatch on a captured ownership connector with exact native endpoints.',
      {guard:guardSchema,...connectorStyleFields},false,async args=>{
      checkGuard(args.guard);
      if(unknown||pending||dirty)fail('retained_edit','Resolve the existing draft or pending change first.');
      const edge=observedConnector(args.edge_id);
      if(!edge||['view_id','source_id','target_id'].some(key=>edge[key]!==args[key]))
        fail('target','Use the exact connector and native endpoint identities from the saved view.');
      if(args.palette_sha256!==edge.palette_sha256)fail('stale_palette','Read the current palette before choosing a swatch.');
      if(typeof args.swatch!=='string'||!Object.hasOwn(state.appearance_palette.swatches,args.swatch))
        fail('input','Choose an exact saved swatch ID.');
      if(args.legend!==null&&(!Array.isArray(args.legend)||args.legend.some(line=>typeof line!=='string'||line.includes('\n')||line.includes('\r')||line!==line.trim())))
        fail('input','Supply each key entry as exact single-line text.');
      beginConnectorStyle(args);
      return await previewConnectorStyle();
    }],
    ['cse_preview_view_key','Preview the authored local key on the exact saved physical view and legend master.',
      {guard:guardSchema,...viewKeyFields},false,async args=>{
      checkGuard(args.guard);
      if(unknown||pending||dirty)fail('retained_edit','Resolve the existing draft or pending change first.');
      if(args.view_id!==state.view_key?.view_id)fail('target','Use the exact saved physical view.');
      if(args.master_sha256!==state.view_key.master_sha256)fail('stale_catalog','Read the current local key master first.');
      if(!Array.isArray(args.legend)||args.legend.length<1||args.legend.length>5||
          args.legend.some(line=>typeof line!=='string'||!line||line.length>256||/[\r\n]/.test(line)||line!==line.trim()))
        fail('input','Supply one to five exact single-line key entries.');
      beginViewKey(args);
      return await previewViewKey();
    }],
    ['cse_preview_display_alias','Preview a display alias for the selected physical frame in this view. Pass null to display the declared name.',{guard:guardSchema,...displayAliasFields},false,async args=>{
      checkGuard(args.guard);cleanTarget(args.element_id);
      if(editingNode()[1].frame_id!==args.node_id||state.projection.id!==args.view_id)
        fail('target','Use the selected native element, physical frame and saved view.');
      if(args.alias!==null&&(typeof args.alias!=='string'||!args.alias||[...args.alias].length>256||args.alias!==args.alias.trim()||/[\x00-\x1f]/.test(args.alias)))
        fail('input','Supply one line of alias text or null to display the declared name.');
      const input=byId('display-alias');
      input.value=args.alias??'';
      input.dispatchEvent(new Event('input',{bubbles:true}));
      return await previewDisplayAlias();
    }],
    ['cse_switch_saved_view','Open another available saved physical view in this project. Use an exact view ID returned in context and resolve any pending edits first.',{guard:guardSchema,view_id:text},false,async args=>{
      checkGuard(args.guard,true);return await switchSavedView(args.view_id);
    }],
    ['cse_set_view_mode','Show the complete saved SVG overview or reveal the selection at readable size (100%). Changes this browser viewport only; retains drafts, native source, saved layout, identities and review scope.',{guard:guardSchema,mode:{enum:['overview','readable']}},false,args=>{
      checkGuard(args.guard);return{outcome:'navigated',navigation:frame.contentWindow.cseDiagramNavigation.mode(args.mode)};
    }],
    ['cse_set_branch_visibility','Expand or collapse the selected visible frame branch at readable size. This changes only this diagram session.',{guard:guardSchema,occurrence_id:text,expanded:{type:'boolean'}},false,args=>{
      checkGuard(args.guard);
      const node=selectedNode()?.[1];
      if(!node?.frame_id||node.id!==args.occurrence_id)fail('target','Select the exact framed parent.');
      const navigation=frame.contentWindow.cseDiagramNavigation.branch(node.frame_id,args.expanded);
      return{outcome:'navigated',navigation};
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
    ['cse_read_model_source','Read an exact bounded SysML chunk from the captured saved project or an exact checked candidate. Codepoint offsets and chunk/file digests preserve Unicode and line endings. Source selection never replaces complete retained review scope. Available without requiring a rendered diagram when model context is initialized.',{guard:guardSchema,request:{anyOf:[{type:'null'},requestSchema]},file:text,offset:{type:'integer',minimum:0},limit:{type:'integer',minimum:1,maximum:65536}},true,async args=>{
      const actual=context();if(!initialized||!state)fail('source_unavailable','Wait for native model context.');exact(args.guard,Object.keys(actual.guard));if(Object.keys(actual.guard).some(key=>args.guard[key]!==actual.guard[key]))fail('stale_context','Read current model context before source inspection.');return{outcome:'observed',...await api('/api/source',{expected_revision:state.revision,expected_bundle_sha256:state.projection.bundle_sha256,request:args.request,file:args.file,offset:args.offset,limit:args.limit})};
    }],
    ['cse_read_ownership_context','Read a bounded native owner/file page and every affected physical view for a captured declaration. Namespace source locators are valid only for their returned bundle. Optionally inspect one affected view’s exact frame bindings and geometry. This does not select an owner, edit a draft, or change retained review scope.',{guard:guardSchema,element_id:text,offset:{type:'integer',minimum:0},limit:{type:'integer',minimum:1,maximum:100},affected_view:nullableText},true,async args=>{
      checkGuard(args.guard);return{outcome:'observed',...await api('/api/ownership-context',{element_id:args.element_id,expected_revision:state.revision,expected_bundle_sha256:state.projection.bundle_sha256,offset:args.offset,limit:args.limit,view_id:args.affected_view})};
    }],
    ['cse_preview_ownership','Preview a native owner change on the exact selected declaration and its subtree, preserving UUIDs. Use a bundle-bound destination and explicit consequences for every affected physical view. Preserve diagram boxes; supply the new owner frame/route or remove occurrences only. Scope remains unchanged and is checked again. Review the checked candidate before saving.',{guard:guardSchema,element_id:text,destination:ownerTarget,composition_transition:compositionTransition,view_effects:ownershipEffects},false,async args=>{
      checkGuard(args.guard);cleanTarget(args.element_id);exact(args.destination,['kind','identity','file','bundle_sha256']);
      if(args.destination.bundle_sha256!==state.projection.bundle_sha256)fail('stale_context','Inspect native destinations again for this source bundle.');
      if(!Array.isArray(args.view_effects)||args.view_effects.length>128)fail('input','Supply complete explicit affected-view consequences.');
      const views=args.view_effects.map(effect=>{if(effect.action==='reparent'){exact(effect,['view_id','action','parent_node','points']);if(!Array.isArray(effect.points)||effect.points.length<2||effect.points.length>128||effect.points.some(p=>!Array.isArray(p)||p.length!==2||!p.every(Number.isFinite)))fail('input','Ownership routes need 2 through 128 finite coordinate pairs.');}else{exact(effect,['view_id','action']);if(!['remove_occurrences','preserve_structure'].includes(effect.action))fail('input','Choose the documented explicit view consequence.');}return{view_id:effect.view_id,action:effect.action,parent_node:effect.parent_node||'',points_text:effect.points?.map(p=>p.join(',')).join('\n')||''}});
      if(args.composition_transition!==null){exact(args.composition_transition,['before','after']);if(Object.values(args.composition_transition).some(value=>typeof value!=='boolean'))fail('input','Composition transition needs exact native booleans.');}
      const row=state.projection.inspection.occurrences['decl:'+args.destination.identity];
      const draft={destination:args.destination,destination_name:row?.element||args.destination.kind+' '+args.destination.identity,transition_ack:args.composition_transition!==null,views};
      const actual=ownershipTransition(draft);if(JSON.stringify(actual)!==JSON.stringify(args.composition_transition))fail('composition_transition','Supplied composition transition differs from the captured declaration and owner kind.');
      retainOwnershipDraft(draft);ownershipOptions();return await previewOwnership();
    }],
    ['cse_acknowledge_ownership_candidate','Confirm review of the exact checked ownership candidate and all affected view consequences. Acknowledgement is bound to this pending request and bundle; it is separate from a durable save, successful retained review or engineering acceptance.',{guard:guardSchema,request_id:text,checked_bundle_sha256:text},false,args=>{
      checkGuard(args.guard);if(unknown||!pending||pending.stale||pending.request.operation!=='reparent'||pending.request.request_id!==args.request_id||pending.request.checked_bundle_sha256!==args.checked_bundle_sha256)fail('pending_request','Review the current exact ownership candidate before acknowledging it.');byId('ownership-candidate-ack').checked=true;byId('ownership-candidate-ack').dispatchEvent(new Event('change'));return{outcome:'reviewed',request_id:args.request_id,checked_bundle_sha256:args.checked_bundle_sha256};
    }],
    ['cse_read_removal_impact','Inspect affected source, declarations and views for the exact selected native part or framed occurrence. Reads the saved revision without changing its selection, draft or retained scope.',{guard:guardSchema,scope:{enum:['diagram','model']}},true,async args=>{
      checkGuard(args.guard);
      const selected=selectedNode()?.[1];
      if(!selected?.element_id||!['diagram','model'].includes(args.scope)||args.scope==='diagram'&&!selected.frame_id)fail('target','Choose the exact part or framed occurrence.');
      const target=args.scope==='diagram'?{view_id:state.projection.id,node_id:selected.frame_id}:{element_id:selected.element_id};
      return{outcome:'observed',...await api('/api/removal-context',{...target,expected_revision:state.revision,expected_bundle_sha256:state.projection.bundle_sha256})};
    }],
    ['cse_preview_diagram_removal','Preview the removal of an exact captured diagram occurrence. Supply every inspected node, route and view effect. The native model remains available.',{guard:guardSchema,element_id:text,node_id:text,view_effects:removalEffects},false,async args=>{
      checkGuard(args.guard);cleanTarget(args.element_id);
      if(editingNode()?.[1].frame_id!==args.node_id||typeof args.node_id!=='string')fail('target','Select the exact framed occurrence.');
      return await previewRemovalRequest('remove_occurrence',{view_id:state.projection.id,node_id:args.node_id},args.view_effects);
    }],
    ['cse_preview_native_deletion','Preview deletion of the selected native part. Supply exact inspected typing effects and all affected view consequences. The checked candidate exposes retained configuration findings before review and save.',{guard:guardSchema,element_id:text,reference_effects:referenceEffects,view_effects:removalEffects},false,async args=>{
      checkGuard(args.guard);cleanTarget(args.element_id);
      return await previewRemovalRequest('delete',{element_id:args.element_id,reference_effects:args.reference_effects},args.view_effects);
    }],
    ['cse_acknowledge_removal_candidate','Acknowledge review of the exact pending removal, view consequences and retained findings. Review leaves the checked request unsaved.',{guard:guardSchema,request_id:text,checked_bundle_sha256:text},false,args=>{
      checkGuard(args.guard);
      if(unknown||!pending||pending.stale||!removalOperation(pending.request.operation)||pending.request.request_id!==args.request_id||pending.request.checked_bundle_sha256!==args.checked_bundle_sha256)fail('pending_request','Review the current exact removal before acknowledging it.');
      byId('ownership-candidate-ack').checked=true;byId('ownership-candidate-ack').dispatchEvent(new Event('change'));
      return{outcome:'reviewed',request_id:args.request_id,checked_bundle_sha256:args.checked_bundle_sha256};
    }],
    ['cse_preview_types','Prepare the complete explicit typing list on the selected native part usage. Supply distinct existing part-definition UUIDs in order, or [] to remove explicit typing. Implied/inherited types and retained configuration scope remain separate; editing a shared declaration affects its consumers. Preview and save use the same native controller as the form.',{guard:guardSchema,element_id:text,type_ids:{type:'array',maxItems:128,uniqueItems:true,items:text}},false,async args=>{
      checkGuard(args.guard);cleanTarget(args.element_id);
      if(editingNode()?.[1].kind!=='PartUsage')fail('element_kind','Explicit feature typing belongs to a part usage.');
      if(!Array.isArray(args.type_ids)||args.type_ids.length>128||args.type_ids.some(id=>typeof id!=='string')||new Set(args.type_ids).size!==args.type_ids.length)fail('typing','Supply zero through 128 distinct part-definition UUIDs.');
      if(args.type_ids.some(id=>!typeDefinitions().some(row=>row.element_id===id)))fail('identity','Choose existing part-definition UUIDs; no form values were changed.');
      setTypingRows(args.type_ids.map(id=>({type_id:id,native_name:typeDefinitions().find(row=>row.element_id===id)?.element||null})));dirty=true;return await previewTyping();
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
      checkGuard(args.guard,true);if(unknown||pending||dirty)fail('retained_edit','Resolve the existing draft, checked change or unconfirmed save explicitly.');
      if(!Number.isInteger(args.target_revision)||!state.history.some(row=>row.revision===args.target_revision))fail('input','Select a saved revision of this project.');
      byId('restore-target').value=args.target_revision;return await previewRestore();
    }],
    ['cse_preview_current_edit','Check the existing visible form values on their retained editing target. Save separately after reviewing the candidate.',{guard:guardSchema,kind:{enum:['create_definition','create_usage','rename','multiplicity','typing','reparent','removal','layout','set_frame_master','set_connector_style','set_view_key','set_display_alias','restore']}},false,async args=>{
      checkGuard(args.guard,args.kind==='restore');
      if(unknown||pending||!editingNode()&&!['restore','set_connector_style','set_view_key'].includes(args.kind))fail('retained_edit','Resolve the pending change or unconfirmed save before another preview.');
      if(dirty&&draftKind&&draftKind!==args.kind)fail('retained_edit','Check the existing draft in its own form, or explicitly discard it first.');
      const previews={create_definition:previewCreateDefinition,create_usage:previewCreateUsage,rename:previewRename,multiplicity:previewMultiplicity,typing:previewTyping,reparent:previewOwnership,removal:previewRemoval,layout:previewLayout,set_frame_master:previewFrameMaster,set_connector_style:previewConnectorStyle,set_view_key:previewViewKey,set_display_alias:previewDisplayAlias,restore:previewRestore};
      if(typeof args.kind!=='string'||!Object.hasOwn(previews,args.kind))fail('input','Choose a supported form kind.');
      const preview=previews[args.kind];
      return await preview();
    }],
    ['cse_save_change','Durably save or retry the exact checked request ID already visible in this tab. Uses the same native Git transaction as the Save button. Returns a durable receipt, definite refusal, or unconfirmed outcome; never infer success from a preview.',{guard:guardSchema,request_id:text},false,async args=>{
      checkGuard(args.guard,true);
      if(!pending||pending.request.request_id!==args.request_id)fail('pending_request','The requested change is not the exact retained preview or retry.');
      return await saveChange();
    }],
    ['cse_discard_change','Explicitly discard the current unsaved form/checked change. Saved project is unchanged. Refuses to discard an unconfirmed save.',{guard:guardSchema},false,args=>{
      checkGuard(args.guard,true);if(unknown)fail('outcome_unknown','Resolve the exact unconfirmed save before discarding.');
      discard();return{outcome:'discarded'};
    }],
    ['cse_refresh_project','Refresh the saved view while retaining form values on their original target. A confirmed preview must be checked again; an unconfirmed save retains its exact retry request.',{guard:guardSchema},false,async args=>{
      checkGuard(args.guard,true);return await refreshSaved();
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
        const responseContext=['cse_read_retained_review','cse_search_component_catalog','cse_inspect_component_catalog',
          'cse_validate_component_selection','cse_get_component_selection','cse_set_component_selection'].includes(name)?()=>({guard:context().guard}):context;
        await document.modelContext.registerTool({name,description,inputSchema:object(properties),annotations:{readOnlyHint:readOnly},
          execute:async args=>{
            try{exact(args,Object.keys(properties));const result=await execute(args);return{action:name,...result,context:responseContext()};}
            catch(error){return{action:name,outcome:'refused',error:{code:error.code||'unavailable',detail:error.message},context:responseContext()};}
          }});
        registration.registered.push(name);
      }catch(error){registration.errors.push({name,detail:String(error)});}
    }
    registration.status=registration.errors.length?'partial':'registered';
  })();
})();
