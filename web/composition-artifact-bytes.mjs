const artifactTypes = Object.freeze({'view.svg':'image/svg+xml','view.json':'application/json'});
const sha = /^[a-f0-9]{64}$/;
const oid = /^[a-f0-9]{40}$/;
const viewName = /^[A-Za-z_][A-Za-z0-9_.-]{0,127}$/;

export function capturedArtifact(initialView, allowViews, artifact) {
  const {kind,commit,revision,view_id,bundle_sha256,expected_sha256} = artifact || {};
  if (!Object.hasOwn(artifactTypes,kind) || !oid.test(commit) || !Number.isSafeInteger(revision) ||
      revision<1 || typeof view_id !== 'string' || !viewName.test(view_id) || !allowViews && view_id!==initialView ||
      !sha.test(bundle_sha256) || !sha.test(expected_sha256))
    throw Error('Choose an artifact from the exact saved physical view.');
  return {view_id,payload:{kind,commit,revision,bundle_sha256,expected_sha256}};
}

export async function checkedArtifactFile(response, project, capture) {
  const file = response?.body;
  const {view_id,payload:{kind,commit,revision,bundle_sha256,expected_sha256}} = capture;
  const mediaType = artifactTypes[kind];
  if ((response?.status??response?.http_status)!==200 || file?.project_id!==project ||
      file?.view_id!==view_id || file.kind!==kind || file.commit!==commit ||
      file.revision!==revision || file.bundle_sha256!==bundle_sha256 ||
      file.media_type!==mediaType || typeof file.text!=='string' || file.sha256!==expected_sha256)
    throw Error('The artifact response does not match the selected saved revision.');
  const bytes = new TextEncoder().encode(file.text);
  const digest = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)))
    .map(value=>value.toString(16).padStart(2,'0')).join('');
  if (file.bytes!==bytes.length || file.sha256!==digest)
    throw Error('The returned artifact bytes failed verification.');
  return {name:'CSE-'+view_id+'-r'+revision+'.'+(kind==='view.svg'?'svg':'json'),
    mediaType, text:file.text};
}
