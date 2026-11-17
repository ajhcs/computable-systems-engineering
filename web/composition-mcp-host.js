// Transport and context only. The supplied MCP client owns authentication;
// the server owns project authorization, native findings and durable receipts.
const toolNames=Object.freeze({state:'cse_read_composition_state',head:'cse_read_composition_head',
  inspection:'cse_read_composition_occurrences',preview:'cse_preview_composition_change',
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
      }else if(payload!==undefined)args.request=payload;
      const result=await app.callServerTool({name:toolNames[operation],arguments:args});
      const native=result._meta?.cse_native;
      if(!native)throw Error('A native composition response was not received.');
      return{status:native.http_status,body:native.body};
    },
  });
}

// This is selected UI context, not a substitute for complete retained reviews.
export function compositionModelContext(context){
  const {ready,host_transport,view_status,guard,editing_target,has_form_draft,draft_kind,unconfirmed_save,notice,last_acknowledged_receipt}=context;
  const request=context.pending_change?.request;
  return{ready,host_transport,view_status,guard,editing_target,has_form_draft,draft_kind,unconfirmed_save,notice,last_acknowledged_receipt,
    selected_occurrence:context.selection,typing_draft:context.typing_draft,creation_draft:context.creation_draft,usage_creation_draft:context.usage_creation_draft,restoration_target_revision:context.restoration_target_revision,
    pending_request:request?{request_id:request.request_id,operation:request.operation,expected_revision:request.expected_revision}:null,
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
