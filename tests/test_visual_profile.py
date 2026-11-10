"""Selected project resources and overrides retain explicit, bounded identities."""
import copy
from hashlib import sha256
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verifier import visual_profile as v


def synthetic_font(name='FixtureSans', weight=400):
    """A minimal uncompressed table fixture, never claimed to be renderable."""
    encoded = name.encode('utf-16-be')
    names = struct.pack('>HHH', 0, 1, 18) + struct.pack('>HHHHHH', 3, 1, 0x409, 6, len(encoded), 0) + encoded
    os2 = struct.pack('>HHH', 0, 0, weight)
    start = 12 + 2 * 16
    return (struct.pack('>IHHHH', 0x10000, 2, 0, 0, 0) +
            struct.pack('>4sIII', b'name', 0, start, len(names)) +
            struct.pack('>4sIII', b'OS/2', 0, start + len(names), len(os2)) + names + os2)


class ProfileTests(unittest.TestCase):
    def setUp(self):
        (ROOT / '.tmp').mkdir(exist_ok=True)
        temp = tempfile.TemporaryDirectory(dir=ROOT / '.tmp')
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        (self.root / 'font.ttf').write_bytes(synthetic_font())
        (self.root / 'symbol.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M1 1L19 19" stroke="#111"/></svg>')
        self.profile = {'version': v.VERSION, 'id': 'SyntheticProfile', 'revision': '1',
                        'authority': {'kind': 'project', 'source': 'synthetic project brief'},
                        'fonts': [{'id': 'body', 'family': 'Fixture Sans', 'path': 'font.ttf',
                                   'weight': 400, 'postscript_name': 'FixtureSans'}],
                        'typography': {'body': {'font': 'body', 'size_pt': 10, 'selectors': ['body', 'svg text']}},
                        'palette': {'ink': '#222222'},
                        'assets': [{'id': 'FixtureSymbol', 'path': 'symbol.svg', 'kind': 'svg',
                                    'role': 'formal-symbol', 'source': 'synthetic geometry',
                                    'license': 'CC0 test fixture', 'adaptations': []}]}
        self.path = self.root / 'profile.json'
        self.save()

    def save(self):
        self.path.write_text(json.dumps(self.profile))

    def cli(self, *args):
        return subprocess.run([sys.executable, '-B', str(ROOT / 'scripts/visual_profile.py'),
                               *args, '--root', str(self.root)], capture_output=True, text=True, cwd=self.root)

    def test_preflight_records_selected_sources_and_real_font_table_identity(self):
        result = v.preflight(self.profile, self.root)
        self.assertEqual(result['status'], 'pass')
        self.assertEqual(result['claim_scope'], v.CLAIM)
        self.assertEqual(result['fonts'][0]['font_metadata']['postscript_name'], 'FixtureSans')
        self.assertEqual(result['fonts'][0]['font_metadata']['weight'], 400)
        self.assertEqual(result['assets'][0]['sha256'], sha256((self.root / 'symbol.svg').read_bytes()).hexdigest())
        self.assertEqual(len(result['assets'][0]['svg_geometry_sha256']), 64)

    def test_explicit_client_project_example_precedence_is_whole_profile(self):
        candidates = dict(explicit='request.json', client='client.json', project='project.json', example='example.json')
        for expected in ('explicit', 'client', 'project', 'example'):
            self.assertEqual(v.select_profile(**candidates), (expected, candidates[expected]))
            candidates[expected] = None
        with self.assertRaises(v.Invalid): v.select_profile(**candidates)

    def test_missing_explicit_choice_does_not_fall_through_to_valid_example(self):
        result = self.cli('preflight', '--profile', 'missing.json', '--example-profile', str(self.path))
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)['status'], 'error')
        self.assertNotIn('profile', json.loads(result.stdout))

    def test_missing_required_font_never_uses_a_system_substitute(self):
        (self.root / 'font.ttf').unlink()
        result = v.preflight(self.profile, self.root)
        self.assertEqual(result['status'], 'fail')
        self.assertEqual(result['fonts'], [])
        self.assertEqual(result['findings'][0]['id'], 'body')
        self.save()
        command = self.cli('preflight', '--profile', str(self.path))
        self.assertEqual(command.returncode, 1)

    def test_declared_identity_mismatch_and_stale_source_digest_fail(self):
        for key, wrong in (('postscript_name', 'GuessedFromFilename'), ('weight', 600), ('sha256', '0' * 64)):
            bad = copy.deepcopy(self.profile)
            bad['fonts'][0][key] = wrong
            with self.subTest(key=key): self.assertEqual(v.preflight(bad, self.root)['status'], 'fail')
        self.profile['assets'][0]['sha256'] = '0' * 64
        self.assertEqual(v.preflight(self.profile, self.root)['status'], 'fail')

    def test_svg_geometry_tracks_primitives_but_preserves_paint_and_id_adaptation(self):
        raw = (self.root / 'symbol.svg').read_bytes()
        self.assertEqual(v.svg_geometry(raw), v.svg_geometry(raw.replace(b'#111', b'#ff0000').replace(b'<path ', b'<path id="occurrence-2" ')))
        self.assertNotEqual(v.svg_geometry(raw), v.svg_geometry(raw.replace(b'M1 1L19 19', b'M1 1L10 19')))
        self.assertNotEqual(v.svg_geometry(raw), v.svg_geometry(raw.replace(b'<path ', b'<path transform="scale(2)" ')))

    def test_runtime_resources_are_explicit_and_pinned_to_the_runtime_root(self):
        self.profile['fonts'][0] = {'id': 'body', 'family': 'Example Inter', 'weight': 400,
                                    'path': 'runtime:assets/diagram-style/fonts/inter-400.woff2'}
        result = v.preflight(self.profile, self.root, ROOT)
        self.assertEqual(result['status'], 'pass')
        self.assertEqual(result['fonts'][0]['format'], 'woff2')
        self.assertEqual(result['fonts'][0]['font_metadata']['identity_scope'], 'requires_rendered_glyph_and_pdf_check')
        self.assertEqual(v.preflight(self.profile, self.root)['status'], 'fail')

    def test_escape_paths_and_symlink_escape_fail(self):
        for bad_path in ('../outside.ttf', '/absolute.ttf', './font.ttf', 'a//font.ttf', 'runtime:../outside', 'http://example/font.ttf'):
            bad = copy.deepcopy(self.profile)
            bad['fonts'][0]['path'] = bad_path
            with self.subTest(path=bad_path), self.assertRaises(v.Invalid): v.validate_profile(bad)
        (self.root / 'escape').symlink_to(ROOT, target_is_directory=True)
        self.profile['fonts'][0]['path'] = 'escape/assets/diagram-style/fonts/inter-400.woff2'
        self.assertEqual(v.preflight(self.profile, self.root, ROOT)['status'], 'fail')

    def test_malformed_unsupported_and_nonfinite_profiles_cannot_validate(self):
        bads = []
        for change in (lambda p: p.update(version='next'), lambda p: p.update(unknown=True),
                       lambda p: p['typography']['body'].update(font='missing'),
                       lambda p: p['typography']['body'].update(size_pt=float('nan')),
                       lambda p: p['fonts'].append(copy.deepcopy(p['fonts'][0])),
                       lambda p: p['typography']['body'].update(selectors=['body{color:red}'])):
            bad = copy.deepcopy(self.profile); change(bad); bads.append(bad)
        for bad in bads:
            with self.subTest(bad=bad), self.assertRaises(v.Invalid): v.validate_profile(bad)
        self.path.write_text('{"version":"a","version":"b"}')
        with self.assertRaises(v.Invalid): v.load(self.path)

    def test_editorial_art_role_does_not_change_or_approve_formal_source(self):
        before = (self.root / 'symbol.svg').read_bytes()
        self.profile['assets'].append({'id': 'CoverArt', 'path': 'symbol.svg', 'kind': 'svg',
                                      'role': 'editorial-art', 'source': 'synthetic art', 'license': 'CC0',
                                      'adaptations': ['reused as cover art only']})
        result = v.preflight(self.profile, self.root)
        self.assertEqual(result['status'], 'pass')
        self.assertEqual([a['role'] for a in result['assets']], ['formal-symbol', 'editorial-art'])
        self.assertNotIn('approval', result)
        self.assertEqual((self.root / 'symbol.svg').read_bytes(), before)

    def test_invalid_font_image_svg_and_resource_limits_do_not_pass(self):
        (self.root / 'font.ttf').write_bytes(b'not a font')
        self.assertEqual(v.preflight(self.profile, self.root)['status'], 'fail')
        (self.root / 'font.ttf').write_bytes(synthetic_font())
        bad = copy.deepcopy(self.profile)
        bad['assets'][0]['kind'] = 'image'
        self.assertEqual(v.preflight(bad, self.root)['status'], 'fail')
        (self.root / 'symbol.svg').write_text('<svg>broken')
        self.assertEqual(v.preflight(self.profile, self.root)['status'], 'fail')
        with patch.dict(v.LIMITS, total_resource_bytes=1):
            result = v.preflight(self.profile, self.root)
        self.assertEqual(result['status'], 'fail')
        self.assertEqual(result['fonts'], [])
        self.assertEqual(result['assets'], [])

    def test_validate_is_structural_and_receipt_never_overwrites_inputs_or_evidence(self):
        result = self.cli('validate', '--profile', str(self.path))
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)['claim_scope'], 'visual_profile_structure_only')
        receipt = self.root / 'preflight.json'
        first = self.cli('preflight', '--profile', str(self.path), '--out', str(receipt))
        self.assertEqual(first.returncode, 0)
        recorded = receipt.read_bytes()
        second = self.cli('preflight', '--profile', str(self.path), '--out', str(receipt))
        self.assertEqual(second.returncode, 2)
        self.assertEqual(receipt.read_bytes(), recorded)
        original = self.path.read_bytes()
        self.assertEqual(self.cli('preflight', '--profile', str(self.path), '--out', str(self.path)).returncode, 2)
        self.assertEqual(self.path.read_bytes(), original)

    def test_overlapping_role_precedence_survives_cli_stdout_and_saved_receipt(self):
        # An element may have both classes. The authored last role must win
        # their equally specific CSS selectors, even when its name sorts first.
        self.profile['typography'] = {
            'zFirst': {'font': 'body', 'size_pt': 10, 'selectors': ['.normal']},
            'aLast': {'font': 'body', 'size_pt': 12, 'selectors': ['.emphasis']}}
        self.save()
        receipt = self.root / 'ordered-preflight.json'
        command = self.cli('preflight', '--profile', str(self.path), '--out', str(receipt))
        self.assertEqual(command.returncode, 0, command.stdout + command.stderr)
        for result in (json.loads(command.stdout), json.loads(receipt.read_text())):
            roles = result['profile']['typography']
            self.assertEqual(list(roles), ['zFirst', 'aLast'])
            # Both selectors match the requested synthetic document label.
            matches = [role for role in roles.values()
                       if any(selector in ('.normal', '.emphasis') for selector in role['selectors'])]
            self.assertEqual(matches[-1]['size_pt'], 12)


if __name__ == '__main__':
    unittest.main()
