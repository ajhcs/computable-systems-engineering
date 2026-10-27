#!/usr/bin/env python3
"""Style the actual native SVG using parsed XML color fields; preserve every other primitive."""
from pathlib import Path
import json,xml.etree.ElementTree as ET
from check_native_composition import invariant_svg
ROOT=Path(__file__).resolve().parents[1]
SVG="{http://www.w3.org/2000/svg}"
ET.register_namespace("",SVG[1:-1]);ET.register_namespace("xlink","http://www.w3.org/1999/xlink")
def recolor_style(style,palette):
    mapping={"#FFFFFF":palette["canvas"],"#181818":palette["line"],"#000000":palette["ink"]}
    fields=[]
    for field in style.split(";"):
        key,sep,value=field.partition(":")
        if sep and key.strip() in {"fill","stroke","background","background-color"}:
            value=mapping.get(value.strip(),value)
        fields.append(key+sep+value)
    return ";".join(fields)
def styled_svg(data,palette):
    root=ET.fromstring(data)
    for e in root.iter():
        if "style" in e.attrib:e.set("style",recolor_style(e.get("style"),palette))
        if e.get("stroke")=="#181818":e.set("stroke",palette["line"])
        if e.get("fill")=="#181818":e.set("fill",palette["line"])
        if e.get("fill")=="#FFFFFF":
            e.set("fill",palette["surface"] if e.tag==SVG+"rect" and e.get("id")=="E1" else palette["nested"])
        if e.get("fill")=="#000000":
            e.set("fill",palette["secondary"] if e.get("font-style")=="italic" else palette["ink"])
    result=ET.tostring(root,encoding="unicode")
    if invariant_svg(result)!=invariant_svg(data):raise ValueError("Non-presentation primitive changed")
    return '<?xml version="1.0" encoding="UTF-8"?>'+result
def main():
    base=ROOT/"examples/native-v2-composition";target=base/"styled";target.mkdir(exist_ok=True)
    data=(base/"native.svg").read_text()
    for name,palette in json.loads((ROOT/"examples/diagram-style-prototypes/tokens.json").read_text()).items():
        (target/(name+".svg")).write_text(styled_svg(data,palette))
if __name__=="__main__":main()
