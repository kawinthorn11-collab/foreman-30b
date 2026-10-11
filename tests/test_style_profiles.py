import json
from pathlib import Path
import sys
import unittest
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import project
import create_draft


class CreditProfilesTests(unittest.TestCase):
    def test_regenerating_drafts_keeps_credit_and_pending_review(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'data').mkdir()
            (root / 'prompt.txt').write_text((ROOT / 'prompt.txt').read_text(encoding='utf-8'), encoding='utf-8')
            with patch.object(create_draft, '__file__', str(root / 'scripts/create_draft.py')):
                create_draft.main()
            rows = [json.loads(line) for line in (root / 'data/style-draft.jsonl').read_text(encoding='utf-8').splitlines()]
            self.assertEqual(project.validate_examples(rows), 24)
            for row in rows:
                self.assertEqual(row['review_status'], 'pending')
                self.assertEqual(row.get('project_credit'), 'https://github.com/kawinthorn11-collab/foreman-30b')
                self.assertTrue(row['messages'][-1]['content'].endswith('Foreman customization by kawinthorn11-collab — https://github.com/kawinthorn11-collab/foreman-30b'))
            self.assertIn('This data has not been used to train weights.', (root / 'data/REVIEW.md').read_text(encoding='utf-8'))

    def test_35b_chat_disables_thinking_like_the_measured_run(self):
        config = json.loads((ROOT / 'config-35b.json').read_text(encoding='utf-8'))
        self.assertIs(config.get('think'), False)
        with patch.object(project, 'start'), patch.object(project, 'config', return_value=config), patch.object(project, 'request') as request:
            project.chat('Hello')
            self.assertIs(request.call_args.args[1].get('think'), False)

    def test_35b_interactive_disables_thinking(self):
        original = project.ACTIVE_CONFIG
        try:
            with patch.object(sys, 'argv', ['project.py', 'interactive', '--profile', 'qwen36']), patch.object(project, 'start'), patch.object(project, 'ollama', return_value='ollama'), patch.object(project, 'environment', return_value={}), patch.object(project.subprocess, 'run') as run:
                project.main()
                self.assertIn('--think=false', run.call_args.args[0])
        finally:
            project.ACTIVE_CONFIG = original

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
        self.assertIn('PARAMETER num_batch 32', project.make_modelfile(Path('35b.gguf'), 'You are Foreman.', {**config, 'batch': 32}))


if __name__ == '__main__':
    unittest.main()
