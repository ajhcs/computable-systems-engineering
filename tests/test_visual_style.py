import json
from pathlib import Path
import sys
import tempfile
import unittest
from copy import deepcopy
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verifier.visual_style import load_profile, contrast, presentation_style, require_supported_text, font_css

class VisualStyleTests(unittest.TestCase):
    def test_palette_and_provisional_scope(self):
        p = load_profile()
        self.assertEqual(len(p["palette"]["families"]), 8)
        self.assertEqual(p["body_variants"]["status"], "provisional")
        self.assertEqual(p["limits"]["color_semantics"], "none")
        for body, expected in (("paper", "#eeeeea"), ("white", "#ffffff"), ("tint", "#f6f5f8")):
            s = presentation_style(body=body)
            self.assertEqual(s["fill"], expected)
            self.assertGreaterEqual(s["contrast"]["body_text"], 4.5)
            self.assertGreaterEqual(s["contrast"]["accent_text"], 4.5)

    def test_absolute_contrast_oracles(self):
        self.assertAlmostEqual(contrast("#000000", "#ffffff"), 21)
        self.assertEqual(contrast("#123456", "#123456"), 1)
        with self.assertRaises(ValueError): contrast("transparent", "#ffffff")

    def test_effective_stroke_and_small_target_refusal(self):
        s = presentation_style(target_width=900, canvas_width=1200)
        self.assertAlmostEqual(s["stroke_width"] * 900 / 1200, 2)
        with self.assertRaises(ValueError): presentation_style(target_width=400, canvas_width=1200)
        for value in (True, float("inf"), float("nan"), 0):
            with self.subTest(value=value), self.assertRaises(ValueError):
                presentation_style(target_width=value)
        with self.assertRaises(ValueError): presentation_style(body="approved-default")

    def test_profile_refuses_unknown_or_semantic_changes(self):
        for mutate in ("unknown", "numeric", "status", "color", "contrast"):
            p = deepcopy(load_profile())
            if mutate == "unknown": p["execute"] = "anything"
            elif mutate == "numeric": p["numeric_proposal"]["body_size"] = True
            elif mutate == "status": p["body_variants"]["status"] = "accepted"
            elif mutate == "color": p["palette"]["ink"] = "url(file:///private)"
            else: p["palette"]["ink"] = "#eeeeea"
            with tempfile.TemporaryDirectory(dir=ROOT / ".tmp") as folder:
                path = Path(folder) / "profile.json"; path.write_text(json.dumps(p))
                with self.assertRaises(ValueError): load_profile(path)

    def test_nondefault_profile_dict_and_file_share_strict_validation(self):
        p = load_profile()
        p["numeric_proposal"]["body_size"] = 23
        expected = deepcopy(p)
        with tempfile.TemporaryDirectory(dir=ROOT / ".tmp") as folder:
            path = Path(folder) / "profile.json"
            path.write_text(json.dumps(p))
            self.assertEqual(presentation_style(load_profile(path))["body_size"], 23)
            self.assertEqual(presentation_style(path)["body_size"], 23)
        self.assertEqual(p, expected)
        p["body_variants"]["status"] = "accepted"
        with self.assertRaises(ValueError): presentation_style(p)

    def test_font_bytes_and_explicit_coverage(self):
        css = font_css()
        self.assertEqual(css.count("@font-face"), 4)
        self.assertEqual(css.count("data:font/woff2;base64,"), 4)
        self.assertNotIn("url(http", css)
        self.assertIn("SIL OPEN FONT LICENSE", css)
        require_supported_text("ProcessSample · F0")
        for value in ("theta \u03b8", "<line>\n", ""):
            with self.assertRaises(ValueError): require_supported_text(value)

if __name__ == "__main__":
    (ROOT / ".tmp").mkdir(exist_ok=True)
    unittest.main()
