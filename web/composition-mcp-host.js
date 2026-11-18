// Transport and context only. The supplied MCP client owns authentication;
// the server owns project authorization, native findings and durable receipts.
const toolNames=Object.freeze({state:'cse_read_composition_state',head:'cse_read_composition_head',
  inspection:'cse_read_composition_occurrences',source:'cse_read_composition_source',ownership_context:'cse_read_composition_ownership_context',preview_view:'cse_read_composition_candidate_view',preview:'cse_preview_composition_change',
  apply:'cse_apply_composition_change',receipt:'cse_lookup_composition_receipt'});
export function createMcpCompositionHost(app,boot,storage){
  const uuid=value=>typeof value==='string'&&/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(value);
  if(typeof app?.callServerTool!=='function'||!uuid(boot?.project_id)||!uuid(boot?.app_instance_id)||typeof boot.view_id!=='string'||!boot.view_id||
      !storage||['getItem','setItem','removeItem'].some(name=>typeof storage[name]!=='function'))throw Error('Incomplete MCP composition host.');
  const project=boot.project_id,view=boot.view_id,prefix='cse-mcp:'+boot.app_instance_id+':';
  return Object.freeze({version:'cse-composition-host-1',kind:'mcp_apps',openArtifact:null,
    intentStorage:Object.freeze({getItem:key=>storage.getItem(prefix+key),setItem:(key,value)=>storage.setItem(prefix+key,value),removeItem:key=>storage.removeItem(prefix+key)}),
    async request({operation,payload}){
      if(!Object.hasOwn(toolNames,operation))throw Error('Unsupported MCP composition operation.');
      const args={project_id:project,view_id:view};
      if(operation==='inspection'){
        if(!payload||Object.hasOwn(payload,'project_id')||Object.hasOwn(payload,'view_id'))throw Error('Inspection cannot replace the granted project or view.');
        Object.assign(args,payload);
      }else if(operation==='source'){
        const keys=['expected_revision','expected_bundle_sha256','request','file','offset','limit'];
        if(!payload||Object.keys(payload).length!==keys.length||keys.some(key=>!Object.hasOwn(payload,key)))throw Error('Source read needs the exact snapshot, optional candidate request, file and bounded chunk.');
        Object.assign(args,payload);
      }else if(operation==='ownership_context'){
        const keys=['element_id','expected_revision','expected_bundle_sha256','offset','limit','view_id'];
        if(!payload||Object.keys(payload).length!==keys.length||keys.some(key=>!Object.hasOwn(payload,key))||
            payload.view_id!==null&&typeof payload.view_id!=='string')throw Error('Ownership inspection needs its captured target, bounded page and optional affected view.');
        const {view_id:affected_view_id,...fields}=payload;
        Object.assign(args,fields,{affected_view_id});
      }else if(operation==='preview_view'){
        if(!payload||Object.keys(payload).length!==2||!Object.hasOwn(payload,'request')||typeof payload.view_id!=='string')throw Error('Choose one affected candidate view and exact checked request.');
        args.request=payload.request;args.affected_view_id=payload.view_id;
      }else if(payload!==undefined)args.request=payload;
      const result=await app.callServerTool({name:toolNames[operation],arguments:args});
      const native=result._meta?.cse_native;
      if(!native)throw Error('A native composition response was not received.');
      return{status:native.http_status,body:native.body};
    },
  });
}

// The component shell performs the explicit handoff to the existing saved-model
// controller. It retains the same SDK client and grant; no fetch/storage global
// is replaced, and the initial session never masquerades as a saved revision.
export function createMcpInitialCompositionHost(app,boot,storage,openSaved){
  const uuid=value=>typeof value==='string'&&/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(value);
  if(typeof app?.callServerTool!=='function'||!uuid(boot?.project_id)||!uuid(boot?.root_element_id)||!uuid(boot?.app_instance_id)||
      typeof boot.view_id!=='string'||!/^[A-Za-z_][A-Za-z0-9_.-]{0,127}$/.test(boot.view_id)||
      !storage||['getItem','setItem','removeItem'].some(name=>typeof storage[name]!=='function')||typeof openSaved!=='function')throw Error('Incomplete MCP initial-project host.');
  const project=boot.project_id,root=boot.root_element_id,view=boot.view_id,prefix='cse-mcp:'+boot.app_instance_id+':initial:';
  const names=Object.freeze({initial_state:'cse_read_initial_composition_state',initial_preview:'cse_preview_initial_composition',
    initial_apply:'cse_initialize_composition_project',initial_receipt:'cse_lookup_initial_composition_receipt',initial_open:'cse_open_initialized_composition'});
  return Object.freeze({version:'cse-initial-host-1',kind:'mcp_apps',
    grant:Object.freeze({project_id:project,root_element_id:root,view_id:view}),
    intentStorage:Object.freeze({getItem:key=>storage.getItem(prefix+key),setItem:(key,value)=>storage.setItem(prefix+key,value),removeItem:key=>storage.removeItem(prefix+key)}),
    async request({operation,payload}){
      if(!Object.hasOwn(names,operation)||operation==='initial_state'&&payload!==undefined)throw Error('Unsupported MCP initial operation.');
      const args={project_id:project,root_element_id:root,view_id:view};
      if(operation!=='initial_state'){
        if(!payload||payload.project_id!==project||payload.root_element_id!==root||payload.view_id!==view)throw Error('Initial request cannot replace the granted project, root or view.');
        args.request=payload;
      }
      const result=await app.callServerTool({name:names[operation],arguments:args}),native=result._meta?.cse_native;
      if(!native||!Number.isInteger(native.http_status)||!native.body)throw Error('A native initial response was not received.');
      return{status:native.http_status,body:native.body};
    },
    openSaved:result=>openSaved(result),
  });
}

// This is selected UI context, not a substitute for complete retained reviews.
export function compositionModelContext(context){
  const {ready,host_transport,view_status,guard,editing_target,has_form_draft,draft_kind,unconfirmed_save,notice,last_acknowledged_receipt}=context;
  const request=context.pending_change?.request;
  return{ready,host_transport,view_status,guard,editing_target,has_form_draft,draft_kind,unconfirmed_save,notice,last_acknowledged_receipt,
    selected_occurrence:context.selection,source_inspection:context.source_inspection,model_sources:context.model_sources,typing_draft:context.typing_draft,ownership_draft:context.ownership_draft,creation_draft:context.creation_draft,usage_creation_draft:context.usage_creation_draft,restoration_target_revision:context.restoration_target_revision,
    phase:context.phase,initial_state:context.initial_state,raw_draft:context.raw_draft,candidate_ready:context.candidate_ready,
    pending_request:request?{request_id:request.request_id,operation:request.operation,expected_revision:request.expected_revision,
      ...(request.operation==='reparent'?{checked_bundle_sha256:request.checked_bundle_sha256}:{}),
      ...(request.operation==='initialize_physical_project'?{expected_bundle_sha256:request.expected_bundle_sha256}:{} )}:null,
    retained_review_identities:(context.configuration_reviews||[]).map(review=>({file:review.file,scope_sha256:review.scope_sha256,status:review.report.status})),
    scope:'selected_ui_context_never_replaces_complete_retained_review'};
}

export function publishMcpCompositionContext(app,workbench){
  if(typeof app?.updateModelContext!=='function'||typeof workbench?.context!=='function'||typeof workbench.subscribe!=='function')throw Error('Incomplete MCP context publisher.');
  let delivered='',publishing=false,retry=null,disposed=false;
  async function push(){
    if(disposed||publishing)return;
    publishing=true;
    try{
      while(!disposed){
        const encoded=JSON.stringify(compositionModelContext(workbench.context()));
        if(encoded===delivered)break;
        await app.updateModelContext({content:[{type:'text',text:'CSE selected UI context; native model and retained review scope remain authoritative. '+encoded}]});
        delivered=encoded;
      }
    }catch(error){if(!disposed&&!retry)retry=setTimeout(()=>{retry=null;push();},250);}
    finally{publishing=false;}
  }
  const unsubscribe=workbench.subscribe(()=>{push();});
  return()=>{disposed=true;clearTimeout(retry);unsubscribe();};
}
