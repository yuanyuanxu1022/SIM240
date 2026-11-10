"""Exercise completed-result packet rejection independently of numerical fixtures."""
from pathlib import Path
import json
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'analysis'))
from evidence import EvidenceError,sha
import check_results as checker

class PacketGuards(unittest.TestCase):
    def write_release(self, folder, **change):
        r=dict(protocol_id='URV-v1',simulation_authorized=False,preparation_only_build=True,
            author_external_data_history_confirmation='PENDING',inputs_sha256={},
            fixture_label='SYNTHETIC_RELEASE_GUARD_TEST_NOT_AN_EXECUTION_CONTRACT')
        r.update(change);p=folder/'release.json';p.write_text(json.dumps(r));return p

    def test_preparation_release_always_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            p=self.write_release(Path(temp))
            with self.assertRaisesRegex(EvidenceError,'zero-step preparation only'):
                checker.binding(p,sha(p))

    def test_pending_history_refused_even_if_other_flags_wrongly_enabled(self):
        with tempfile.TemporaryDirectory() as temp:
            p=self.write_release(Path(temp),simulation_authorized=True,preparation_only_build=False)
            with self.assertRaisesRegex(EvidenceError,'history pending'):
                checker.binding(p,sha(p))

    def test_tampered_source_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp);source=folder/'synthetic_input.txt';source.write_text('bound input')
            digest=sha(source);source.write_text('changed input')
            p=self.write_release(folder,simulation_authorized=True,preparation_only_build=False,
                author_external_data_history_confirmation='CONFIRMED',inputs_sha256={str(source):digest})
            with self.assertRaisesRegex(EvidenceError,'source/input changed'):
                checker.binding(p,sha(p))

    def packet(self, folder):
        run=folder/'SYNTHETIC_INCOMPLETE_PACKET';run.mkdir()
        completion=dict(release_sha256='synthetic-anchor',independent_process_exit_code=0,
            inputs_unchanged=True,inputs_after_sha256={},planned_case_id='URV1_H75_P_dx5_a100000',
            run_id='SYNTHETIC',output_sha256={})
        (folder/'SYNTHETIC_PATH_DECLARATIONS_ONLY.json').write_text('{}')
        return run,completion

    def test_missing_raw_files_cannot_pass(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp);run,c=self.packet(folder)
            (run/'completion.json').write_text(json.dumps(c))
            # Only the release layer is replaced; this test targets packet completeness.
            with patch.object(checker,'binding',return_value={'inputs_sha256':{}}):
                with self.assertRaisesRegex(EvidenceError,'incomplete output manifest'):
                    checker.check_run(run,folder/'SYNTHETIC_PATH_DECLARATIONS_ONLY.json','synthetic-anchor',folder/'analysis')

    def test_nonzero_independent_exit_cannot_pass(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp);run,c=self.packet(folder);c['independent_process_exit_code']=3
            (run/'completion.json').write_text(json.dumps(c))
            with patch.object(checker,'binding',return_value={'inputs_sha256':{}}):
                with self.assertRaisesRegex(EvidenceError,'independent exit'):
                    checker.check_run(run,folder/'SYNTHETIC_PATH_DECLARATIONS_ONLY.json','synthetic-anchor',folder/'analysis')

    def test_postrun_source_map_cannot_be_truncated(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp);run,c=self.packet(folder)
            (run/'completion.json').write_text(json.dumps(c))
            with patch.object(checker,'binding',return_value={'inputs_sha256':{'missing':'sha'}}):
                with self.assertRaisesRegex(EvidenceError,'post-run input binding incomplete'):
                    checker.check_run(run,folder/'SYNTHETIC_PATH_DECLARATIONS_ONLY.json','synthetic-anchor',folder/'analysis')

if __name__=='__main__': unittest.main(verbosity=2)
