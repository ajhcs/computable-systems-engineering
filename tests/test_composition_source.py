"""Exact bounded source reads and candidate/saved snapshot separation."""
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace
import sys
import tempfile
import unittest
from unittest.mock import patch
from uuid import uuid4
import runpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verifier.composition_source import chunk, files
from verifier.composition_edit import EditError
from verifier.composition_project import CompositionProject
from verifier.composition_session import CompositionSession


class SourceReadTests(unittest.TestCase):
    def test_unicode_codepoints_and_crlf_reassemble_exact_bytes(self):
        text = 'a\r\nΔ😀b\r\n'
        document = SimpleNamespace(files={'model.sysml': text}, revision='captured_bundle')
        self.assertEqual(files(document), [{'file':'model.sysml','sha256':sha256(text.encode()).hexdigest(),'codepoints':8}])
        pieces, offset = [], 0
        while offset is not None:
            row = chunk(document, 'model.sysml', offset, 2)
            self.assertEqual(row['offset_units'], 'unicode_codepoints')
            self.assertEqual(row['chunk_sha256'], sha256(row['text'].encode()).hexdigest())
            pieces.append(row['text']);offset = row['next_offset']
        self.assertEqual(''.join(pieces).encode(), b'a\r\n\xce\x94\xf0\x9f\x98\x80b\r\n')

    def test_offsets_limits_bool_and_foreign_paths_refuse(self):
        document = SimpleNamespace(files={'model.sysml':'native'}, revision='bundle')
        for file,offset,limit in [('../private',0,1),('/etc/passwd',0,1),('model.sysml',True,1),
                                 ('model.sysml',0,False),('model.sysml',7,1),('model.sysml',-1,1),
                                 ('model.sysml',0,0),('model.sysml',0,65537)]:
            with self.subTest(file=file,offset=offset,limit=limit), self.assertRaises(EditError):
                chunk(document,file,offset,limit)
        self.assertEqual(chunk(document,'model.sysml',6,1)['text'],'')
        self.assertIsNone(chunk(document,'model.sysml',6,1)['next_offset'])

    def test_saved_and_checked_candidate_chunks_do_not_publish_or_repeat_native_preview(self):
        cls = runpy.run_path(str(ROOT/'tests/test_composition_ownership.py'))['OwnershipTests']
        cls.setUpClass();before=cls.document
        from verifier.composition_ownership import destinations
        destination=next(row['target']for row in destinations(before)if row['native_name']=='P::current::right')
        request={'operation':'reparent','request_id':str(uuid4()),'expected_revision':1,'element_id':cls.subject,
                 'destination':destination,'composition_transition':None,'view_effects':cls().effects(),'checked_bundle_sha256':None}
        with tempfile.TemporaryDirectory()as temporary:
            project,first=CompositionProject.create(Path(temporary)/'source.git',before.files,
                project_id=before.project_id,request_id=str(uuid4()))
            session=CompositionSession(project,'PC_OWN')
            args={'expected_revision':1,'expected_bundle_sha256':before.revision,'file':'model.sysml','offset':0,'limit':65536}
            saved=session.read_source(**args,request=None)
            self.assertEqual(saved['text'],before.files['model.sysml'])
            self.assertIsNone(saved['request_sha256'])
            with patch.object(project,'preview',wraps=project.preview)as counted:
                preview=session.preview(request)
                checked=preview['checked_request']
                candidate=session.read_source(**args,request=checked)
                self.assertEqual(candidate['bundle_sha256'],preview['candidate_bundle_sha256'])
                self.assertEqual(candidate['request_sha256'],preview['request_sha256'])
                self.assertIn('P::current::right::sensor',candidate['text'])
                self.assertEqual(session.read_source(**{**args,'offset':3,'limit':7},request=checked)['text'],candidate['text'][3:10])
                self.assertEqual(counted.call_count,1)
            self.assertEqual(project.head(),first['commit'])
            result=session.apply(checked)
            self.assertEqual(result['receipt']['revision'],2)
            with self.assertRaises(EditError)as caught:
                session.read_source(**args,request=checked)
            self.assertEqual(caught.exception.code,'stale_revision')
            current=project.snapshot()
            fresh=session.read_source(expected_revision=2,expected_bundle_sha256=current['document'].revision,
                request=None,file='model.sysml',offset=0,limit=65536)
            self.assertEqual(fresh['text'],candidate['text'])
            self.assertEqual(fresh['snapshot'],'saved')


if __name__=='__main__':
    unittest.main()
