#!/usr/bin/env python3
"""Regenerate four bounded teaching views; not a general SysML diagram exporter."""
from pathlib import Path
from hashlib import sha256
import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from html import escape

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verifier.sysml import check_sysml
BASE = ROOT / "examples/diagram-reference"
NAVY, TEAL, GRAY, AMBER = "#16324f", "#16766c", "#63758a", "#b56c10"

def digest(path):
    return sha256(path.read_bytes()).hexdigest()

def check_contract(name, source):
    """Explicit fixture contracts; reject semantic drift rather than guessing."""
    expected = {
        "context": [
            "out item request : Request;", "in item assignedTool : Allocation;",
            "in item request : Request;", "out item assignedTool : Allocation;",
            "flow requestFlow of Request from borrower.request to system.request;",
            "flow allocationFlow of Allocation from system.assignedTool to borrower.assignedTool;"
        ],
        "ordered-actions": ["first start;", "then action receiveRequest;",
                            "then action assessAvailability;", "then action recordAllocation;", "then done;"],
        "timed-obligation": ["period 1 second", "in attribute request : Boolean;",
                             "out attribute recorded : Boolean;", "subject unit = system;",
                             "Upon unit.request = true, unit shall within 2 seconds",
                             "satisfy unit.recorded = true."],
        "runtime": ["part launcher : SkillLauncher;", "part cli : CLI;", "part adapter : Adapter;",
                    "part pilot : PilotParser;", "part checker : BoundedChecker;"]
    }[name]
    for text in expected:
        if source.count(text) != 1:
            raise ValueError(f"{name}: missing/ambiguous fixture construct: {text}")
    if name == "context":
        for owner, body in (("Borrower", "out item request : Request;"), ("ToolLibrary", "in item request : Request;")):
            match = re.search(r"part def " + owner + r"\s*\{([^}]+)\}", source)
            if not match or body not in match.group(1):
                raise ValueError("context: item direction changed in " + owner)
        flows = re.findall(r"\bflow \w+ of \w+ from [\w.]+ to [\w.]+;", source)
        if len(flows) != 2:
            raise ValueError("context: exactly two item flows required")
    if name == "ordered-actions":
        order = re.findall(r"(?:first|then)\s+(?:action\s+)?(\w+)\s*;", source)
        if order != ["start", "receiveRequest", "assessAvailability", "recordAllocation", "done"]:
            raise ValueError("ordered-actions: succession order changed")
    if name == "timed-obligation" and source.count("require constraint") != 1:
        raise ValueError("timed-obligation: selected obligation changed")

class View:
    def __init__(self, key, title, subtitle, model, claim):
        self.key, self.title, self.subtitle = key, title, subtitle
        self.model, self.claim = model, claim
        self.nodes, self.edges = [], []
        self.width, self.height = 1280, 720

    def box(self, key, lines, x, y, w, h, fill="#eaf5f2", refs=(), size=22):
        self.nodes.append(dict(id=key, lines=lines, x=x, y=y, w=w, h=h,
                               fill=fill, refs=list(refs), size=size))

    def edge(self, key, source, target, y1, y2, lines=(), refs=(), label_y=None):
        a, b = [next(n for n in self.nodes if n["id"] == key) for key in (source,target)]
        right = a["x"] < b["x"]
        x1 = a["x"] + (a["w"] if right else 0)
        x2 = b["x"] + (0 if right else b["w"])
        self.edges.append(dict(id=key, source=source, target=target, x1=x1, y1=y1,
                               x2=x2, y2=y2, lines=list(lines), refs=list(refs),
                               label_y=label_y if label_y is not None else min(y1,y2)-24))

    def write(self, output):
        output.mkdir(parents=True, exist_ok=True)
        model_hash = digest(self.model)
        svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" height="{self.height}" viewBox="0 0 {self.width} {self.height}">',
               '<rect width="1280" height="720" fill="#fff"/>',
               '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 Z" fill="#16766c"/></marker></defs>']
        mx = ET.Element("mxfile", host="app.diagrams.net", version="reference-1")
        page = ET.SubElement(mx,"diagram",id=self.key,name=self.title)
        graph = ET.SubElement(page,"mxGraphModel",page="1",pageWidth="1280",pageHeight="720")
        cells = ET.SubElement(graph,"root")
        ET.SubElement(cells,"mxCell",id="0")
        ET.SubElement(cells,"mxCell",id="1",parent="0")

        def text(key, lines, x, y, width=1180, size=22, color=NAVY, align="left", refs=()):
            # y is the top of a text block; one geometry feeds SVG and draw.io.
            h = len(lines)*(size+8)+8
            cell=ET.SubElement(cells,"mxCell",id=key,value="\n".join(lines),vertex="1",parent="1",
                style=f"text;html=0;whiteSpace=wrap;align={align};verticalAlign=top;fontFamily=DejaVu Sans;fontSize={size};fontColor={color};spacing=0;",
                cseRefs="|".join(refs))
            ET.SubElement(cell,"mxGeometry",x=str(x),y=str(y),width=str(width),height=str(h),attrib={"as":"geometry"})
            anchor="middle" if align=="center" else "start"
            tx=x+width/2 if align=="center" else x
            for i,line in enumerate(lines):
                svg.append(f'<text data-cell="{key}" x="{tx}" y="{y+size+i*(size+8)}" text-anchor="{anchor}" font-family="DejaVu Sans,sans-serif" font-size="{size}" fill="{color}">{escape(line)}</text>')

        text("title",[self.title],50,30,size=32)
        text("subtitle",[self.subtitle],50,86,size=19,color=GRAY)
        # Draw edges before nodes. Text labels have their own editable cells.
        for e in self.edges:
            if e["y1"]==e["y2"]:
                path=f'M {e["x1"]} {e["y1"]} L {e["x2"]} {e["y2"]}'
                points=[]
            else:
                mid=(e["x1"]+e["x2"])/2
                path=f'M {e["x1"]} {e["y1"]} L {mid} {e["y1"]} L {mid} {e["y2"]} L {e["x2"]} {e["y2"]}'
                points=[(mid,e["y1"]),(mid,e["y2"])]
            svg.append(f'<path data-cell="{e["id"]}" d="{path}" fill="none" stroke="{TEAL}" stroke-width="2.5" marker-end="url(#arrow)"/>')
            cell=ET.SubElement(cells,"mxCell",id=e["id"],edge="1",parent="1",source=e["source"],target=e["target"],
                style=f"edgeStyle=none;endArrow=block;endFill=1;strokeColor={TEAL};strokeWidth=2.5;",
                cseRefs="|".join(e["refs"]))
            geo=ET.SubElement(cell,"mxGeometry",relative="1",attrib={"as":"geometry"})
            ET.SubElement(geo,"mxPoint",x=str(e["x1"]),y=str(e["y1"]),attrib={"as":"sourcePoint"})
            ET.SubElement(geo,"mxPoint",x=str(e["x2"]),y=str(e["y2"]),attrib={"as":"targetPoint"})
            # Fixed endpoint ports preserve separate directed items in the editor.
            a,b=[next(n for n in self.nodes if n["id"]==k) for k in (e["source"],e["target"])]
            style=cell.get("style")+f'exitX={(e["x1"]-a["x"])/a["w"]};exitY={(e["y1"]-a["y"])/a["h"]};entryX={(e["x2"]-b["x"])/b["w"]};entryY={(e["y2"]-b["y"])/b["h"]};exitPerimeter=0;entryPerimeter=0;'
            cell.set("style",style)
            if points:
                arr=ET.SubElement(geo,"Array",attrib={"as":"points"})
                for x,y in points: ET.SubElement(arr,"mxPoint",x=str(x),y=str(y))
            if e["lines"]:
                center=(e["x1"]+e["x2"])/2
                text(e["id"]+"-label",e["lines"],center-155,e["label_y"],310,17,align="center",refs=e["refs"])
        for n in self.nodes:
            svg.append(f'<rect data-cell="{n["id"]}" x="{n["x"]}" y="{n["y"]}" width="{n["w"]}" height="{n["h"]}" rx="8" fill="{n["fill"]}" stroke="{TEAL}" stroke-width="2"/>')
            cell=ET.SubElement(cells,"mxCell",id=n["id"],value="",vertex="1",parent="1",
                style=f"rounded=1;arcSize=8;fillColor={n['fill']};strokeColor={TEAL};strokeWidth=2;",
                cseRefs="|".join(n["refs"]))
            ET.SubElement(cell,"mxGeometry",x=str(n["x"]),y=str(n["y"]),width=str(n["w"]),height=str(n["h"]),attrib={"as":"geometry"})
            text(n["id"]+"-text",n["lines"],n["x"]+12,n["y"]+18,n["w"]-24,n["size"],align="center",refs=n["refs"])
        text("claim",self.claim,50,565,size=18,color=GRAY)
        text("source",[f"{self.model.name} | SHA-256 {model_hash[:20]} | generated reference view"],50,675,size=15,color=GRAY)
        svg.append("</svg>")
        (output/f"{self.key}.svg").write_text("\n".join(svg))
        ET.indent(mx)
        ET.ElementTree(mx).write(output/f"{self.key}.drawio",encoding="utf-8",xml_declaration=True)
        ids=[c.get("id") for c in cells]
        if len(ids)!=len(set(ids)): raise ValueError("duplicate diagram cell")
        for e in self.edges:
            if e["source"] not in ids or e["target"] not in ids: raise ValueError("broken diagram endpoint")
        # Teaching fixtures forbid node overlaps. Footer/title are separate text.
        for i,a in enumerate(self.nodes):
            for b in self.nodes[i+1:]:
                if a["x"]<b["x"]+b["w"] and b["x"]<a["x"]+a["w"] and a["y"]<b["y"]+b["h"] and b["y"]<a["y"]+a["h"]:
                    raise ValueError(f"node overlap {a['id']} {b['id']}")
        return dict(id=self.key,title=self.title,model=self.model.relative_to(ROOT).as_posix(),
                    model_sha256=model_hash,nodes=self.nodes,edges=self.edges,
                    svg=f"{self.key}.svg",drawio=f"{self.key}.drawio",claim=self.claim)

def views(reports):
    c=View("01-context","Context: two different items, two directions",
           "Synthetic black-box context | custom SysML v2 item-flow view",BASE/"context.sysml",
           ["Request flows borrower → system; Allocation flows system → borrower.",
            "No internal design, successful delivery, timing, or stakeholder acceptance is claimed."])
    c.box("borrower",["part borrower : Borrower","external participant"],70,220,330,250,fill="#f0f3f7",refs=["LibraryContext::borrower"])
    c.box("system",["part system : ToolLibrary","system of interest","internals intentionally omitted"],820,220,390,250,refs=["LibraryContext::system"])
    c.edge("requestFlow","borrower","system",310,310,["requestFlow : Request"],["LibraryContext::requestFlow"],270)
    c.edge("allocationFlow","system","borrower",410,410,["allocationFlow : Allocation"],["LibraryContext::allocationFlow"],365)
    a=View("02-actions","Behavior: order without invented decisions",
           "Synthetic available-tool path | custom SysML v2 action-succession view",BASE/"ordered-actions.sysml",
           ["receiveRequest → assessAvailability → recordAllocation; the selected path ends at done.",
            "Succession is control order. It does not establish item flow, duration, allocation, or reachability proof.",
            "The unavailable-tool outcome remains outside this selected view."])
    names=["start","receiveRequest","assessAvailability","recordAllocation","done"]
    coords=[(45,80),(180,240),(490,240),(800,240),(1100,130)]
    for name,(x,w) in zip(names,coords):
        a.box(name,["action" if name not in ("start","done") else "control",name],x,270,w,135,refs=["LibraryActions::BorrowAvailable::"+name],size=19)
    for i in range(4): a.edge("then-"+str(i),names[i],names[i+1],337,337,refs=["LibraryActions::BorrowAvailable succession "+str(i)])
    t=View("03-deadline","Obligation: the same deadline, two verdicts",
           "Synthetic 1-second samples | illustrative timing graph, not a formal SysML diagram",BASE/"timed-obligation.sysml",
           ["R_RECORD: Upon request = true, within 2 seconds satisfy recorded = true.",
            "Trigger at t=1; inclusive deadline t=3. Sustained true request is not a fresh rising edge.",
            "Results apply to these complete synthetic traces; no real behavior or acceptance is established."])
    t.box("binding",["R_RECORD / responseTime","subject unit = system : ToolLibrary"],50,155,1180,92,size=21,refs=["LibraryDeadline::TimelyRecord"])
    for i in range(4):
        x=290+i*245
        t.box("pass-"+str(i),[f"t={i} s",f"request: {str(i>0).lower()}",f"recorded: {str(i==3).lower()}"],x,280,210,115,size=18,refs=["R_RECORD"])
        t.box("fail-"+str(i),[f"t={i} s",f"request: {str(i>0).lower()}","recorded: false"],x,420,210,115,fill="#fff3df",size=18,refs=["R_RECORD"])
    t.box("pass-status",["PASS","complete trace"],50,280,195,115,size=21,refs=["synthetic-pass.json"])
    t.box("fail-status",["FAIL","deadline missed"],50,420,195,115,fill="#fff3df",size=21,refs=["synthetic-fail.json"])
    r=View("04-runtime","Real repository: parsing and computation diverge",
           "Code-grounded dependency view | illustrative architecture, not a formal SysML diagram",BASE/"runtime.sysml",
           ["launcher → CLI → adapter. Adapter invokes the Java pilot and, for supported clauses, the checker.",
            "Syntax-only ends with parser/shape findings; bounded review also needs manifest and evidence.",
            "Runtime grouping is abstract. This view does not model production services or engineer acceptance."])
    r.box("launcher",["Skill launcher","skills/develop-*/","scripts/cse.py"],50,270,210,125,refs=["skills/develop-system-concept/scripts/cse.py"])
    r.box("cli",["CLI","scripts/sysml.py"],340,270,210,125,refs=["scripts/sysml.py"])
    r.box("adapter",["Adapter","verifier/sysml.py"],630,270,235,125,refs=["verifier/sysml.py"])
    r.box("pilot",["Java pilot / bridge","syntax + references"],980,180,250,125,refs=["tools/sysml/SysmlBridge.java"])
    r.box("checker",["Bounded checker","verifier/language.py"],980,420,250,125,refs=["verifier/language.py"])
    r.edge("invoke","launcher","cli",332,332,refs=["cse.py subprocess.run"])
    r.edge("call","cli","adapter",332,332,refs=["sysml.py check_sysml"])
    r.edge("parse","adapter","pilot",300,245,refs=["sysml.py _parser_output"])
    r.edge("compute","adapter","checker",365,480,refs=["sysml.py check_document"])
    return [c,a,t,r]

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output",type=Path,default=BASE/"rendered")
    args=ap.parse_args()
    reports={}
    for name in ("context","ordered-actions","timed-obligation","runtime"):
        path=BASE/f"{name}.sysml"
        check_contract(name,path.read_text())
        report=check_sysml(path,syntax_only=True)
        if report["status"]!="pass": raise ValueError(json.dumps(report["parser_issues"]))
        reports[name]=report
    # Static code anchors validate the actual call paths instead of drawing imagined services.
    anchors={
      "skills/develop-system-concept/scripts/cse.py":["str(ROOT / \"scripts\" / COMMANDS[args.command])","subprocess.run"],
      "scripts/sysml.py":["from verifier.sysml import check_sysml","report = check_sysml"],
      "verifier/sysml.py":["def _parser_output","subprocess.run(command","SysmlBridge","check_document(candidate"],
      "tools/sysml/SysmlBridge.java":["class SysmlBridge"],
      "verifier/language.py":["def check_document"]
    }
    for relative,strings in anchors.items():
        content=(ROOT/relative).read_text()
        for text in strings:
            if text not in content: raise ValueError(f"missing code anchor {relative}: {text}")
    path=BASE/"timed-obligation.sysml"
    manifest={"version":1,"source_revision":"synthetic-diagram-1","expected":[{"id":"R_RECORD","constraint":"responseTime","source":"SYN-DIAGRAM-01"}]}
    (BASE/"synthetic-manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    results={}
    for name,last,expected in (("pass",True,"pass"),("fail",False,"fail")):
        obs=[{"LibraryDeadline::system::request":bool(i),"LibraryDeadline::system::recorded":last and i==3} for i in range(4)]
        evidence={"model_sha256":digest(path),"complete":True,"observations":obs}
        (BASE/f"synthetic-{name}.json").write_text(json.dumps(evidence,indent=2)+"\n")
        result=check_sysml(path,manifest=manifest,evidence=evidence,review=True)
        if result["status"]!=expected: raise ValueError(f"expected {expected}: {result}")
        results[name]=result
    media=[view.write(args.output) for view in views(reports)]
    facts={"version":1,"scope":"four fixed teaching fixtures; not general model equivalence",
           "syntax":{k:{"status":v["status"],"parser":v["parser"],"sha256":v["model_sha256"]} for k,v in reports.items()},
           "synthetic_review":{k:{"status":v["status"],"claim_scope":v["claim_scope"]} for k,v in results.items()},
           "code_anchors":{k:{"sha256":digest(ROOT/k),"anchors":v} for k,v in anchors.items()},
           "media":media}
    (args.output/"index.json").write_text(json.dumps(facts,indent=2)+"\n")
    print(json.dumps({"syntax":{k:v["status"] for k,v in reports.items()},
                      "synthetic_review":{k:v["status"] for k,v in results.items()}},indent=2))

if __name__=="__main__":
    main()
