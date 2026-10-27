#!/usr/bin/env python3
"""Bounded native-v2 composition correspondence; known presentation colors are the only exclusions."""
from pathlib import Path
import json, re, xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
COLOR_ATTRIBUTES={"fill","stroke"}
COLOR_STYLE={"fill","stroke","background","background-color"}
def invariant_svg(data):
    root=ET.fromstring(data)
    for element in root.iter():
        for key in COLOR_ATTRIBUTES:
            if key in element.attrib and re.fullmatch(r"#[0-9a-fA-F]{6}",element.get(key)):
                element.set(key,"COLOR")
        if "style" in element.attrib:
            fields=[]
            for field in element.get("style").split(";"):
                key,sep,value=field.partition(":")
                if sep and key.strip() in COLOR_STYLE and re.fullmatch(r"#[0-9a-fA-F]{6}",value.strip()):
                    value="COLOR"
                fields.append(key+sep+value)
            element.set("style",";".join(fields))
    def record(e): return (e.tag,tuple(sorted(e.attrib.items())),e.text,e.tail,tuple(record(c) for c in e))
    return record(root)
def validate_facts(facts,source,puml,svg):
    if facts["schema"]!="cse-native-composition-1" or facts["parse_has_errors"] or facts["parse_issues"]:
        raise ValueError("Invalid linked native parse receipt")
    selected=facts["selected"]
    if selected["kind"]!="PartDefinition" or selected["name"]!="ActiveSegmentedMirror": raise ValueError("Wrong selected definition")
    if len(facts["parts"])!=3: raise ValueError("Missing/extra owned part")
    graph={}
    for kind,label,alias,uid in re.findall(r'comp (def|usage) "([^"]+)" as (E\d+) .*?\[\[psysml:([^\]]+)\]\]',puml):
        if uid in graph: raise ValueError("Duplicate native identity")
        graph[uid.strip()]=(kind,label.strip(),alias)
    if len(graph)!=4 or graph.get(selected["id"],())[0:2]!=("def",selected["name"]): raise ValueError("Definition graph identity mismatch")
    links=[(a,b,uid.strip()) for a,b,uid in re.findall(r'(E\d+) \*-- (E\d+) \[\[psysml:([^\]]+)\]\]',puml)]
    decoded_puml=re.sub(r'<U\+([0-9A-Fa-f]+)>',lambda m:chr(int(m.group(1),16)),puml)
    if len(links)!=3: raise ValueError("Missing/extra composition edge")
    svgroot=ET.fromstring(svg)
    hrefs={value for e in svgroot.iter() for key,value in e.attrib.items() if key=="href" or key.endswith("}href")}
    svgids=[e.get("id") for e in svgroot.iter() if e.get("id")]
    if len(svgids)!=len(set(svgids)): raise ValueError("Duplicate SVG id")
    source_by_type={p["type_name"]:p for p in source["parts"]}
    names=set()
    for part in facts["parts"]:
        if part["kind"]!="PartUsage" or not part["composite"] or part["owner_id"]!=selected["id"] or part["owner"]!=selected["qualified"]:
            raise ValueError("Ownership/composition mismatch")
        if part["visibility"]!="private" or len(part["definitions"])!=1: raise ValueError("Visibility/type mismatch")
        if part["qualified"]!=selected["qualified"]+"::"+part["name"]: raise ValueError("Qualified role mismatch")
        definition=part["definitions"][0];original=source_by_type.get(definition["name"])
        if original is None or (part["lower"],part["upper"])!=(original["lower"],original["upper"]): raise ValueError("Multiplicity/type mismatch")
        if definition["qualified"]!="APECompositionDerived::"+definition["name"]: raise ValueError("Qualified type mismatch")
        derived_name=original["name"] or "mount"
        if part["name"]!=derived_name or derived_name in names: raise ValueError("Source role correspondence mismatch")
        names.add(derived_name)
        if original["aggregation"]!="composite": raise ValueError("Source composition mismatch")
        if original["implicit_multiplicity"]!=part["multiplicity_origin"].startswith("implicit"): raise ValueError("Implicit/explicit bounds mismatch")
        expected=derived_name+": "+definition["name"]+(f'[{part["upper"]}]' if not original["implicit_multiplicity"] else "")
        if part["id"] not in graph or graph[part["id"]][:2]!=("usage",expected): raise ValueError("Native usage label mismatch")
        alias=graph[part["id"]][2];parentalias=graph[selected["id"]][2]
        if (parentalias,alias,part["membership_id"]) not in links: raise ValueError("Native membership endpoint mismatch")
        if original["id"] not in decoded_puml or original["type_id"] not in (ROOT/"examples/engineering-reference/derived/ape-composition.sysml").read_text(): raise ValueError("Source ID trace missing")
        for uid in [part["id"]]:
            if "psysml:"+uid not in hrefs: raise ValueError("Native SVG identity missing")
        if f"elem_{alias}" not in svgids: raise ValueError("Native SVG graph element missing")
    paths=[e for e in svgroot.iter() if e.tag.endswith("}path")]
    diamonds=[e for e in svgroot.iter() if e.tag.endswith("}polygon")]
    if len(paths)!=3 or len(diamonds)!=3: raise ValueError("Missing/extra SVG composition glyph")
    rectangles={e.get("id"):e for e in svgroot.iter() if e.tag.endswith("}rect") and e.get("id")}
    def border(point,rect):
        x,y=point;left=float(rect.get("x"));top=float(rect.get("y"))
        right=left+float(rect.get("width"));bottom=top+float(rect.get("height"))
        return left-1<=x<=right+1 and top-1<=y<=bottom+1 and min(abs(x-left),abs(x-right),abs(y-top),abs(y-bottom))<=1
    for (parentalias,alias,_),path,diamond in zip(links,paths,diamonds):
        coords=[float(v) for v in re.findall(r"-?\d+(?:\.\d+)?",path.get("d"))]
        if len(coords)!=8:raise ValueError("Unsupported native edge path")
        if not border(coords[:2],rectangles[parentalias]) or not border(coords[-2:],rectangles[alias]):raise ValueError("SVG edge endpoint mismatch")
        points=[float(v) for v in re.findall(r"-?\d+(?:\.\d+)?",diamond.get("points"))]
        if diamond.get("fill") in (None,"none") or len(points)!=10 or points[:2]!=coords[:2] or points[-2:]!=coords[:2]:raise ValueError("Composition diamond is not on owner endpoint")
    if "psysml:"+selected["id"] not in hrefs: raise ValueError("Selected SVG identity missing")
    return {"claim_scope":"reviewed-derivative-correspondence","original_source_validation":"not_run; curated facts are a reviewed derivative","parts":3,"composition_edges":3,"native_puml_identities":7,"native_svg_identity_links":4,"source_role_correspondence":"pass",
            "visibility":"private facts retained; native TREE does not display visibility",
            "scope":"selected ownership/type/multiplicity graph and source IDs; no simulation or full graphical conformance"}
def main():
    base=ROOT/"examples/native-v2-composition"
    facts=json.loads((base/"native.facts.json").read_text())
    source=json.loads((ROOT/"examples/engineering-reference/source/view-facts.json").read_text())["slices"]["ape-composition"]
    result=validate_facts(facts,source,(base/"native.puml").read_text(),(base/"native.svg").read_text())
    signature=invariant_svg((base/"native.svg").read_text())
    styled=list((base/"styled").glob("*.svg"))
    if len(styled)!=5: raise ValueError("Expected five treatments")
    for path in styled:
        if invariant_svg(path.read_text())!=signature: raise ValueError("Non-color change in "+path.name)
    result["styled_semantic_primitive_equality"]=len(styled)
    print(json.dumps(result,indent=2))
    return result
if __name__=="__main__":main()
