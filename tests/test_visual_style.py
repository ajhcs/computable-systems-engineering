import json
from pathlib import Path
import sys
import tempfile
import unittest
from copy import deepcopy
from fractions import Fraction
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verifier.visual_style import load_profile, contrast, presentation_style, require_supported_text, font_css, text_width, wrap_text, function_tree_roles

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

    def test_tree_role_catalog_legacy_profiles_and_independent_resolution(self):
        p=load_profile();saved=deepcopy(p);roles=function_tree_roles(p)
        self.assertEqual(roles['pairs']['orange_on_violet']['fill_color'],'#e0dae6')
        self.assertEqual(roles['pairs']['orange_on_violet']['frame_color'],'#894b25')
        self.assertEqual(roles['branch_pairs'],['blue_on_blue','orange_on_orange','green_on_green'])
        for name,family in [('blue_on_blue','blue'),('orange_on_orange','tangerine'),('green_on_green','green')]:
            self.assertEqual(roles['pairs'][name]['fill_color'],p['palette']['families'][family]['tint'])
            self.assertEqual(roles['pairs'][name]['frame_color'],p['palette']['families'][family]['shade'])
            self.assertEqual(roles['pairs'][name]['connector_color'],p['palette']['families'][family]['shade'])
        self.assertNotIn('brick_on_cream',roles['branch_pairs'])
        self.assertNotIn('green_on_cool',roles['branch_pairs'])
        for pair in roles['pairs'].values():
            self.assertGreaterEqual(pair['contrast']['text'],4.5)
            self.assertTrue(all(v>=3 for k,v in pair['contrast'].items() if k!='text'))
        p['function_tree_roles']['pairs']['orange_on_violet']['connector']='blue.shade'
        changed=function_tree_roles(p)['pairs']['orange_on_violet']
        self.assertEqual(changed['connector_color'],'#27456f')
        self.assertEqual(changed['frame_color'],'#894b25')
        self.assertEqual(changed['fill_color'],'#e0dae6')
        legacy=deepcopy(saved);legacy.pop('function_tree_roles')
        self.assertEqual(load_profile(legacy)['function_tree_roles'],saved['function_tree_roles'])
        tokens=json.loads((ROOT/'assets/diagram-style/design-tokens.json').read_text())
        self.assertEqual(tokens['function_tree_implementation']['roles'],saved['function_tree_roles'])
        self.assertEqual(load_profile(),saved)

    def test_tree_role_refusals_prevent_unknown_or_low_contrast_pairs(self):
        for defect in ('unknown_ref','unknown_pair','header_contrast','role_tone','css','status','connector_contrast'):
            p=load_profile();roles=p['function_tree_roles'];pair=roles['pairs']['orange_on_violet']
            if defect=='unknown_ref':pair['fill']='missing.tint'
            elif defect=='unknown_pair':roles['root_pair']='missing'
            elif defect=='header_contrast':p['palette']['families']['blue']['tint']=p['palette']['families']['blue']['shade']
            elif defect=='role_tone':pair['connector']='blue.tint'
            elif defect=='css':pair['style']='anything'
            elif defect=='status':roles['status']='universally_accepted'
            else:p['palette']['families']['green']['shade']='#eeeeea'
            with self.subTest(defect=defect),self.assertRaises(ValueError):load_profile(p)

    def test_absolute_contrast_oracles(self):
        self.assertAlmostEqual(contrast("#000000", "#ffffff"), 21)
        self.assertEqual(contrast("#123456", "#123456"), 1)
        with self.assertRaises(ValueError): contrast("transparent", "#ffffff")

    def test_contrast_accumulation_matches_exact_sum_of_float_terms(self):
        # Exact rational addition independently rounds the weighted float terms
        # once. Sequential float addition (Python <=3.11 sum) loses a low bit
        # for these real palette colors and changes serialized report hashes.
        def luminance(color):
            channels = [int(color[i:i+2], 16) / 255 for i in (1, 3, 5)]
            channels = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in channels]
            terms = [Fraction.from_float(v * weight) for v, weight in zip(channels, (0.2126, 0.7152, 0.0722))]
            return float(sum(terms, Fraction()))
        for foreground, background in (('#25282d', '#d5e2da'), ('#315e43', '#d5e2da'),
                                       ('#7f362f', '#eeeeea'), ('#7f362f', '#ece1ce')):
            low, high = sorted((luminance(foreground), luminance(background)))
            with self.subTest(foreground=foreground, background=background):
                self.assertEqual(contrast(foreground, background), (high + 0.05) / (low + 0.05))

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

    def test_measured_wrapping_preserves_text_and_tracks_actual_face(self):
        self.assertGreater(text_width('WWW',22),text_width('iii',22)*2)
        self.assertAlmostEqual(text_width('ABC',22),text_width('A',22)+text_width('B',22)+text_width('C',22))
        for text in ('A long engineering name with all spaces retained', 'W'*64, '  exact  spaces  '):
            lines=wrap_text(text,150,22)
            self.assertEqual(''.join(lines),text)
            self.assertTrue(all(text_width(line,22)<=150 for line in lines))
        with self.assertRaises(ValueError):wrap_text('W',1,22)

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
