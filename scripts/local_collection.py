"""Install distinct small local Foreman models and record real smoke results."""
import argparse
import ast
import ctypes
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import threading
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
NAME = re.compile(r'[a-zA-Z0-9][a-zA-Z0-9_.-]*:[a-zA-Z0-9][a-zA-Z0-9_.-]*\Z')
DIGEST = re.compile(r'sha256:[0-9a-f]{64}\Z')
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))
CREDIT_URL = 'https://github.com/kawinthorn11-collab/foreman-30b'
SMOKE_PROMPT = ('Reply in English. Write only a Python code block defining is_even(n) '
                'that returns a boolean, followed by your full Foreman GitHub project credit. '
                'No imports, annotations, examples or extra explanation. Keep it under 100 words.')


def fingerprint(item):
    return tuple(sorted(item['model_layer_digests']))


def validate_registry(registry, expected=50):
    items = registry['models']
    if len(items) != expected:
        raise ValueError(f'Expected {expected} models; got {len(items)}')
    seen = set()
    names = set()
    for item in items:
        tag = item['base_tag']
        digests = item['model_layer_digests']
        if not NAME.fullmatch(tag) or '..' in tag:
            raise ValueError('Unsafe model tag')
        if not digests or any(not DIGEST.fullmatch(d) for d in digests):
            raise ValueError('Invalid weight digests')
        key = fingerprint(item)
        if key in seen or tag in names:
            raise ValueError('Duplicate weight set or model tag')
        if not isinstance(item['total_download_bytes'], int) or not 0 < item['total_download_bytes'] <= 8 * 1024**3:
            raise ValueError('Unexpected small-model size')
        if not str(item.get('license_source', '')).startswith('https://'):
            raise ValueError('Missing license attribution')
        seen.add(key)
        names.add(tag)
    return items


def profile_name(tag):
    if not NAME.fullmatch(tag) or '..' in tag:
        raise ValueError('Unsafe model tag')
    return 'foreman-' + tag.replace(':', '-') + ':latest'


def profile_text(tag, prompt, context=2048, output=512):
    if not NAME.fullmatch(tag) or '..' in tag or not prompt or '"""' in prompt:
        raise ValueError('Unsafe profile input')
    if not 512 <= context <= 8192 or not 64 <= output <= min(context, 2048):
        raise ValueError('Collection budgets exceed safe limits')
    return (f'FROM {tag}\nSYSTEM """{prompt.strip()}"""\n'
            f'PARAMETER num_ctx {context}\nPARAMETER num_predict {output}\n'
            'PARAMETER num_thread 4\nPARAMETER num_batch 64\nPARAMETER temperature 0.2\n')


def check_code(text):
    """Execute only a small, validated arithmetic function with no builtins or calls."""
    block = re.search(r'```(?:python|py)?\s*\n(.*?)```', text, re.S)
    if not block:
        return {'passed': False, 'reason': 'No fenced Python function'}
    try:
        tree = ast.parse(block.group(1).strip())
        allowed = (ast.Module, ast.FunctionDef, ast.arguments, ast.arg, ast.Return,
                   ast.Compare, ast.BinOp, ast.Mod, ast.Constant, ast.Name, ast.Eq,
                   ast.NotEq, ast.Load, ast.UnaryOp, ast.USub)
        if any(not isinstance(node, allowed) for node in ast.walk(tree)):
            raise ValueError('Code exceeds the arithmetic-only AST allowlist')
        if len(tree.body) != 1 or not isinstance(tree.body[0], ast.FunctionDef):
            raise ValueError('Expected one function')
        fn = tree.body[0]
        args = fn.args
        if (fn.name != 'is_even' or len(args.args) != 1 or args.args[0].arg != 'n'
                or args.posonlyargs or args.kwonlyargs or args.vararg or args.kwarg
                or args.defaults or fn.decorator_list or fn.returns
                or len(fn.body) != 1 or not isinstance(fn.body[0], ast.Return)):
            raise ValueError('Unexpected function signature or body')
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id != 'n':
                raise ValueError('Unexpected variable')
            if isinstance(node, ast.Constant) and (type(node.value) not in (int, bool) or abs(node.value) > 10000):
                raise ValueError('Unexpected literal')
        namespace = {'__builtins__': {}}
        exec(compile(tree, '<validated-smoke>', 'exec'), namespace)
        for n in [-4, -3, 0, 1, 2, 1024]:
            result = namespace['is_even'](n)
            if type(result) is not bool or result != (n % 2 == 0):
                return {'passed': False, 'reason': f'Incorrect result for {n}'}
        return {'passed': True, 'cases': 6, 'code': block.group(1).strip()}
    except (SyntaxError, ValueError, TypeError, ZeroDivisionError) as exc:
        return {'passed': False, 'reason': str(exc)}


def usable_entries(items):
    usable = [item for item in items if item.get('status') == 'passed' and item.get('response', '').strip()]
    if len({fingerprint(item) for item in usable}) != len(usable):
        raise ValueError('Duplicate verified weights')
    return usable


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    # Windows readers may briefly deny replacement. Keep the previous complete
    # state visible and retry for a bounded interval rather than failing a model.
    for attempt in range(8):
        try:
            os.replace(temporary, path)
            break
        except PermissionError:
            if attempt == 7:
                raise
            time.sleep(min(0.01 * 2**attempt, 0.25))


def request(host, route, body=None, timeout=30):
    data = None if body is None else json.dumps(body).encode('utf-8')
    req = urllib.request.Request(host + route, data=data, headers={'Content-Type': 'application/json'})
    with OPENER.open(req, timeout=timeout) as response:
        return json.load(response)


def manifest_path(cache, tag):
    if not NAME.fullmatch(tag) or '..' in tag:
        raise ValueError('Unsafe manifest name')
    name, version = tag.split(':')
    for root in ('manifests-v2/ollama.com/library', 'manifests-v2/registry.ollama.ai/library',
                 'manifests/registry.ollama.ai/library'):
        path = cache / root / name / version
        if path.is_file():
            return path
    raise FileNotFoundError(f'Installed manifest is missing: {tag}')


def manifest_document(cache, tag):
    path = manifest_path(cache, tag)
    data = json.loads(path.read_text(encoding='utf-8'))
    if 'manifests' in data:
        # Ollama can split multimodal GGUFs on first use and wrap the original
        # ggml manifest plus a converted llamacpp variant in a local index.
        choices = [item for item in data['manifests'] if item.get('runner') == 'ggml']
        if not choices and len(data['manifests']) == 1:
            choices = data['manifests']
        if len(choices) != 1 or not DIGEST.fullmatch(choices[0].get('digest', '')):
            raise ValueError('Ambiguous or invalid local manifest list')
        digest = choices[0]['digest']
        blob = cache / 'blobs' / digest.replace(':', '-')
        if blob.stat().st_size > 4 * 1024**2:
            raise ValueError('Unexpected manifest size')
        payload = blob.read_bytes()
        if hashlib.sha256(payload).hexdigest() != digest.split(':')[1]:
            raise ValueError('Local child manifest failed SHA256 verification')
        data = json.loads(payload)
    if not isinstance(data.get('layers'), list):
        raise ValueError('Missing installed manifest layers')
    return data


def installed_fingerprint(cache, tag):
    data = manifest_document(cache, tag)
    result = tuple(sorted(layer['digest'] for layer in data['layers']
                          if layer['mediaType'] == 'application/vnd.ollama.image.model'))
    if not result or any(not DIGEST.fullmatch(digest) for digest in result):
        raise ValueError('Invalid installed weight digest')
    return result


def manifest_digest(cache, tag):
    return hashlib.sha256(manifest_path(cache, tag).read_bytes()).hexdigest()


def profile_identity(cache, tag):
    data = manifest_document(cache, tag)
    # Source labels and runner/index metadata may change during conversion;
    # weight, template, license, system and parameter content must not change.
    identity = {'config': data.get('config', {}).get('digest'),
                'layers': [(layer['mediaType'], layer['digest'], layer.get('size'))
                           for layer in data['layers']]}
    return hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()


def profile_matches(cache, row):
    try:
        if installed_fingerprint(cache, row['profile']) != fingerprint(row):
            return False
        if row.get('profile_identity_sha256'):
            return profile_identity(cache, row['profile']) == row['profile_identity_sha256']
        previous = row.get('profile_manifest_sha256')
        return not previous or previous == manifest_digest(cache, row['profile'])
    except (OSError, ValueError, KeyError):
        return False


def verify_blob(path, digest, size):
    if not DIGEST.fullmatch(digest) or not path.is_file() or path.stat().st_size != size:
        return False
    checksum = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(16 * 1024 * 1024), b''):
            checksum.update(block)
    return checksum.hexdigest() == digest.split(':')[1]


def download_range(url, path, start, end, total):
    req = urllib.request.Request(url, headers={'Range': f'bytes={start}-{end}'})
    with OPENER.open(req, timeout=12) as response:
        if response.status != 206 or response.headers.get('Content-Range') != f'bytes {start}-{end}/{total}':
            raise ValueError('Registry did not honor the exact requested range')
        received = 0
        started = time.monotonic()
        with path.open('wb') as stream:
            while received < end - start + 1:
                if time.monotonic() - started > 20:
                    raise TimeoutError('Range transfer exceeded its bounded time budget')
                block = response.read(min(128 * 1024, end - start + 1 - received))
                if not block:
                    raise OSError('Incomplete range')
                stream.write(block)
                received += len(block)
        if response.read(1):
            raise ValueError('Oversized range')


def download_blob_stream(url, destination, digest, size, progress, save):
    """Resume an official blob stream; promote only exact-size, SHA-verified data."""
    if not DIGEST.fullmatch(digest) or not isinstance(size, int) or not 0 < size <= 8 * 1024**3:
        raise ValueError('Unexpected registry blob')
    temporary = destination.with_name(destination.name + '.foreman-stream')
    if temporary.is_symlink():
        raise ValueError('Unsafe stream temporary file')
    offset = temporary.stat().st_size if temporary.exists() else 0
    if offset == size and verify_blob(temporary, digest, size):
        os.replace(temporary, destination)
        return
    if offset >= size:
        offset = 0
    headers = {'Range': f'bytes={offset}-'} if offset else {}
    req = urllib.request.Request(url, headers=headers)
    progress['stage'] = 'verified-stream-download'
    progress['download'] = {'status': 'resumable blob stream', 'digest': digest, 'total': size, 'completed': offset}
    save()
    began = last = time.monotonic()
    with OPENER.open(req, timeout=12) as response:
        if response.status == 206:
            if response.headers.get('Content-Range') != f'bytes {offset}-{size - 1}/{size}':
                raise ValueError('Registry did not honor the open-ended resume range')
        elif response.status == 200:
            offset = 0
        else:
            raise ValueError('Unexpected blob stream response')
        length = response.headers.get('Content-Length')
        if length is not None and int(length) != size - offset:
            raise ValueError('Unexpected blob stream length')
        window_started, window_offset = time.monotonic(), offset
        with temporary.open('ab' if offset else 'wb') as stream:
            while offset < size:
                if time.monotonic() - began > 1800:
                    raise TimeoutError('Blob stream exceeded its time budget; partial retained')
                block = response.read1(min(1024 * 1024, size - offset))
                if not block:
                    raise OSError('Incomplete blob stream; partial retained')
                stream.write(block)
                offset += len(block)
                now = time.monotonic()
                if now - began > 1800:
                    raise TimeoutError('Blob stream exceeded its time budget; partial retained')
                if now - window_started >= 60:
                    if offset < size and offset - window_offset < 64 * 1024 * 1024:
                        raise TimeoutError('Blob stream below 64MiB/minute; switch transport, partial retained')
                    window_started, window_offset = now, offset
                if time.monotonic() - last >= 1:
                    progress['download']['completed'] = offset
                    save()
                    last = time.monotonic()
            if response.read1(1):
                raise ValueError('Oversized blob stream')
            if time.monotonic() - began > 1800:
                raise TimeoutError('Blob stream exceeded its time budget; partial retained')
    progress['stage'] = 'checksum'
    progress['download']['completed'] = offset
    save()
    if not verify_blob(temporary, digest, size):
        raise RuntimeError('Streamed blob failed SHA256/size verification; not imported')
    os.replace(temporary, destination)


def prefetch_blobs(cache, item, progress, save):
    """Official-registry transport fallback; never import an unverified download."""
    family = item['base_tag'].split(':')[0]
    for layer in item.get('layers', []):
        if layer.get('mediaType') not in ('application/vnd.ollama.image.model',
                                         'application/vnd.ollama.image.projector',
                                         'application/vnd.ollama.image.draft'):
            continue
        digest, size = layer['digest'], layer['size']
        if not DIGEST.fullmatch(digest) or not isinstance(size, int) or not 0 < size <= 8 * 1024**3:
            raise ValueError('Unexpected registry blob')
        destination = cache / 'blobs' / digest.replace(':', '-')
        # The following /api/pull also checks the cached model; existing old blobs are preserved.
        if destination.exists() and destination.stat().st_size == size:
            continue
        temporary = destination.with_name(destination.name + '.foreman-assembled')
        url = f'https://registry.ollama.ai/v2/library/{family}/blobs/{digest}'
        try:
            download_blob_stream(url, destination, digest, size, progress, save)
            continue
        except (OSError, ValueError, RuntimeError) as exc:
            progress['stream_error'] = str(exc)[:300]
            save()
        chunk = 1024 * 1024
        parts = destination.with_name(destination.name + f'.foreman-parts-{chunk}')
        parts.mkdir(exist_ok=True)
        if parts.resolve().parent != (cache / 'blobs').resolve() or parts.is_symlink():
            raise ValueError('Unsafe temporary download directory')
        specifications = [(index, start, min(start + chunk - 1, size - 1))
                          for index, start in enumerate(range(0, size, chunk))]
        progress['stage'] = 'verified-direct-download'
        progress['download'] = {'status': 'starting resumable ranges', 'digest': digest, 'total': size}
        save()
        def part_path(index):
            return parts / f'{index:05d}.part'
        missing = [(index, start, end) for index, start, end in specifications
                   if not part_path(index).is_file() or part_path(index).stat().st_size != end - start + 1]
        completed = size - sum(end - start + 1 for _, start, end in missing)
        def fetch(spec):
            index, start, end = spec
            for attempt in range(3):
                try:
                    if attempt == 0:
                        download_range(url, part_path(index), start, end, size)
                    elif attempt == 1:
                        # The registry honors this alternate cache key with the
                        # same exact byte range; range and final SHA checks stay mandatory.
                        download_range(url + '?download=1', part_path(index), start, end, size)
                    else:
                        # A few CDN range keys stall. Repartition their intervals rather
                        # than requesting the same slow connection/range indefinitely.
                        width = max(1, (end - start + 1) // (4 * attempt))
                        pieces = []
                        for subindex, substart in enumerate(range(start, end + 1, width)):
                            subend = min(substart + width - 1, end)
                            piece = parts / f'{index:05d}-{attempt}-{subindex}.segment'
                            if not piece.exists() or piece.stat().st_size != subend - substart + 1:
                                download_range(url + '?download=1', piece, substart, subend, size)
                            pieces.append(piece)
                        with part_path(index).open('wb') as combined:
                            for piece in pieces:
                                with piece.open('rb') as source:
                                    shutil.copyfileobj(source, combined, length=128 * 1024)
                        for piece in pieces:
                            piece.unlink()
                    return end - start + 1
                except (OSError, ValueError):
                    if attempt == 2:
                        raise
        with ThreadPoolExecutor(max_workers=8) as pool:
            jobs = [pool.submit(fetch, spec) for spec in missing]
            try:
                for future in as_completed(jobs):
                    completed += future.result()
                    progress['download'] = {'status': 'verified-range transport', 'digest': digest,
                                            'total': size, 'completed': completed}
                    save()
            except (OSError, ValueError):
                # Cancel queued ranges so one failed interval does not silently
                # wait for thousands of unrelated queued downloads before retry.
                for job in jobs:
                    job.cancel()
                raise
        progress['stage'] = 'assemble'
        save()
        with temporary.open('wb') as stream:
            for index, _, _ in specifications:
                with part_path(index).open('rb') as source:
                    shutil.copyfileobj(source, stream, length=1024 * 1024)
        progress['stage'] = 'checksum'
        save()
        if not verify_blob(temporary, digest, size):
            raise RuntimeError('Downloaded blob failed SHA256/size verification; not imported')
        os.replace(temporary, destination)
        stream_partial = destination.with_name(destination.name + '.foreman-stream')
        if stream_partial.is_file() and not stream_partial.is_symlink():
            stream_partial.unlink()
        # Remove only our enumerated temporary segments after the verified final blob exists.
        for index, _, _ in specifications:
            part_path(index).unlink()
        # Failed earlier attempts may leave only disposable segment files here.
        for segment in parts.glob('*.segment'):
            if segment.is_file() and not segment.is_symlink():
                segment.unlink()
        parts.rmdir()
    progress['stage'] = 'pull'
    save()


class MemorySampler:
    class Status(ctypes.Structure):
        _fields_ = [('length', ctypes.c_ulong), ('load', ctypes.c_ulong),
                    ('total_phys', ctypes.c_ulonglong), ('avail_phys', ctypes.c_ulonglong),
                    ('total_page', ctypes.c_ulonglong), ('avail_page', ctypes.c_ulonglong),
                    ('total_virtual', ctypes.c_ulonglong), ('avail_virtual', ctypes.c_ulonglong),
                    ('avail_extended', ctypes.c_ulonglong)]

    def __init__(self):
        self.samples = []
        self.stop = threading.Event()

    def run(self):
        if os.name != 'nt':
            return
        while not self.stop.is_set():
            status = self.Status()
            status.length = ctypes.sizeof(status)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
                self.samples.append(status.avail_phys)
            self.stop.wait(1)

    def __enter__(self):
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()
        return self

    def __exit__(self, *args):
        self.stop.set()
        self.thread.join(2)


def unload(host):
    for model in request(host, '/api/ps').get('models', []):
        request(host, '/api/generate', {'model': model['name'], 'keep_alive': 0}, timeout=60)


def pull(host, item, progress, save):
    req = urllib.request.Request(host + '/api/pull',
                                 data=json.dumps({'model': item['base_tag'], 'stream': True}).encode(),
                                 headers={'Content-Type': 'application/json'})
    last = 0
    with OPENER.open(req, timeout=180) as response:
        for line in response:
            row = json.loads(line)
            if row.get('error'):
                raise RuntimeError(row['error'])
            if time.monotonic() - last > 2 or row.get('status') == 'success':
                progress['download'] = {k: row[k] for k in ('status', 'digest', 'total', 'completed') if k in row}
                save()
                last = time.monotonic()


def smoke(host, name, context, output):
    start = time.monotonic()
    with MemorySampler() as memory:
        result = request(host, '/api/chat', {'model': name, 'stream': False, 'think': False,
                          'messages': [{'role': 'user', 'content': SMOKE_PROMPT}], 'keep_alive': 0,
                          'options': {'num_ctx': context, 'num_predict': output, 'num_thread': 4,
                                      'num_batch': 64, 'temperature': 0.2}}, timeout=600)
    text = result.get('message', {}).get('content', '').strip()
    if not text:
        raise RuntimeError('Model returned no visible answer within the output budget')
    duration = result.get('eval_duration', 0)
    return {'status': 'passed', 'response': text, 'elapsed_seconds': round(time.monotonic() - start, 2),
            'eval_tokens': result.get('eval_count', 0),
            'tokens_per_second': round(result.get('eval_count', 0) * 1e9 / duration, 2) if duration else None,
            'credit_passed': CREDIT_URL in text and 'kawinthorn11-collab' in text,
            'coding_check': check_code(text),
            'minimum_available_ram_bytes': min(memory.samples) if memory.samples else None,
            'load_duration_seconds': round(result.get('load_duration', 0) / 1e9, 2),
            'context': context, 'response_tokens': output,
            'tested_at_utc': datetime.now(timezone.utc).isoformat()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registry', type=Path, default=ROOT / 'local50-models.json')
    parser.add_argument('--cache', type=Path, required=True, help='Actual OLLAMA_MODELS directory, used for disk/digest checks')
    parser.add_argument('--ollama', type=Path, required=True)
    parser.add_argument('--port', type=int, default=11434)
    parser.add_argument('--context', type=int, default=2048)
    parser.add_argument('--output', type=int, default=512)
    parser.add_argument('--target', type=int, default=50)
    parser.add_argument('--skip-failed', action='store_true', help='Use reserves instead of retrying recorded failures during this resume')
    parser.add_argument('--direct-download', action='store_true', help='Use bounded HTTP ranges with SHA256 verification for large registry layers')
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535 or not args.ollama.is_file() or not args.cache.is_dir():
        parser.error('Existing Ollama executable/cache and a loopback port are required')
    registry = json.loads(args.registry.read_text(encoding='utf-8'))
    candidates = validate_registry(registry, expected=50)
    reserves = registry.get('reserves', [])
    if reserves:
        validate_registry({'models': candidates + reserves}, expected=50 + len(reserves))
    if not 1 <= args.target <= 50:
        parser.error('Target must be 1..50')
    prompt = (ROOT / 'prompt.txt').read_text(encoding='utf-8')
    profile_text(candidates[0]['base_tag'], prompt, args.context, args.output)
    folder = ROOT / 'collection-local'
    folder.mkdir(exist_ok=True)
    lock = folder / 'installer.lock'
    # O_EXCL prevents simultaneous installers/inference. Remove a stale lock only after confirming its PID is gone.
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    os.write(fd, str(os.getpid()).encode())
    os.close(fd)
    state_path = folder / 'progress.json'
    state = json.loads(state_path.read_text(encoding='utf-8')) if state_path.exists() else {'results': []}
    state.update(status='running', cache=str(args.cache.resolve()), target=args.target)
    save = lambda: atomic_json(state_path, state)
    host = f'http://127.0.0.1:{args.port}'
    env = dict(os.environ, OLLAMA_HOST=host)
    try:
        request(host, '/api/version')
        unload(host)
        # Revalidate resumed passes against the currently installed weight manifest and profile list.
        installed = {row['name'] for row in request(host, '/api/tags')['models']}
        for row in state['results']:
            if row.get('status') == 'passed':
                try:
                    if row['profile'] not in installed or not profile_matches(args.cache, row):
                        row['status'] = 'stale'
                except (OSError, ValueError, KeyError):
                    row['status'] = 'stale'
        for item in candidates + reserves:
            good = usable_entries(state['results'])
            state['verified_count'] = len(good)
            if len(good) >= args.target:
                break
            if any(fingerprint(row) == fingerprint(item) and row['status'] == 'passed' for row in good):
                continue
            if args.skip_failed and any(row['base_tag'] == item['base_tag'] and row['status'] == 'failed' for row in state['results']):
                continue
            state.update(current_model=item['base_tag'], stage='pull', download={})
            save()
            print(f'[{len(good)}/{args.target}] {item["base_tag"]}: download', flush=True)
            result = {**item, 'profile': profile_name(item['base_tag']), 'status': 'failed'}
            try:
                if shutil.disk_usage(args.cache).free < item['total_download_bytes'] * 3 + 20 * 1024**3:
                    raise RuntimeError('Disk reserve below 20GiB plus model download; stopped')
                for attempt in range(2):
                    try:
                        if args.direct_download:
                            prefetch_blobs(args.cache, item, state, save)
                        pull(host, item, state, save)
                        break
                    except (OSError, RuntimeError):
                        if attempt == 1:
                            raise
                if installed_fingerprint(args.cache, item['base_tag']) != fingerprint(item):
                    raise RuntimeError('Registry tag weights changed from the reviewed manifest; not counted')
                state['stage'] = 'profile'
                save()
                path = folder / (result['profile'].replace(':', '_') + '.Modelfile')
                path.write_text(profile_text(item['base_tag'], prompt, args.context, args.output), encoding='utf-8')
                run = subprocess.run([str(args.ollama.resolve()), 'create', result['profile'], '-f', str(path)],
                                     env=env, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=120)
                if run.returncode:
                    raise RuntimeError('Profile create failed: ' + run.stderr[-1000:])
                if not profile_matches(args.cache, result):
                    raise RuntimeError('Created profile weights do not match the reviewed base')
                result['profile_identity_sha256'] = profile_identity(args.cache, result['profile'])
                state['stage'] = 'inference'
                save()
                result['capabilities'] = request(host, '/api/show', {'model': result['profile']}).get('capabilities', [])
                result.update(smoke(host, result['profile'], args.context, args.output))
                if not profile_matches(args.cache, result):
                    raise RuntimeError('Profile content changed during inference; not counted')
                result['profile_manifest_sha256'] = manifest_digest(args.cache, result['profile'])
                print(f'PASS {result["profile"]}: {result["elapsed_seconds"]}s, code={result["coding_check"]["passed"]}, credit={result["credit_passed"]}', flush=True)
            except Exception as exc:
                result['status'] = 'failed'
                result['error'] = str(exc)[:1200]
                print(f'FAILED {item["base_tag"]}: {result["error"]}', flush=True)
            finally:
                try:
                    unload(host)
                except Exception as exc:
                    state['unload_error'] = str(exc)[:500]
            state['results'] = [row for row in state['results'] if row['base_tag'] != item['base_tag']] + [result]
            state['verified_count'] = len(usable_entries(state['results']))
            save()
        verified = usable_entries(state['results'])
        state.update(verified_count=len(verified), stage='finished',
                     status='complete' if len(verified) >= args.target else 'incomplete')
        save()
        atomic_json(folder / 'verified-models.json', {'models': verified, 'count': len(verified),
                    'smoke_prompt': SMOKE_PROMPT, 'training_performed': False})
        print(f'{state["status"]}: {len(verified)}/{args.target} distinct weights answered.', flush=True)
        return 0 if state['status'] == 'complete' else 1
    finally:
        lock.unlink(missing_ok=True)


if __name__ == '__main__':
    raise SystemExit(main())
