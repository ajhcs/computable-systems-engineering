#!/usr/bin/env python3
"""Optional generation pilot; reuses existing ChatGPT auth, no API fallback. Run on BuilderBob."""
from pathlib import Path
import json
import subprocess
import os
import time
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'.tmp/diagram-evaluation'
OUT.mkdir(parents=True,exist_ok=True)
auth=subprocess.run(["/home/builderbob/.local/bin/codex","login","status"],text=True,capture_output=True)
if "ChatGPT" not in auth.stdout+auth.stderr:
    raise SystemExit("Evaluation requires existing ChatGPT login; no paid API fallback is authorized.")
base="\n\n".join(subprocess.check_output(["git","show","HEAD:"+p],cwd=ROOT,text=True) for p in (
    "skills/develop-operational-scenarios/SKILL.md","skills/develop-operational-scenarios/references/sysml.md"))
concise=(ROOT/'docs/concise-guidance-candidate.md').read_text().partition('\n\n')[2]
task="""Produce a matched formal SysML v2 model and readable graph for this original synthetic case.
A client is external to a BookingDesk system. BookRequest travels client to desk, and ReservationReceipt travels desk to client. Draw separate typed directed flows. Internals are not selected.
The selected available-slot action path is receiveRequest, checkAvailability, recordReservation, then done; do not invent an unavailable branch or allocate the actions to a physical component.
One proposed teaching obligation R_RECEIPT binds to desk with input request : Boolean and output recorded : Boolean. Use one-second CSE clock and CSE-REQ/2.0: Upon unit.request = true, unit shall within 2 seconds satisfy unit.recorded = true. Source SYN-EVAL-01. Include a concern and a use case. No supplied implementation evidence or engineer acceptance exists.
Return a JSON object with model (complete SysML text), nodes (array of {id,label}), flows (array of {id,source,target,item}), order (array of action names), explanation (string), and validation (string). Do not use tools, inspect files, make calls, or claim to have run checks. The supplied guidance and examples are all the materials for this bounded generation trial."""
schema={"type":"object","additionalProperties":False,"properties":{
 "model":{"type":"string"},"nodes":{"type":"array","items":{"type":"object","additionalProperties":False,"properties":{"id":{"type":"string"},"label":{"type":"string"}},"required":["id","label"]}},
 "flows":{"type":"array","items":{"type":"object","additionalProperties":False,"properties":{"id":{"type":"string"},"source":{"type":"string"},"target":{"type":"string"},"item":{"type":"string"}},"required":["id","source","target","item"]}},
 "order":{"type":"array","items":{"type":"string"}},"explanation":{"type":"string"},"validation":{"type":"string"}
},"required":["model","nodes","flows","order","explanation","validation"]}
(OUT/'schema.json').write_text(json.dumps(schema))
examples="\n\n".join((ROOT/'examples/diagram-reference'/name).read_text() for name in ("context.sysml","ordered-actions.sysml","timed-obligation.sysml"))
common="This is an authorized comparative evaluation using existing ChatGPT authentication. Produce only the requested output; tool execution is unnecessary.\n"
env=dict(os.environ,PATH="/workspace/cache/builderbob/global-tools/releases/jdk/26.0.2.1+1/bin:/workspace/build/builderbob/runtimes/node-v22.23.2-linux-x64/bin:/home/builderbob/.local/bin:/usr/bin:/bin",TMPDIR="/workspace/tmp/builderbob/cse-ref")
for condition,guidance in (("current",base),("concise-examples",concise+"\nMatched original references:\n"+examples)):
 prompt=common+guidance+"\nTASK:\n"+task
 (OUT/f"{condition}-prompt.txt").write_text(prompt)
 cmd=["/home/builderbob/.local/bin/codex","exec","--ignore-user-config","--ephemeral","--sandbox","read-only","--json","--color","never","--output-schema",str(OUT/'schema.json'),"-o",str(OUT/f"{condition}-response.json")]
 if condition=="concise-examples":
  cmd+=["--image",str(ROOT/'examples/diagram-reference/rendered/01-context.png')]
 cmd+=["-"]
 start=time.monotonic()
 with (OUT/f"{condition}-events.jsonl").open("w") as stdout,(OUT/f"{condition}-stderr.txt").open("w") as stderr:
  result=subprocess.run(cmd,input=prompt,text=True,cwd=ROOT,env=env,stdout=stdout,stderr=stderr,timeout=240)
 (OUT/f"{condition}-run.json").write_text(json.dumps({"exit_code":result.returncode,"seconds":round(time.monotonic()-start,2),"prompt_bytes":len(prompt.encode()),"prompt_words":len(prompt.split()),"image_inputs":1 if condition=="concise-examples" else 0},indent=2))
 print(condition,"exit",result.returncode,flush=True)
