"""The shared copy inventory detects drift without changing standalone files."""
from pathlib import Path
import sys,tempfile,unittest

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from verifier.standalone import COPY_GROUPS,check_copies

class CopyTests(unittest.TestCase):
    def test_current_independent_skills_have_equal_declared_copies(self):
        self.assertEqual(check_copies(ROOT)['status'],'pass')
    def test_one_changed_or_missing_helper_cannot_be_hidden(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'.tmp') as d:
            root=Path(d)
            for paths in COPY_GROUPS.values():
                for name in paths:
                    p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('same')
            self.assertEqual(check_copies(root)['status'],'pass')
            name=COPY_GROUPS['launcher'][-1];(root/name).write_text('different')
            result=check_copies(root)
            self.assertEqual(result['status'],'fail');self.assertEqual((root/name).read_text(),'different')
            (root/name).unlink()
            self.assertEqual(check_copies(root)['status'],'error')
    def test_inventory_retains_operational_helpers_and_all_four_review_routes(self):
        self.assertEqual(len(COPY_GROUPS['operational-helper']),2)
        self.assertEqual(len(COPY_GROUPS['work-review']),4)
        self.assertTrue(all(name.startswith('skills/') for values in COPY_GROUPS.values() for name in values))

if __name__=='__main__':
    (ROOT/'.tmp').mkdir(exist_ok=True);unittest.main()
