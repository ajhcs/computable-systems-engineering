#!/usr/bin/env python3
"""Prepare synthetic skill trials and check their observable artifacts and commands.

This program never invokes a model. A recorded trace is evidence of the commands
it contains, not proof that a session was fresh or that a user accepted its work.
"""
from collections import Counter
from hashlib import sha256
from html.parser import HTMLParser
import argparse
import json
from pathlib import Path
import struct
import subprocess
import sys
import xml.etree.ElementTree as ET
import zlib

RUNTIME = Path(__file__).resolve().parents[1]
INVENTORY = RUNTIME / "examples/visual-guidance-evaluation/cases.json"
VERSION = "cse.visual-guidance-evaluation/1"


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def cases():
    data = json.loads(INVENTORY.read_text(encoding="utf-8"))
    if data.get("version") != "cse.visual-guidance-cases/1":
        raise ValueError("Unsupported case inventory")
    return {item["id"]: item for item in data["cases"]}


def selected_case(case_id):
    try:
        return cases()[case_id]
    except KeyError as error:
        raise ValueError("Unknown case: " + case_id) from error


def safe_path(root, value):
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("Expected a project-relative path: " + str(value))
    result = (root / path).resolve()
    if not result.is_relative_to(root.resolve()):
        raise ValueError("Path escapes project: " + str(value))
    return result


def write_png(path):
    """A small original procedural fixture; this is not production artwork."""
    width, height = 96, 24
    rows = b"".join(b"\x00" + bytes(channel for x in range(width)
                  for channel in (20 + x, 50 + y * 3, 120 + (x // 12 % 2) * 60))
                  for y in range(height))
    def chunk(kind, payload):
        return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload))
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
                     + chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b""))


def profile(mono=False, missing=False):
    fonts = [{"id": "body", "family": "IBM Plex Sans", "weight": 400,
              "path": "runtime:examples/ecosystem-diagram-reference/fonts/IBMPlexSans-Regular.woff2",
              "postscript_name": "IBMPlexSans"},
             {"id": "heading", "family": "IBM Plex Sans", "weight": 600,
              "path": "runtime:examples/ecosystem-diagram-reference/fonts/IBMPlexSans-SemiBold.woff2",
              "postscript_name": "IBMPlexSans-SmBld"}]
    if mono:
        fonts = [{"id": "body", "family": "IBM Plex Mono", "weight": 400,
                  "path": "runtime:examples/ecosystem-diagram-reference/fonts/IBMPlexMono-Regular.woff2",
                  "postscript_name": "IBMPlexMono"}]
    if missing:
        fonts[0]["path"] = "required-font-not-supplied.woff2"
    return {"version": "cse.visual-profile/1", "id": "synthetic-client" if mono else "synthetic-project",
            "revision": "1", "authority": {"kind": "client" if mono else "project", "source": "brief.txt"},
            "fonts": fonts,
            "typography": {
                "body": {"font": "body", "size_pt": 10, "selectors": ["body", "p", "td", "figcaption", "svg text"]},
                "heading": {"font": "body" if mono else "heading", "size_pt": 18, "selectors": ["h1", "h2", "th"]}},
            "palette": {"ink": "#172b3a", "accent": "#225e7e", "paper": "#ffffff"},
            "assets": [
                {"id": "comp-process", "path": "runtime:assets/engineering-library/components/comp-process.svg",
                 "kind": "svg", "role": "illustration", "source": "CSE component library: comp-process",
                 "license": "See runtime:LICENSE and runtime:assets/engineering-library/sources/original/domain/computing-field.md", "adaptations": []},
                {"id": "cover-art", "path": "artwork.png", "kind": "image", "role": "editorial-art",
                 "source": "Original procedural synthetic evaluation fixture", "license": "MIT", "adaptations": []}]}


HTML = """<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Archive Relay proposal</title>
<style>@page{size:A4;margin:18mm}body{margin:0;color:#172b3a}header{height:24mm;overflow:hidden}
header img{width:100%;height:100%;object-fit:cover}table{border-collapse:collapse;width:100%}
td,th{padding:5mm;text-align:left;border-bottom:1px solid #b3c1c8}figure{margin:6mm 0}svg{max-width:100%}</style>
</head><body><header data-cse-asset="cover-art"></header><main id="accepted-body"><h1>Archive Relay proposal</h1>
<p>The analyst will review the supplied records and deliver a coded summary.</p>
<p>The client supplies the source records and reviews the draft.</p>
<table><tr><th>Work</th><th>Fee</th></tr><tr><td>Four hours of analysis</td><td>$400</td></tr></table>
<p>This proposal does not authorize collection of additional records.</p></main>
<figure id="formal-flow"><div data-cse-asset="comp-process"></div><figcaption>Supplied records → review → coded summary</figcaption></figure>
</body></html>\n"""


def prepare(case_id, destination, runtime):
    case = selected_case(case_id)
    destination = Path(destination).resolve()
    if destination.exists():
        raise ValueError("Use a new project directory; refusing existing path")
    destination.mkdir(parents=True)
    files = {}
    request = case["request"]
    if case["kind"] != "text":
        (destination / "input.html").write_text(HTML, encoding="utf-8")
        write_png(destination / "artwork.png")
        (destination / "project-visual-profile.json").write_text(json.dumps(profile(missing=case["kind"] == "blocked"), indent=2) + "\n")
        (destination / "kit-reference.json").write_text(json.dumps({"example_only": True, "font_family": "DejaVu Sans",
                "authority": "Kit specimen; does not override project or client profile"}, indent=2) + "\n")
        if case_id == "client-override":
            (destination / "client-visual-profile.json").write_text(json.dumps(profile(mono=True), indent=2) + "\n")
        request += ("\n\nUse input.html and preserve the wording inside #accepted-body verbatim. "
                    "The selected project profile is project-visual-profile.json unless the request selects the client profile. "
                    "Keep editorial artwork outside the formal flow. Reuse CSE component comp-process with its recorded identity; "
                    "it is a generic illustration and creates no accepted engineering semantics. "
                    "Keep editable output/document.html and output/figure-1.svg, and produce output/document.pdf when the selected required resources are available. "
                    "Keep rendering and selection evidence beside those outputs. Do not modify supplied inputs or install software.")
    (destination / "brief.txt").write_text(request + "\n", encoding="utf-8")
    (destination / "prompt.txt").write_text(request + "\n", encoding="utf-8")
    for path in destination.iterdir():
        if path.is_file():
            files[path.name] = digest(path)
    manifest = {"version": VERSION, "case_id": case_id, "inputs": files,
                "runtime": str(Path(runtime).resolve()), "profile": case.get("profile", "project-visual-profile.json")}
    (destination / "evaluation-inputs.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return {"status": "pass", "case_id": case_id, "project": str(destination), "prompt": str(destination / "prompt.txt")}


class RegionParser(HTMLParser):
    def __init__(self, target):
        super().__init__(convert_charrefs=True)
        self.target, self.depth, self.text = target, 0, []

    def handle_starttag(self, tag, attrs):
        if self.depth:
            if tag not in {"br", "img", "hr", "input", "meta", "link", "source", "wbr"}:
                self.depth += 1
        elif dict(attrs).get("id") == self.target:
            self.depth = 1

    def handle_endtag(self, tag):
        if self.depth:
            self.depth -= 1

    def handle_startendtag(self, tag, attrs):
        pass

    def handle_data(self, data):
        if self.depth:
            self.text.append(data)


def region_text(path, target):
    parser = RegionParser(target)
    parser.feed(Path(path).read_text(encoding="utf-8"))
    if not parser.text:
        raise ValueError("Missing or empty preserved region: " + target)
    return " ".join(" ".join(parser.text).split())


GEOMETRY = {"path": ("d",), "rect": ("x", "y", "width", "height", "rx", "ry"),
            "line": ("x1", "y1", "x2", "y2"), "circle": ("cx", "cy", "r"),
            "ellipse": ("cx", "cy", "rx", "ry"), "polygon": ("points",), "polyline": ("points",)}


def svg_geometry(path):
    raw = Path(path).read_bytes()
    if len(raw) > 33554432 or b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
        raise ValueError("Unbounded SVG or entity declarations are unsupported")
    root = ET.fromstring(raw)
    if root.tag.split("}")[-1] != "svg":
        raise ValueError("Expected SVG root")
    if len(list(root.iter())) > 10000:
        raise ValueError("SVG exceeds evaluation node limit")
    return Counter((tag, tuple((key, element.get(key, "")) for key in (*GEOMETRY[tag], "transform")))
                   for element in root.iter() if (tag := element.tag.split("}")[-1]) in GEOMETRY)


class SelectedSVGParser(HTMLParser):
    """Collect each explicitly identified SVG occurrence in an HTML document."""
    def __init__(self, asset_id):
        super().__init__(convert_charrefs=True)
        self.asset_id, self.active, self.occurrences = asset_id, [], []
        self.nodes = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if self.active or tag == "svg":
            self.nodes += 1
            if self.nodes > 10000:
                raise ValueError("SVG exceeds evaluation node limit")
        if tag == "svg":
            occurrence = Counter() if attrs.get("data-cse-source") == self.asset_id else None
            self.active.append(occurrence)
            if occurrence is not None:
                self.occurrences.append(occurrence)
        if tag in GEOMETRY:
            primitive = (tag, tuple((key, attrs.get(key, "")) for key in (*GEOMETRY[tag], "transform")))
            for occurrence in self.active:
                if occurrence is not None:
                    occurrence[primitive] += 1

    def handle_endtag(self, tag):
        if tag == "svg":
            if not self.active:
                raise ValueError("Unmatched SVG closing tag")
            self.active.pop()

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag == "svg":
            self.handle_endtag(tag)


def selected_svg_geometry(paths, asset_id, master):
    """Require the whole master in every identified occurrence, wherever placed."""
    expected, occurrences = svg_geometry(master), []
    for path in paths:
        raw = Path(path).read_bytes()
        if len(raw) > 33554432 or b"<!ENTITY" in raw.upper():
            raise ValueError("Unbounded artifact or entity declarations are unsupported")
        if Path(path).suffix.lower() == ".svg":
            # Validate XML independently; HTMLParser is deliberately tolerant of HTML.
            if b"<!DOCTYPE" in raw.upper():
                raise ValueError("SVG document type declarations are unsupported")
            root = ET.fromstring(raw)
            if root.tag.split("}")[-1] != "svg":
                raise ValueError("Expected SVG root")
        parser = SelectedSVGParser(asset_id)
        parser.feed(raw.decode("utf-8"))
        parser.close()
        if parser.active:
            raise ValueError("Unclosed SVG occurrence")
        occurrences.extend(parser.occurrences)
    complete = [bool(expected) and not expected - actual for actual in occurrences]
    return {"retained": bool(occurrences) and all(complete),
            "occurrences": len(occurrences), "complete_occurrences": sum(complete)}


def trace_records(path):
    text = Path(path).read_text(encoding="utf-8")
    try:
        record = json.loads(text)
    except json.JSONDecodeError:
        records = [json.loads(line) for line in text.splitlines() if line.strip()]
    else:
        records = record if isinstance(record, list) else [record]
    if not all(isinstance(record, dict) for record in records):
        raise ValueError("Trace records must be objects")
    return records


def commands_from_trace(path):
    commands = []
    records = trace_records(path)
    for record in records:
        if "commands" in record:
            commands.extend(item["command"] for item in record["commands"]
                            if item.get("exit_code") == 0 and isinstance(item.get("command"), str))
        if record.get("type") == "item.completed":
            item = record.get("item", {})
            if item.get("type") == "command_execution" and item.get("exit_code") == 0:
                commands.append(item["command"])
    return commands


def pdf_contains_region(path, pages, target="accepted-body"):
    expected = region_text(path, target)
    extracted = " ".join(" ".join(page.get("text", "") for page in pages).split())
    return bool(expected) and expected in extracted


def failure_matches_profile(recorded, profile, profile_path, profile_digest, replay):
    """Bind a recorded resource failure to the selected profile and current replay."""
    if not isinstance(recorded, dict):
        return False
    if recorded.get("schema") == "cse.document-environment/1":
        recorded = recorded.get("profile_preflight", {})
    return (isinstance(recorded, dict) and recorded.get("version") == "cse.visual-profile/1"
            and recorded.get("status") == "fail" and recorded.get("profile") == profile
            and recorded.get("profile_sha256") == profile_digest
            and recorded.get("profile_path") == str(profile_path.resolve())
            and all(recorded.get(key) == value for key, value in replay.items()))


def evaluate(case_id, project, runtime, trace, receipt_path="output/render-receipt.json", python=None,
             failure_receipt="output/profile-preflight.json"):
    """Check bounded artifacts; never infer correctness from the assistant's final prose."""
    case, root, runtime = selected_case(case_id), Path(project).resolve(), Path(runtime).resolve()
    checks = []
    def check(name, condition, detail=None):
        checks.append({"id": name, "status": "pass" if condition else "fail", **({"detail": detail} if detail else {})})
    manifest = json.loads((root / "evaluation-inputs.json").read_text())
    check("case_identity", manifest.get("version") == VERSION and manifest.get("case_id") == case_id)
    check("runtime_identity", manifest.get("runtime") == str(runtime))
    for relative, expected in manifest.get("inputs", {}).items():
        path = safe_path(root, relative)
        check("input_preserved:" + relative, path.is_file() and digest(path) == expected)
    expected_inputs = {"brief.txt", "prompt.txt"}
    if case["kind"] != "text":
        expected_inputs |= {"input.html", "artwork.png", "project-visual-profile.json", "kit-reference.json"}
    if case_id == "client-override":
        expected_inputs.add("client-visual-profile.json")
    check("input_inventory_present", set(manifest.get("inputs", {})) == expected_inputs)
    commands = commands_from_trace(trace)
    check("observable_trace_present", bool(commands) or any(record.get("type") == "turn.completed" for record in trace_records(trace)))
    skill_paths = [str(runtime / "skills" / name / "SKILL.md") for name in
                   ("generate-engineering-diagrams", "coordinate-engineering-work")]
    activated = any(path in command for path in skill_paths for command in commands)
    if case["kind"] == "text":
        check("visual_skill_not_loaded", not activated)
        check("renderer_not_invoked", not any("render_technical_document.cjs" in command for command in commands))
        outputs = [p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in {".pdf", ".svg", ".png", ".html", ".jpg", ".jpeg", ".gif", ".webp"}]
        check("no_graphical_artifacts", not outputs)
    elif case["kind"] == "blocked":
        from verifier.visual_profile import load, preflight, resolve_resource
        selected = safe_path(root, manifest["profile"])
        profile, profile_digest = load(selected)
        result = preflight(profile, root, runtime)
        missing = set()
        for font in profile["fonts"]:
            try:
                resolve_resource(font["path"], root, runtime)
            except FileNotFoundError:
                missing.add(font["id"])
        failed_ids = {finding.get("id") for finding in result.get("findings", []) if finding.get("status") == "fail"}
        check("required_font_unavailable", result.get("status") == "fail" and bool(missing) and missing <= failed_ids)
        check("no_final_pdf", not any(p.is_file() and p.suffix.lower() == ".pdf" for p in root.rglob("*")))
        check("selected_visual_skill_loaded", activated)
        recorded_failures = []
        sidecar = safe_path(root, failure_receipt)
        if sidecar.is_file():
            recorded_failures.append(json.loads(sidecar.read_text()))
        for record in trace_records(trace):
            item = record.get("item", {})
            if record.get("type") != "item.completed" or item.get("type") != "command_execution" or item.get("exit_code") in (None, 0):
                continue
            if not any(str(runtime / "scripts" / name) in item.get("command", "") for name in ("visual_profile.py", "render_technical_document.cjs")):
                continue
            try:
                observed = json.loads(item.get("aggregated_output", ""))
            except json.JSONDecodeError:
                continue
            recorded_failures.append(observed)
        check("required_resource_failure_recorded_and_rechecked", bool(missing) and missing <= failed_ids and
              any(failure_matches_profile(item, profile, selected, profile_digest, result) for item in recorded_failures))
    else:
        check("selected_visual_skill_loaded", activated)
        check("shared_renderer_invoked", any(str(runtime / "scripts/render_technical_document.cjs") in command for command in commands))
        receipt_file = safe_path(root, receipt_path)
        receipt = json.loads(receipt_file.read_text())
        check("renderer_receipt_schema", receipt.get("schema") == "cse.document-render/1")
        check("renderer_completed", receipt.get("status") == "pass")
        required_checks = {"actual_fonts_match", "text_within_bounds", "selected_assets_used", "svg_geometry_preserved",
                           "selected_vectors_visible", "selected_images_loaded", "no_uninspected_content", "no_external_requests",
                           "no_browser_errors", "pdf_export_checked", "sources_unchanged"}
        render_checks = receipt.get("checks", {})
        check("required_render_checks_completed", required_checks <= set(render_checks) and all(value is True for value in render_checks.values()))
        for relative in ("output/document.html", "output/document.pdf", "output/figure-1.svg"):
            path = safe_path(root, relative)
            check("artifact_present:" + relative, path.is_file() and path.stat().st_size > 0)
        if case.get("preserve_body"):
            check("accepted_body_preserved", region_text(root / "input.html", "accepted-body") == region_text(root / "output/document.html", "accepted-body"))
        master = runtime / "assets/engineering-library/components/comp-process.svg"
        geometry = selected_svg_geometry((root / "output/document.html", root / "output/figure-1.svg"), "comp-process", master)
        check("svg_master_geometry_retained", geometry["retained"], geometry)
        assets = receipt.get("assets", [])
        check("svg_occurrence_inventory_matches", geometry["occurrences"] > 0 and geometry["occurrences"] ==
              sum(item.get("occurrences", 0) for item in assets if item.get("id") == "comp-process"))
        for wanted in ("comp-process", "cover-art"):
            records = [item for item in assets if item.get("id") == wanted]
            check("selected_asset_used:" + wanted, bool(records) and all(item.get("occurrences", 0) > 0 for item in records))
            source = master if wanted == "comp-process" else root / "artwork.png"
            check("selected_asset_identity:" + wanted, bool(records) and all(item.get("source_sha256") == digest(source) for item in records))
        art = [image for asset in assets if asset.get("id") == "cover-art" for image in asset.get("images", [])]
        check("selected_image_visible_and_loaded", bool(art) and all(image.get("loaded") is True and image.get("visible") is True and image.get("within_bounds") is True for image in art))
        check("asset_roles_separate", any(a.get("id") == "cover-art" and a.get("role") == "editorial-art" for a in assets)
              and any(a.get("id") == "comp-process" and a.get("role") != "editorial-art" for a in assets))
        probes = receipt.get("font_probes", [])
        actual_names = {font.get("postScriptName") for probe in probes for font in probe.get("fonts", []) if font.get("glyphCount", 0) > 0}
        check("actual_glyph_fonts_match_selection", bool(actual_names) and actual_names == set(case["font_names"]), sorted(actual_names))
        outputs = receipt.get("outputs", [])
        if isinstance(outputs, dict):
            outputs = list(outputs.values())
        check("output_hash_inventory_present", len(outputs) >= 2)
        output_paths = set()
        for item in outputs:
            path = safe_path(receipt_file.parent, item.get("path", ""))
            output_paths.add(path)
            check("current_output:" + path.name, path.is_file() and item.get("sha256") == digest(path))
        check("delivered_artifacts_hash_bound", {root / "output/document.html", root / "output/document.pdf", root / "output/figure-1.svg"} <= output_paths)
        sources = receipt.get("inputs", [])
        check("renderer_inputs_current", len(sources) >= 2 and all(Path(item.get("path", "")).is_file() and digest(item["path"]) == item.get("sha256") for item in sources))
        preflight = receipt.get("profile_preflight", {})
        check("selected_profile_current", preflight.get("status") == "pass" and preflight.get("profile_sha256") == digest(root / manifest["profile"]))
        pdf = receipt.get("pdf", {})
        pdf_checks = pdf.get("checks", {})
        check("pdf_evidence_current_and_complete", pdf.get("schema") == "cse.document-pdf/1" and pdf.get("status") == "pass"
              and pdf.get("sha256") == digest(root / "output/document.pdf") and bool(pdf_checks) and all(value is True for value in pdf_checks.values()))
        check("pdf_fonts_match_selection", set(pdf.get("postscript_names", [])) == set(case["font_names"]))
        selected_weights = {font["weight"] for font in json.loads((root / manifest["profile"]).read_text())["fonts"]}
        check("pdf_font_weights_match_selection", set(pdf.get("weights", [])) == selected_weights)
        preflight_file = receipt_file.parent / "profile-preflight.json"
        independent = {"status": "not_run"}
        if preflight_file.is_file():
            check("profile_sidecar_matches_receipt", json.loads(preflight_file.read_text()) == preflight)
            check("selected_resources_current", all(Path(item.get("resolved_path", "")).is_file() and digest(item["resolved_path"]) == item.get("sha256")
                  for group in ("fonts", "assets") for item in preflight.get(group, [])))
            completed = subprocess.run([python or sys.executable, str(runtime / "scripts/check_document_pdf.py"),
                    "--pdf", str(root / "output/document.pdf"), "--profile-preflight", str(preflight_file), "--raster-assets", "1"],
                    capture_output=True, text=True, timeout=30)
            try:
                independent = json.loads(completed.stdout)
            except json.JSONDecodeError:
                independent = {"status": "error"}
        check("independent_pdf_inspection", independent.get("status") == "pass" and independent.get("sha256") == digest(root / "output/document.pdf")
              and set(independent.get("postscript_names", [])) == set(case["font_names"]) and set(independent.get("weights", [])) == selected_weights)
        if case.get("preserve_body"):
            check("accepted_body_present_in_pdf", independent.get("status") == "pass" and pdf_contains_region(root / "input.html", independent.get("pages", [])))
    return {"schema": VERSION, "case_id": case_id,
            "status": "pass" if checks and all(c["status"] == "pass" for c in checks) else "fail",
            "claim_scope": "bounded_observable_artifacts_and_recorded_commands",
            "session_freshness": "not_inferred_from_trace", "checks": checks}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list")
    prepare_parser = sub.add_parser("prepare")
    prepare_parser.add_argument("--case", required=True)
    prepare_parser.add_argument("--output", type=Path, required=True)
    prepare_parser.add_argument("--runtime", type=Path, default=RUNTIME)
    check_parser = sub.add_parser("check")
    check_parser.add_argument("--case", required=True)
    check_parser.add_argument("--project", type=Path, required=True)
    check_parser.add_argument("--runtime", type=Path, required=True)
    check_parser.add_argument("--trace", type=Path, required=True)
    check_parser.add_argument("--render-receipt", default="output/render-receipt.json")
    check_parser.add_argument("--python", help="Existing Python interpreter with PyMuPDF for independent PDF inspection; defaults to this interpreter")
    check_parser.add_argument("--failure-receipt", default="output/profile-preflight.json",
                              help="Project-relative typed profile failure receipt for the missing-font case")
    args = parser.parse_args()
    try:
        if args.command == "list":
            result = {"schema": VERSION, "cases": list(cases().values())}
        elif args.command == "prepare":
            result = prepare(args.case, args.output, args.runtime)
        else:
            result = evaluate(args.case, args.project, args.runtime, args.trace, args.render_receipt, args.python, args.failure_receipt)
    except (OSError, ValueError, KeyError, TypeError, ET.ParseError, subprocess.SubprocessError) as error:
        result = {"schema": VERSION, "status": "error", "error": str(error)}
    print(json.dumps(result, indent=2))
    return 0 if result.get("status", "pass") == "pass" else 1


if __name__ == "__main__":
    sys.path.insert(0, str(RUNTIME))
    raise SystemExit(main())
