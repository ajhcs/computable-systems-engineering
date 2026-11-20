import {capturedArtifact,checkedArtifactFile} from './composition-artifact-bytes.mjs';

const UUID = /^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/;
const VIEW = /^[A-Za-z_][A-Za-z0-9_.-]{0,127}$/;
const PROJECT_READS = new Set(['head','receipt','model_review','catalog_search','catalog_inspect','catalog_selection']);
const SAVED_OPERATIONS = new Set(['state','head','receipt','inspection','source','preview','apply',
  'preview_view','ownership_context','removal_context','model_review','catalog_search','catalog_inspect','catalog_selection']);
const INITIAL_OPERATIONS = new Set(['initial_state','initial_preview','initial_apply','initial_receipt','initial_open']);

function nativeTransport(boot, getAccessToken) {
  if (typeof boot?.project_id!=='string'||!UUID.test(boot.project_id) ||
      typeof boot.view_id!=='string'||!VIEW.test(boot.view_id) || typeof getAccessToken!=='function')
    throw Error('Incomplete authenticated physical workbench.');
  const endpoint = '/api/composition/'+boot.project_id;
  return async command => {
    const token = await getAccessToken();
    if (typeof token!=='string' || !/^[A-Za-z0-9._-]+$/.test(token))
      throw Error('Sign in to the private workbench.');
    const response = await fetch(endpoint,{
      method:'POST',cache:'no-store',credentials:'same-origin',
      headers:{Authorization:'Bearer '+token,'Content-Type':'application/json'},
      body:JSON.stringify(command),
    });
    return {status:response.status,body:await response.json()};
  };
}

function intentStore(storage) {
  if (!storage || ['getItem','setItem','removeItem'].some(name=>typeof storage[name]!=='function'))
    throw Error('Draft storage is unavailable.');
  return Object.freeze({getItem:key=>storage.getItem(key),setItem:(key,value)=>storage.setItem(key,value),
    removeItem:key=>storage.removeItem(key)});
}

export function createWebArtifactTransfer(boot, getAccessToken, saveFile) {
  const native = nativeTransport(boot,getAccessToken);
  if (typeof saveFile !== 'function') throw Error('Missing browser artifact handler.');
  return async artifact => {
    const capture = capturedArtifact(boot.view_id,boot.allow_project_views===true,artifact);
    const response = await native({operation:'artifact',...capture});
    const file = await checkedArtifactFile(response,boot.project_id,capture);
    await saveFile(file);
    return {isError:false};
  };
}

export function createWebCompositionHost(boot, getAccessToken, storage, openArtifact=null, rememberView=null) {
  const native = nativeTransport(boot,getAccessToken);
  const capturedView = boot.view_id;
  const allowViews = boot.allow_project_views===true;
  if (openArtifact!==null && typeof openArtifact!=='function') throw Error('Invalid artifact transfer.');
  if (rememberView!==null && typeof rememberView!=='function') throw Error('Invalid saved-view address handler.');
  return Object.freeze({version:'cse-composition-host-1',kind:'private_web',
    viewSelection:allowViews,intentStorage:intentStore(storage),openArtifact,
    rememberView:allowViews ? rememberView : null,
    refreshIntervalMs:15_000,
    request({operation,payload,viewId}) {
      if (!SAVED_OPERATIONS.has(operation)) throw Error('Unsupported physical workbench operation.');
      if (viewId!==undefined && (typeof viewId!=='string' || !VIEW.test(viewId)
          || !allowViews && viewId!==capturedView))
        throw Error('The selected view is outside the project view grant.');
      return native({operation,view_id:PROJECT_READS.has(operation)?null:(viewId??capturedView),payload:payload??{}});
    },
  });
}

export function createWebInitialCompositionHost(boot, getAccessToken, storage, openSaved) {
  const native = nativeTransport(boot,getAccessToken);
  if (!UUID.test(boot.root_element_id) || typeof openSaved!=='function')
    throw Error('Incomplete initial physical workbench grant.');
  const grant = Object.freeze({project_id:boot.project_id,root_element_id:boot.root_element_id,view_id:boot.view_id});
  return Object.freeze({version:'cse-initial-host-1',kind:'private_web',grant,intentStorage:intentStore(storage),openSaved,
    request({operation,payload}) {
      if (!INITIAL_OPERATIONS.has(operation) || (operation==='initial_state' && payload!==undefined))
        throw Error('Unsupported initial workbench operation.');
      if (operation!=='initial_state' && (!payload || Object.entries(grant).some(([key,value])=>payload[key]!==value)))
        throw Error('Initial intent is outside the project, root and view grant.');
      return native({operation,view_id:null,payload:payload??{}});
    },
  });
}
