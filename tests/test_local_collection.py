import copy
import json
from pathlib import Path
import sys
import unittest
import tempfile
import hashlib
import io
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import local_collection as collection


def entry(tag='qwen3:4b', digit='a'):
    return {'base_tag': tag, 'model_layer_digests': ['sha256:' + digit * 64],
            'total_download_bytes': 3000000000, 'license_source': 'https://ollama.com/library/qwen3'}


class LocalCollectionTests(unittest.TestCase):
    def test_progress_write_retries_transient_windows_sharing_and_bounds_persistent_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'progress.json'
            replace = collection.os.replace
            attempts = [0]
            def transient(source, target):
                attempts[0] += 1
                if attempts[0] == 1:
                    raise PermissionError('Transient Windows reader')
                replace(source, target)
            with (patch.object(collection.os, 'replace', side_effect=transient),
                  patch.object(collection.time, 'sleep')):
                collection.atomic_json(path, {'count': 15})
            self.assertEqual(json.loads(path.read_text()), {'count': 15})
            self.assertEqual(attempts[0], 2)
            with (patch.object(collection.os, 'replace', side_effect=PermissionError('Persistent lock')) as locked,
                  patch.object(collection.time, 'sleep')):
                with self.assertRaises(PermissionError):
                    collection.atomic_json(path, {'count': 16})
            self.assertLessEqual(locked.call_count, 8)
            self.assertEqual(json.loads(path.read_text()), {'count': 15})

    def test_stream_download_resumes_open_ended_range_and_checks_complete_blob(self):
        self.assertTrue(hasattr(collection, 'download_blob_stream'), 'Stream transport missing')
        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder) / 'verified-blob'
            payload = b'checked weights'
            digest = 'sha256:' + hashlib.sha256(payload).hexdigest()
            destination.with_name(destination.name + '.foreman-stream').write_bytes(payload[:4])
            class Reply(io.BytesIO):
                status = 206
                headers = {'Content-Range': 'bytes 4-14/15', 'Content-Length': '11'}
            with patch.object(collection.OPENER, 'open', return_value=Reply(payload[4:])) as opened:
                collection.download_blob_stream('https://registry.ollama.ai/blob', destination, digest, 15, {}, lambda: None)
            self.assertEqual(opened.call_args.args[0].get_header('Range'), 'bytes=4-')
            self.assertEqual(destination.read_bytes(), payload)

    def test_stream_download_restarts_if_resume_range_ignored_and_rejects_bad_sha(self):
        self.assertTrue(hasattr(collection, 'download_blob_stream'), 'Stream transport missing')
        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder) / 'verified-blob'
            payload = b'checked weights'
            partial = destination.with_name(destination.name + '.foreman-stream')
            partial.write_bytes(b'old')
            class Reply(io.BytesIO):
                status = 200
                headers = {'Content-Length': '15'}
            digest = 'sha256:' + hashlib.sha256(payload).hexdigest()
            with patch.object(collection.OPENER, 'open', return_value=Reply(payload)):
                collection.download_blob_stream('https://registry.ollama.ai/blob', destination, digest, 15, {}, lambda: None)
            self.assertEqual(destination.read_bytes(), payload)
            destination.unlink()
            with patch.object(collection.OPENER, 'open', return_value=Reply(payload)):
                with self.assertRaises(RuntimeError):
                    collection.download_blob_stream('https://registry.ollama.ai/blob', destination, 'sha256:' + '0' * 64, 15, {}, lambda: None)
            self.assertFalse(destination.exists())

    def test_stream_deadline_rejects_late_final_read_without_promoting(self):
        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder) / 'verified-blob'
            payload = b'checked weights'
            digest = 'sha256:' + hashlib.sha256(payload).hexdigest()
            clock = [0.0]
            class Reply(io.BytesIO):
                status = 200
                headers = {'Content-Length': '15'}
                def read1(self, size):
                    clock[0] = 2000.0
                    return super().read1(size)
            with (patch.object(collection.OPENER, 'open', return_value=Reply(payload)),
                  patch.object(collection.time, 'monotonic', side_effect=lambda: clock[0])):
                with self.assertRaises(TimeoutError):
                    collection.download_blob_stream('https://registry.ollama.ai/blob', destination, digest, 15, {}, lambda: None)
            self.assertFalse(destination.exists())

    def test_stream_trickling_data_switches_transport_and_retains_partial(self):
        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder) / 'verified-blob'
            # More than the old 1MiB/minute limit still leaves a multi-GB blob impractically slow.
            payload = b'x' * (2 * 1024 * 1024)
            digest = 'sha256:' + hashlib.sha256(payload).hexdigest()
            clock = [0.0]
            class Reply(io.BytesIO):
                status = 200
                headers = {'Content-Length': str(len(payload))}
                def read1(self, size):
                    clock[0] += 20.0
                    return super().read1(min(size, 512 * 1024))
            with (patch.object(collection.OPENER, 'open', return_value=Reply(payload)),
                  patch.object(collection.time, 'monotonic', side_effect=lambda: clock[0])):
                with self.assertRaises(TimeoutError):
                    collection.download_blob_stream('https://registry.ollama.ai/blob', destination, digest, len(payload), {}, lambda: None)
            self.assertFalse(destination.exists())
            self.assertEqual(destination.with_name(destination.name + '.foreman-stream').read_bytes(), payload[:1536 * 1024])

    def test_direct_download_resumes_verified_size_parts_and_verifies_final_blob(self):
        with tempfile.TemporaryDirectory() as folder:
            cache = Path(folder)
            payload = b'x' * 1048576 + b'last segment'
            digest = 'sha256:' + hashlib.sha256(payload).hexdigest()
            destination = cache / 'blobs' / digest.replace(':', '-')
            parts = destination.with_name(destination.name + '.foreman-parts-1048576')
            parts.mkdir(parents=True)
            (parts / '00000.part').write_bytes(payload[:1048576])
            partial = destination.with_name(destination.name + '.foreman-stream')
            partial.write_bytes(payload[:-1])
            item = {**entry(), 'layers': [{'mediaType': 'application/vnd.ollama.image.model',
                                         'digest': digest, 'size': len(payload)}]}
            def fetch(url, path, start, end, total):
                self.assertEqual(total, len(payload))
                path.write_bytes(payload[start:end + 1])
            with (patch.object(collection, 'download_blob_stream', side_effect=OSError('Use range fallback'), create=True),
                  patch.object(collection, 'download_range', side_effect=fetch) as download):
                collection.prefetch_blobs(cache, item, {}, lambda: None)
            self.assertEqual(download.call_count, 1)
            self.assertEqual(destination.read_bytes(), payload)
            self.assertFalse(parts.exists())
            self.assertFalse(partial.exists())

    def test_manifest_list_preserves_original_identity_and_checks_child_digest(self):
        with tempfile.TemporaryDirectory() as folder:
            cache = Path(folder)
            profile = cache / 'manifests-v2/ollama.com/library/foreman-qwen3-4b/latest'
            profile.parent.mkdir(parents=True)
            document = {'config': {'digest': 'sha256:' + 'c' * 64}, 'layers': [
                {'mediaType': 'application/vnd.ollama.image.model', 'digest': 'sha256:' + 'a' * 64, 'size': 123},
                {'mediaType': 'application/vnd.ollama.image.system', 'digest': 'sha256:' + 'd' * 64, 'size': 12}]}
            profile.write_text(json.dumps(document))
            self.assertTrue(hasattr(collection, 'profile_identity'), 'Stable profile identity missing')
            identity = collection.profile_identity(cache, 'foreman-qwen3-4b:latest')
            payload = json.dumps({**document, 'runner': 'ggml', 'format': 'gguf'}).encode()
            digest = 'sha256:' + hashlib.sha256(payload).hexdigest()
            blob = cache / 'blobs' / digest.replace(':', '-')
            blob.parent.mkdir()
            blob.write_bytes(payload)
            profile.write_text(json.dumps({'manifests': [{'digest': digest, 'runner': 'ggml'}]}))
            row = {**entry(), 'profile': 'foreman-qwen3-4b:latest', 'profile_identity_sha256': identity}
            self.assertEqual(collection.installed_fingerprint(cache, row['profile']), tuple(row['model_layer_digests']))
            self.assertTrue(collection.profile_matches(cache, row))
            blob.write_bytes(payload + b' ')
            self.assertFalse(collection.profile_matches(cache, row))

    def test_resume_detects_replaced_profile_even_when_original_base_is_unchanged(self):
        self.assertTrue(hasattr(collection, 'profile_matches'), 'Profile resume verification missing')
        with tempfile.TemporaryDirectory() as folder:
            cache = Path(folder)
            base = cache / 'manifests/registry.ollama.ai/library/qwen3/4b'
            profile = cache / 'manifests-v2/ollama.com/library/foreman-qwen3-4b/latest'
            for path, digit in [(base, 'a'), (profile, 'b')]:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps({'layers': [{'mediaType': 'application/vnd.ollama.image.model', 'digest': 'sha256:' + digit * 64}]}))
            row = {**entry(), 'profile': 'foreman-qwen3-4b:latest'}
            self.assertFalse(collection.profile_matches(cache, row))
            profile.write_text(base.read_text())
            self.assertTrue(collection.profile_matches(cache, row))

    def test_range_download_rejects_ignored_or_wrong_range(self):
        self.assertTrue(hasattr(collection, 'download_range'), 'Bounded range transport missing')
        class Reply(io.BytesIO):
            status = 206
            headers = {'Content-Range': 'bytes 0-2/6'}
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'part'
            with patch.object(collection.OPENER, 'open', return_value=Reply(b'abc')):
                collection.download_range('https://registry.ollama.ai/blob', path, 0, 2, 6)
            self.assertEqual(path.read_bytes(), b'abc')
            reply = Reply(b'abcdef')
            reply.status = 200
            with patch.object(collection.OPENER, 'open', return_value=reply):
                with self.assertRaises(ValueError):
                    collection.download_range('https://registry.ollama.ai/blob', path, 0, 2, 6)

    def test_direct_blob_promotion_requires_size_and_sha256(self):
        self.assertTrue(hasattr(collection, 'verify_blob'), 'Blob checksum verifier missing')
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'blob'
            path.write_bytes(b'checked weights')
            digest = 'sha256:' + hashlib.sha256(b'checked weights').hexdigest()
            self.assertTrue(collection.verify_blob(path, digest, 15))
            self.assertFalse(collection.verify_blob(path, digest, 16))
            self.assertFalse(collection.verify_blob(path, 'sha256:' + '0' * 64, 15))

    def test_rejects_duplicate_weights_and_invalid_names(self):
        self.assertTrue(hasattr(collection, 'validate_registry'), 'Registry validator missing')
        collection.validate_registry({'models': [entry(), entry('phi4-mini:latest', 'b')]}, expected=2)
        for bad in [entry('alias:latest'), entry('../private:key', 'c')]:
            with self.assertRaises(ValueError):
                collection.validate_registry({'models': [entry(), bad]}, expected=2)

    def test_rejects_count_digest_size_and_unverified_license(self):
        self.assertTrue(hasattr(collection, 'validate_registry'), 'Registry validator missing')
        for change in [{'model_layer_digests': []}, {'model_layer_digests': ['bad']},
                       {'total_download_bytes': -1}, {'license_source': ''}]:
            bad = entry()
            bad.update(change)
            with self.assertRaises(ValueError):
                collection.validate_registry({'models': [bad]}, expected=1)

    def test_generated_code_is_verified_without_allowing_calls_or_imports(self):
        self.assertTrue(hasattr(collection, 'check_code'), 'Safe code checker missing')
        good = '```python\ndef is_even(n):\n    return n % 2 == 0\n```'
        self.assertTrue(collection.check_code(good)['passed'])
        for bad in ['def is_even(n):\n return True',
                    'import os\ndef is_even(n):\n return n % 2 == 0',
                    'def is_even(n):\n return __import__("os").system("echo unsafe")',
                    '@evil\ndef is_even(n):\n return n % 2 == 0',
                    'def is_even(n):\n while True: pass']:
            self.assertFalse(collection.check_code('```python\n' + bad + '\n```')['passed'])

    def test_only_successful_distinct_profiles_are_exported(self):
        self.assertTrue(hasattr(collection, 'usable_entries'), 'Verified export missing')
        a = {**entry(), 'profile': 'foreman-qwen3-4b:local', 'status': 'passed', 'response': 'hello'}
        failed = {**entry('phi4-mini:latest', 'b'), 'profile': 'foreman-phi4-mini:local', 'status': 'failed'}
        self.assertEqual(collection.usable_entries([a, failed]), [a])
        with self.assertRaises(ValueError):
            collection.usable_entries([a, copy.deepcopy(a)])

    def test_bounded_profile_has_credit_and_does_not_train(self):
        self.assertTrue(hasattr(collection, 'profile_text'), 'Bounded profile missing')
        text = collection.profile_text('qwen3:4b', 'Foreman credit.', 2048, 512)
        self.assertIn('FROM qwen3:4b\n', text)
        self.assertIn('num_ctx 2048', text)
        self.assertIn('num_batch 64', text)
        for context, output in [(65536, 512), (2048, 4096), (-1, 512)]:
            with self.assertRaises(ValueError):
                collection.profile_text('qwen3:4b', 'Foreman credit.', context, output)


if __name__ == '__main__':
    unittest.main()
