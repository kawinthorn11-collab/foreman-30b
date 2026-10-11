import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import project


class CreditProfilesTests(unittest.TestCase):
    def test_credit_policy_preserves_upstream_and_tool_calls(self):
        prompt = (ROOT / 'prompt.txt').read_text(encoding='utf-8')
        self.assertIn('https://github.com/kawinthorn11-collab/foreman-30b', prompt)
        self.assertIn('upstream', prompt.lower())
        self.assertIn('tool-call', prompt.lower())

    def test_every_draft_answer_teaches_the_credit(self):
        rows = [json.loads(line) for line in (ROOT / 'data/style-draft.jsonl').read_text(encoding='utf-8').splitlines()]
        project.validate_examples(rows)
        for row in rows:
            self.assertEqual(row['review_status'], 'pending')
            for message in row['messages']:
                if message['role'] == 'assistant':
                    self.assertTrue(message['content'].endswith('Foreman customization by kawinthorn11-collab — https://github.com/kawinthorn11-collab/foreman-30b'))

    def test_profile_accepts_only_single_line_real_base_name(self):
        self.assertTrue(hasattr(project, 'make_installed_profile'), 'installed-base profile generator is missing')
        make = project.make_installed_profile
        result = make('qwen3.5:4b-q4_K_M', 'You are Foreman.', 65536, 2048)
        self.assertIn('FROM qwen3.5:4b-q4_K_M\n', result)
        self.assertIn('PARAMETER num_ctx 65536', result)
        for base in ['', 'fake\nSYSTEM hacked', '../secrets/key', 'x"y']:
            with self.assertRaises(ValueError):
                make(base, 'You are Foreman.', 2048, 512)

    def test_new_large_model_has_a_pinned_bounded_profile(self):
        self.assertTrue((ROOT / 'config-35b.json').exists(), 'Pinned 35B profile is missing')
        config = json.loads((ROOT / 'config-35b.json').read_text(encoding='utf-8'))
        project.check_config(config)
        self.assertEqual(config['context'], 2048)
        self.assertEqual(config['model'], 'foreman-35b:latest')
        self.assertEqual(config['bytes'], 10756586464)
        self.assertEqual(len(config['sha256']), 64)


if __name__ == '__main__':
    unittest.main()
