"""Portable shortlist renderer; controls change presentation selection only."""
import base64
from html import escape
import json
from pathlib import Path
from component_agent import destination, resolve, revision, RequestError
from verifier import components as library

STYLE='''
:root{color-scheme:light dark;font-family:system-ui,sans-serif;background:Canvas;color:CanvasText}
*{box-sizing:border-box}body{margin:0;padding:1rem;line-height:1.5}main{max-width:62rem;margin:auto}
h1{font-size:1.25rem;margin:0 0 .5rem}p{margin:.5rem 0}fieldset{border:0;padding:0;margin:1rem 0}
legend{font-weight:600}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,14rem),1fr));gap:1rem}
article{border:1px solid GrayText;border-radius:.4rem;padding:1rem;min-width:0}
img{display:block;width:100%;height:8rem;object-fit:contain;background:white}
h2{font-size:1rem;margin:.5rem 0;overflow-wrap:anywhere}code{font-size:.85rem;overflow-wrap:anywhere}
label{display:flex;align-items:center;gap:.5rem;padding:.5rem 0;cursor:pointer}
input{width:1.2rem;height:1.2rem;flex-shrink:0}button{font:inherit;padding:.5rem .9rem;min-height:2.75rem;cursor:pointer}
:focus-visible{outline:3px solid Highlight;outline-offset:3px}.actions{display:flex;flex-wrap:wrap;gap:.75rem}
textarea{width:100%;min-height:5rem;font:inherit;resize:vertical}output{display:block;margin:.75rem 0}
'''

SCRIPT='''
"use strict";
const state=JSON.parse(document.getElementById("cse-component-data").textContent);
const boxes=[...document.querySelectorAll('input[name="componentIds"]')];
const status=document.getElementById("cse-selection-status");
const copy=document.getElementById("cse-copy-ids"),save=document.getElementById("cse-save-selection");
function ids(){return boxes.filter(b=>b.checked).map(b=>b.value)}
function update(persist=true){const selected=ids();status.textContent=selected.length+" selected";
 status.dataset.selectedIds=JSON.stringify(selected);copy.disabled=save.disabled=selected.length===0;
 if(!document.getElementById("cse-copy-fallback").hidden)document.getElementById("cse-selected-ids").value=selected.join("\\n");
 if(persist)history.replaceState(null,"","#"+encodeURIComponent(JSON.stringify({revision:state.catalog_sha256,ids:selected})));}
boxes.forEach(b=>b.addEventListener("change",update));
copy.addEventListener("click",async()=>{
 const text=ids().join("\\n");
 try{if(!navigator.clipboard)throw Error("clipboard unavailable");
 await navigator.clipboard.writeText(text);status.textContent="Component IDs copied";}
 catch(_){document.getElementById("cse-copy-fallback").hidden=false;
 const field=document.getElementById("cse-selected-ids");field.value=text;field.focus();field.select();
 status.textContent="Clipboard unavailable. Copy the selected IDs from the text field.";}
});
save.addEventListener("click",()=>{
 const record={schema:"cse.component-selection/1",catalog_sha256:state.catalog_sha256,component_ids:ids()};
 const url=URL.createObjectURL(new Blob([JSON.stringify(record,null,2)+"\\n"],{type:"application/json"}));
 const link=document.createElement("a");link.href=url;link.download="cse-component-selection.json";
 document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
 status.textContent="Selection record downloaded";
});
let restoreError="";
boxes.forEach(b=>b.checked=false);
if(location.hash){try{
 if(location.hash.length>65536)throw Error("invalid selection");
 const saved=JSON.parse(decodeURIComponent(location.hash.slice(1)));
 if(saved.revision!==state.catalog_sha256)throw Error("stale selection");
 if(!Array.isArray(saved.ids)||saved.ids.some(id=>!boxes.some(b=>b.value===id)))throw Error("unknown component");
 boxes.forEach(b=>b.checked=saved.ids.includes(b.value));
}catch(_){restoreError="Saved selection is unavailable for this shortlist. Select components again.";}}
update(false);if(restoreError)status.textContent=restoreError;
'''

def render(ids,out,root=library.LIBRARY):
    if len(ids)>8:raise RequestError('inline_limit','An inline shortlist supports at most eight components; refine the search or create another shortlist.')
    rows=resolve(ids,root,maximum=8);path=destination(out,root)
    if path.suffix.casefold()!='.html':raise RequestError('invalid_destination','A shortlist output must use the .html extension.')
    library.validate(root);cards=[]
    for row in rows:
        id=row['id'];label='Select '+row['name']+' ['+id+']'
        image=base64.b64encode((Path(root)/row['file']).read_bytes()).decode()
        cards.append(f'''<article id="cse-component-{escape(id)}" data-component-id="{escape(id)}" aria-labelledby="cse-name-{escape(id)}">
<img src="data:image/svg+xml;base64,{image}" alt="{escape(row['name'],quote=True)}" width="132" height="132">
<h2 id="cse-name-{escape(id)}">{escape(row['name'])}</h2><code>{escape(id)}</code>
<label for="cse-select-{escape(id)}"><input id="cse-select-{escape(id)}" name="componentIds" type="checkbox" value="{escape(id)}" data-action="select-component" aria-label="{escape(label,quote=True)}">Select component</label></article>''')
    data=json.dumps({'catalog_sha256':revision(root)}).replace('<','\\u003c')
    html=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src data:; style-src 'unsafe-inline'; script-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>Engineering component selection</title><style>{STYLE}</style></head><body>
<main id="cse-component-picker" data-catalog-sha256="{revision(root)}"><h1>Choose engineering components</h1>
<p>Select artwork to use in your diagram. Model bindings are specified separately.</p>
<fieldset><legend>Component shortlist</legend><div class="cards">{''.join(cards)}</div></fieldset>
<output id="cse-selection-status" role="status" aria-live="polite" data-selected-ids="[]">0 selected</output>
<div class="actions"><button id="cse-copy-ids" data-action="copy-component-ids" type="button" disabled>Copy IDs</button>
<button id="cse-save-selection" data-action="download-component-selection" type="button" disabled>Download selection</button></div>
<div id="cse-copy-fallback" hidden><label for="cse-selected-ids">Selected component IDs</label><textarea id="cse-selected-ids" readonly></textarea></div>
<noscript>Use the visible component IDs with the icons.py selection command when JavaScript is unavailable.</noscript></main>
<script id="cse-component-data" type="application/json">{data}</script><script>{SCRIPT}</script></body></html>'''
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8') as stream:stream.write(html)
    return {'schema':'cse.component-agent/1','status':'pass','file':str(path),'catalog_sha256':revision(root),
            'component_ids':ids,'model_changes':False,'transport':'standalone_html'}
