import json
import shlex
import sys
import tempfile
import unittest
from pathlib import Path

from uars import apply_reviews, digest, metrics, proposal, verify
from uars_v06_preflight import conservative_baseline, windows


class PracticalVerification(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.text = 'Испытание: прибор работает только при 25 °C. Прибор не работает при 80 °C.\n'
        (self.root / 'source.txt').write_text(self.text, encoding='utf-8')
        self.batch = {'sources': [{'id': 's1', 'path': 'source.txt',
                                  'source_url': 'urn:uars:test', 'sha256': digest(self.text.encode())}],
                      'claims': [{'id': 'c1', 'text': 'Прибор работает при 80 °C.',
                                  'scope': 'document_content', 'source_id': 's1'}]}
        self.path = self.root / 'batch.json'
        self.save()

    def save(self):
        self.path.write_text(json.dumps(self.batch), encoding='utf-8')

    def review(self, report, **updates):
        entry = {'claim_id': 'c1', 'support_label': 'CONTRADICTED',
                 'reviewer': 'test fixture', 'reason': 'Explicit negation at 80 °C',
                 'decisive_start': self.text.index('Прибор не'), 'decisive_end': len(self.text) - 1,
                 'context_start': 0, 'context_end': len(self.text)}
        entry.update(updates)
        return apply_reviews(report, self.path, {'run_id': report['run_id'], 'reviews': [entry]})

    def test_absent_model_keeps_label_null(self):
        r = verify(self.path)
        self.assertIsNone(r['results'][0]['support_label'])
        self.assertEqual(metrics(r)['decision_coverage'], 0)
        self.assertIsNone(metrics(r)['accuracy'])

    def test_hash_mismatch_stops_run(self):
        (self.root / 'source.txt').write_text('tampered', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            verify(self.path)

    def test_source_and_scope_validation(self):
        for field, value in [('scope', 'unknown'), ('source_id', 'missing')]:
            with self.subTest(field=field):
                original = self.batch['claims'][0][field]
                self.batch['claims'][0][field] = value
                self.save()
                with self.assertRaises(ValueError):
                    verify(self.path)
                self.batch['claims'][0][field] = original

    def test_no_support_from_negated_or_quoted_substring(self):
        for text in ['It is false that the device works.', 'Claim: the device works. This is wrong.',
                     'If supply is stable, the device works.', 'SS is not ß.']:
            self.assertEqual(conservative_baseline('the device works', text)['support_label'], 'REVIEW')

    def test_review_offsets_reconstruct_unicode_source(self):
        row = self.review(verify(self.path))['results'][0]
        self.assertEqual(row['support_label'], 'CONTRADICTED')
        self.assertEqual(row['system_outcome'], 'DECIDED')
        self.assertEqual(row['decisive_span']['text'], 'Прибор не работает при 80 °C.')
        self.assertEqual(row['context_span']['text'], self.text)

    def test_context_must_contain_quote(self):
        with self.assertRaisesRegex(ValueError, 'outside context'):
            self.review(verify(self.path), context_end=10)

    def test_insufficient_requires_full_document(self):
        with self.assertRaisesRegex(ValueError, 'full document'):
            self.review(verify(self.path), support_label='INSUFFICIENT', context_end=10)
        row = self.review(verify(self.path), support_label='INSUFFICIENT')['results'][0]
        self.assertIsNone(row['decisive_span'])

    def test_temporal_review_cannot_override_gate(self):
        self.batch['claims'][0]['scope'] = 'current_status'
        self.save()
        report = verify(self.path)
        self.assertEqual(report['results'][0]['reason'], 'temporal_status_not_certified')
        with self.assertRaisesRegex(ValueError, 'temporal certification'):
            self.review(report)

    def test_stale_review_and_changed_source_rejected(self):
        report = verify(self.path)
        with self.assertRaisesRegex(ValueError, 'different run'):
            apply_reviews(report, self.path, {'run_id': 'wrong', 'reviews': []})
        self.batch['claims'][0]['text'] = 'changed claim'
        self.save()
        with self.assertRaisesRegex(ValueError, 'batch changed'):
            self.review(report)

    def test_repeated_and_invented_model_quote_rejected(self):
        candidate = {'id': 'C00', 'start': 0, 'end': 9, 'text': 'test test'}
        for quote in ['test', 'not here']:
            with self.assertRaises(ValueError):
                proposal({'support_label': 'SUPPORTED', 'confidence': 'high',
                          'candidate_id': 'C00', 'decisive_text': quote}, [candidate])

    def command(self, code):
        return shlex.join([sys.executable, '-c', code])

    def test_judge_proposal_never_becomes_accepted_label(self):
        payload = {'support_label': 'CONTRADICTED', 'confidence': 'high',
                   'candidate_id': 'C00', 'decisive_text': 'Прибор не работает при 80 °C.'}
        cmd = self.command('import json; print(json.dumps(' + repr(payload) + '))')
        report = verify(self.path, cmd, model_id='fixture', model_digest='fixture-only')
        row = report['results'][0]
        self.assertEqual(row['proposal']['support_label'], 'CONTRADICTED')
        self.assertIsNone(row['support_label'])
        self.assertEqual(row['system_outcome'], 'REVIEW')
        self.assertFalse(report['semantic_quality_measured'])

    def test_judge_timeout_and_bad_json_are_errors(self):
        for cmd in [self.command('import time; time.sleep(1)'), self.command('print("bad")')]:
            row = verify(self.path, cmd, timeout=0.05, model_id='fixture', model_digest='fixture')['results'][0]
            self.assertEqual(row['system_outcome'], 'ERROR')
            self.assertIsNone(row['support_label'])

    def test_model_identity_and_timeout_required(self):
        with self.assertRaises(ValueError):
            verify(self.path, 'echo')
        for timeout in [0, -1, float('nan'), float('inf')]:
            with self.assertRaises(ValueError):
                verify(self.path, timeout=timeout)

    def test_windows_cover_end_and_preserve_exact_offsets(self):
        text = ('начало ' * 220) + '\nEND\n'
        chunks = windows(text)
        self.assertEqual(chunks[-1]['end'], len(text))
        for chunk in chunks:
            self.assertEqual(text[chunk['start']:chunk['end']], chunk['text'])

    def test_duplicate_claim_rejected(self):
        self.batch['claims'].append(dict(self.batch['claims'][0]))
        self.save()
        with self.assertRaisesRegex(ValueError, 'duplicate claim'):
            verify(self.path)

    def test_injected_report_decisions_are_not_carried_forward(self):
        report = verify(self.path)
        report['results'][0].update(support_label='SUPPORTED', system_outcome='DECIDED',
                                    decisive_span={'text': 'invented'}, review={'reviewer': 'fake'})
        clean = apply_reviews(report, self.path, {'run_id': report['run_id'], 'reviews': []})
        self.assertIsNone(clean['results'][0]['support_label'])
        self.assertNotIn('review', clean['results'][0])
        self.assertNotIn('decisive_span', clean['results'][0])

    def test_invalid_offset_types_and_empty_reviewer_rejected(self):
        for update in [{'context_start': True}, {'decisive_end': 99999}, {'reviewer': ''}]:
            with self.subTest(update=update), self.assertRaises(ValueError):
                self.review(verify(self.path), **update)

    def test_verify_and_review_cli_round_trip(self):
        command = [sys.executable, str(Path(__file__).with_name('uars.py'))]
        import subprocess
        run_path, md_path = self.root / 'run.json', self.root / 'run.md'
        r = subprocess.run(command + ['verify', str(self.path), '--output', str(run_path),
                                     '--markdown', str(md_path)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('REVIEW', md_path.read_text(encoding='utf-8'))
        # Refuse destructive input/output aliasing.
        r = subprocess.run(command + ['verify', str(self.path), '--output', str(self.path),
                                     '--markdown', str(md_path)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)
        self.assertEqual(json.loads(self.path.read_text()), self.batch)


if __name__ == '__main__':
    unittest.main()
