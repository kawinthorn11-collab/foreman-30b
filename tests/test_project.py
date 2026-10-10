import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from project import validate_examples, make_modelfile, check_config
import project


class ProjectTests(unittest.TestCase):
    def test_foreign_server_is_rejected_before_import(self):
        with patch.object(project, 'request', return_value={'version': '0.40.2'}), patch.object(project, 'owns_server', return_value=False, create=True):
            with self.assertRaisesRegex(RuntimeError, 'not owned'):
                project.start()

    def test_loopback_request_explicitly_disables_proxy(self):
        with patch.object(project.urllib.request, 'ProxyHandler', wraps=project.urllib.request.ProxyHandler) as handler:
            with patch.object(project.urllib.request, 'build_opener') as opener:
                opener.return_value.open.return_value.__enter__.return_value.read.return_value = b'{}'
                project.request('/api/version')
            handler.assert_called_once_with({})

    def test_training_examples_reject_assistant_without_user(self):
        with self.assertRaises(ValueError):
            validate_examples([{'messages': [{'role': 'assistant', 'content': 'Hello'}]}])

    def test_credentials_are_not_accepted_as_training_text(self):
        with self.assertRaises(ValueError):
            validate_examples([{'messages': [{'role': 'user', 'content': 'key'},
                {'role': 'assistant', 'content': 'Authorization: Bearer hn_' + 'a' * 43}]}])

    def test_duplicates_are_rejected(self):
        sample = {'messages': [{'role': 'user', 'content': 'Who are you?'},
                               {'role': 'assistant', 'content': 'I am Foreman.'}]}
        with self.assertRaises(ValueError):
            validate_examples([sample, sample])

    def test_modelfile_pins_memory_and_uses_actual_prompt(self):
        config = {'context': 2048, 'threads': 4, 'gpu_layers': 28, 'max_output': 512}
        text = make_modelfile(Path('model.gguf'), 'You are Foreman.', config)
        self.assertIn('PARAMETER num_ctx 2048', text)
        self.assertIn('PARAMETER num_gpu 28', text)
        self.assertIn('You are Foreman.', text)

    def test_unbounded_context_is_rejected(self):
        with self.assertRaises(ValueError):
            check_config({'context': 65536, 'gpu_layers': 28, 'max_output': 512})


if __name__ == '__main__':
    unittest.main()
