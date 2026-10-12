"""Semantic drift and stale editable-view checks for the matched references."""
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.diagram_references import check_contract
from verifier.sysml import JAR,CLASSES

class ContractTests(unittest.TestCase):
    def test_reverse_item_direction_is_rejected(self):
        source=(ROOT/"examples/diagram-reference/context.sysml").read_text()
        bad=source.replace("from borrower.request to system.request","from system.request to borrower.request")
        with self.assertRaises(ValueError): check_contract("context",bad)

    def test_changed_order_is_rejected(self):
        source=(ROOT/"examples/diagram-reference/ordered-actions.sysml").read_text()
        bad=source.replace("then action receiveRequest;","then action TEMP;").replace(
            "then action assessAvailability;","then action receiveRequest;").replace(
            "then action TEMP;","then action assessAvailability;")
        with self.assertRaises(ValueError): check_contract("ordered-actions",bad)

    def test_changed_deadline_is_rejected(self):
        source=(ROOT/"examples/diagram-reference/timed-obligation.sysml").read_text()
        with self.assertRaises(ValueError):
            check_contract("timed-obligation",source.replace("within 2 seconds","within 3 seconds"))

    def test_owner_direction_is_rejected(self):
        source=(ROOT/"examples/diagram-reference/context.sysml").read_text()
        bad=source.replace("part def Borrower {\n        out item request","part def Borrower {\n        in item request").replace(
            "part def ToolLibrary {\n        in item request","part def ToolLibrary {\n        out item request")
        with self.assertRaises(ValueError): check_contract("context",bad)

@unittest.skipUnless(JAR.is_file() and (CLASSES/"SysmlBridge.class").is_file(),
                    "Run scripts/install_sysml_parser.py for reference integration")
class ArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        (ROOT/".tmp").mkdir(exist_ok=True)
        cls.tmp=tempfile.TemporaryDirectory(dir=ROOT/".tmp")
        cls.output=Path(cls.tmp.name)
        subprocess.run([sys.executable,str(ROOT/"scripts/diagram_references.py"),
                        "--output",str(cls.output)],cwd=ROOT,check=True,stdout=subprocess.PIPE)
        cls.index=json.loads((cls.output/"index.json").read_text())
    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_checked_in_views_are_current(self):
        saved=ROOT/"examples/diagram-reference/rendered"
        for name in ("01-context","02-actions","03-deadline","04-runtime"):
            for ext in ("svg","drawio"):
                self.assertEqual((self.output/f"{name}.{ext}").read_bytes(),
                                 (saved/f"{name}.{ext}").read_bytes(),f"stale {name}.{ext}")

    def test_saved_png_and_svg_match_render_receipt(self):
        saved=ROOT/"examples/diagram-reference/rendered"
        for record in json.loads((saved/"visual-checks.json").read_text()):
            svg=saved/record["file"]
            png=svg.with_suffix(".png")
            self.assertEqual(sha256(svg.read_bytes()).hexdigest(),record["svg_sha256"])
            self.assertEqual(sha256(png.read_bytes()).hexdigest(),record["png_sha256"])

    def test_editable_items_match_native_flow_endpoints(self):
        source=(ROOT/"examples/diagram-reference/context.sysml").read_text()
        native={name:(item,a,b) for name,item,a,b in re.findall(
            r"flow (\w+) of (\w+) from (\w+)\.\w+ to (\w+)\.\w+;",source)}
        cells={c.get("id"):c for c in ET.parse(self.output/"01-context.drawio").findall(".//mxCell")}
        for name,(item,a,b) in native.items():
            edge=cells[name]
            self.assertEqual((edge.get("source"),edge.get("target")),(a,b))
            self.assertIn(item,cells[name+"-label"].get("value"))
            self.assertIn("LibraryContext::"+name,edge.get("cseRefs"))
        self.assertEqual({c.get("id") for c in cells.values() if c.get("edge")=="1"},set(native))

    def test_all_editable_labels_match_rendered_text(self):
        for view in self.index["media"]:
            cells=ET.parse(self.output/view["drawio"]).findall(".//mxCell")
            texts={}
            for element in ET.parse(self.output/view["svg"]).getroot().iter():
                if element.tag.endswith("}text"):
                    texts.setdefault(element.get("data-cell"),[]).append(element.text or "")
            for cell in cells:
                if cell.get("value"):
                    self.assertEqual(cell.get("value").splitlines(),texts[cell.get("id")])
            ids={cell.get("id") for cell in cells}
            self.assertEqual(len(cells),len(ids))
            for cell in cells:
                if cell.get("edge")=="1":
                    self.assertIn(cell.get("source"),ids)
                    self.assertIn(cell.get("target"),ids)

    def test_timing_labels_match_supplied_synthetic_evidence(self):
        media=next(m for m in self.index["media"] if m["id"]=="03-deadline")
        nodes={n["id"]:n for n in media["nodes"]}
        for status in ("pass","fail"):
            observations=json.loads((ROOT/f"examples/diagram-reference/synthetic-{status}.json").read_text())["observations"]
            for i,sample in enumerate(observations):
                lines=nodes[f"{status}-{i}"]["lines"]
                self.assertIn("request: "+str(sample["LibraryDeadline::system::request"]).lower(),lines)
                self.assertIn("recorded: "+str(sample["LibraryDeadline::system::recorded"]).lower(),lines)
        self.assertEqual(self.index["synthetic_review"]["pass"]["status"],"pass")
        self.assertEqual(self.index["synthetic_review"]["fail"]["status"],"fail")

if __name__=="__main__":
    unittest.main()
