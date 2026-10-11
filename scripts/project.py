"""Foreman: reproducible prompted local prototype, not fine-tuned weights."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
ACTIVE_CONFIG = 'config.json'
WEIGHTS_DIR = ROOT / 'weights'

def check_config(config):
    for key, lo, hi in [('context', 512, 8192), ('gpu_layers', 0, 48),
                        ('max_output', 1, 2048), ('threads', 1, 16), ('batch', 1, 256)]:
        value = config.get(key, {'threads': 4, 'batch': 64}.get(key))
        if type(value) is not int or not lo <= value <= hi:
            raise ValueError(f'{key} must be an integer between {lo} and {hi}')
    if config['max_output'] > config['context']:
        raise ValueError('Output limit exceeds context')
    if type(config.get('port', 11435)) is not int or not 1024 <= config.get('port', 11435) <= 65535:
        raise ValueError('Invalid local port')
    return config

def validate_examples(examples):
    seen = set()
    secret = re.compile(r'(?:Bearer\s+[A-Za-z0-9_-]{32,}|sk-[A-Za-z0-9_-]{24,}|hn_[A-Za-z0-9_-]{32,})')
    if not examples:
        raise ValueError('Empty dataset')
    for example in examples:
        messages = example.get('messages', [])
        if messages and messages[0].get('role') == 'system':
            messages = messages[1:]
        if not messages or len(messages) % 2:
            raise ValueError('Each conversation needs complete user/assistant pairs')
        for i, message in enumerate(messages):
            role = 'user' if i % 2 == 0 else 'assistant'
            if message.get('role') != role or not isinstance(message.get('content'), str) or not message['content'].strip():
                raise ValueError('Invalid conversation roles or empty text')
        raw = json.dumps(example, sort_keys=True, ensure_ascii=False)
        if secret.search(raw):
            raise ValueError('Possible credential in dataset')
        digest = hashlib.sha256(json.dumps(messages, sort_keys=True).encode()).hexdigest()
        if digest in seen:
            raise ValueError('Duplicate conversation')
        seen.add(digest)
    return len(examples)

def make_modelfile(weight, prompt, config):
    check_config(config)
    if '"""' in prompt or '\n' in str(weight) or '"' in str(weight):
        raise ValueError('Unsupported Modelfile delimiter')
    return (f'FROM "{Path(weight).resolve().as_posix()}"\nSYSTEM """{prompt.strip()}"""\n'
            f'PARAMETER num_ctx {config["context"]}\nPARAMETER num_gpu {config["gpu_layers"]}\n'
            f'PARAMETER num_thread {config.get("threads", 4)}\nPARAMETER num_predict {config["max_output"]}\n'
            f'PARAMETER num_batch {config.get("batch", 64)}\nPARAMETER temperature 0.2\nPARAMETER top_p 0.8\n'
            'PARAMETER top_k 20\nPARAMETER repeat_penalty 1.05\n')

def make_installed_profile(base, prompt, context=2048, max_output=512):
    """Prompt customization of installed weights; not training or conversion."""
    if not isinstance(base, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:/-]*', base) or '..' in base or base.startswith('/'):
        raise ValueError('Use a valid installed Ollama model name')
    if not isinstance(prompt, str) or not prompt.strip() or '"""' in prompt:
        raise ValueError('Invalid system prompt')
    if type(context) is not int or not 512 <= context <= 65536:
        raise ValueError('Context must be between 512 and 65536; hardware fit is separate')
    if type(max_output) is not int or not 1 <= max_output <= min(context, 2048):
        raise ValueError('Invalid output limit')
    return (f'FROM {base}\nSYSTEM """{prompt.strip()}"""\n'
            f'PARAMETER num_ctx {context}\nPARAMETER num_predict {max_output}\n'
            'PARAMETER temperature 0.2\n')

def config():
    return check_config(json.loads((ROOT / ACTIVE_CONFIG).read_text(encoding='utf-8')))

def request(path, payload=None, timeout=900):
    c = config()
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(f'http://127.0.0.1:{c["port"]}{path}', data=data,
                                 headers={'Content-Type': 'application/json'})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(req, timeout=timeout) as response:
        return json.load(response)

def ollama():
    candidate = os.environ.get('FOREMAN_OLLAMA') or shutil.which('ollama')
    bundled = ROOT.parent / 'HuaNaNgan/runtime/ollama/ollama.exe'
    if not candidate and bundled.exists():
        candidate = str(bundled)
    if not candidate:
        raise RuntimeError('Install Ollama or set FOREMAN_OLLAMA to its executable')
    return candidate

def environment():
    env = os.environ.copy()
    env.update(OLLAMA_HOST=f'127.0.0.1:{config()["port"]}', OLLAMA_MODELS=str(ROOT / 'cache'),
               OLLAMA_VULKAN='1', CUDA_VISIBLE_DEVICES='-1', OLLAMA_NUM_PARALLEL='1',
               OLLAMA_MAX_LOADED_MODELS='1', OLLAMA_KEEP_ALIVE='2m', OLLAMA_NO_CLOUD='1')
    return env

def server_identity():
    if os.name != 'nt':
        raise RuntimeError('Server ownership check currently supports Windows only')
    port = config()['port']
    script = (f'$listener = Get-NetTCPConnection -State Listen -LocalPort {port} -ErrorAction SilentlyContinue | '
              "Where-Object LocalAddress -eq '127.0.0.1'; if ($listener) { "
              '$process = Get-CimInstance Win32_Process -Filter ("ProcessId=" + $listener.OwningProcess); '
              '[pscustomobject]@{pid=$process.ProcessId;exe=$process.ExecutablePath;'
              "created=$process.CreationDate.ToUniversalTime().ToString('o')} | ConvertTo-Json -Compress }")
    result = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', script],
                            capture_output=True, text=True, timeout=20, check=True,
                            creationflags=0x08000000)
    return json.loads(result.stdout) if result.stdout.strip() else None

def owns_server():
    try:
        saved = json.loads((ROOT / 'logs/server-identity.json').read_text())
        actual = server_identity()
        return actual == saved and str(Path(actual['exe']).resolve()).lower() == str(Path(ollama()).resolve()).lower()
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
        return False

def start():
    try:
        request('/api/version', timeout=2)
    except (OSError, ValueError):
        pass
    else:
        if not owns_server():
            raise RuntimeError('Port occupied by a server not owned by Foreman; choose a free port')
        return
    logs = ROOT / 'logs'
    logs.mkdir(exist_ok=True)
    with (logs / 'ollama.log').open('ab') as log:
        proc = subprocess.Popen([ollama(), 'serve'], env=environment(), stdout=log, stderr=log,
                                creationflags=0x08000000 if os.name == 'nt' else 0)
    (logs / 'server.pid').write_text(str(proc.pid))
    for _ in range(120):
        if proc.poll() is not None:
            raise RuntimeError('Ollama exited; inspect logs/ollama.log')
        try:
            request('/api/version', timeout=1)
            identity = server_identity()
            if not identity or identity['pid'] != proc.pid:
                proc.terminate()
                raise RuntimeError('Listening server is not owned by the launched Foreman process')
            (logs / 'server-identity.json').write_text(json.dumps(identity))
            return
        except OSError:
            time.sleep(0.5)
    raise RuntimeError('Server startup timed out')

def verify(weight):
    c = config()
    if not weight.exists() or weight.stat().st_size != c['bytes']:
        raise ValueError('Model file missing or wrong size')
    with weight.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    if digest != c['sha256']:
        raise ValueError('Model SHA256 mismatch')
    return digest

def download():
    c = config()
    folder = WEIGHTS_DIR
    folder.mkdir(parents=True, exist_ok=True)
    final = folder / c['filename']
    if final.exists():
        verify(final)
        return final
    part = final.with_suffix(final.suffix + '.part')
    needed = c['bytes'] - (part.stat().st_size if part.exists() else 0)
    cache_parent = ROOT / 'cache'
    cache_parent.mkdir(exist_ok=True)
    same_device = folder.stat().st_dev == cache_parent.stat().st_dev
    download_needed = needed + (c['bytes'] if same_device else 0) + 2 * 1024**3
    if shutil.disk_usage(folder).free < download_needed or shutil.disk_usage(cache_parent).free < c['bytes'] + 2 * 1024**3:
        raise RuntimeError('Insufficient disk space for download and Ollama model cache')
    url = f'https://huggingface.co/{c["gguf_repo"]}/resolve/{c["revision"]}/{c["filename"]}?download=true'
    subprocess.run(['curl.exe' if os.name == 'nt' else 'curl', '-L', '--fail', '--retry', '3',
                    '-C', '-', '-o', str(part), url], check=True)
    verify(part)
    part.replace(final)
    return final

def setup():
    weight = download()
    start()
    model = ROOT / 'Modelfile.local'
    model.write_text(make_modelfile(weight, (ROOT / 'prompt.txt').read_text(encoding='utf-8'), config()), encoding='utf-8')
    subprocess.run([ollama(), 'create', config()['model'], '-f', str(model)], env=environment(), check=True)

def chat(prompt):
    start()
    c = config()
    return request('/api/chat', {'model': c['model'], 'stream': False, 'keep_alive': '2m',
                                 'messages': [{'role': 'user', 'content': prompt}]})

def main():
    global ACTIVE_CONFIG, WEIGHTS_DIR
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['setup', 'start', 'chat', 'validate', 'interactive'])
    parser.add_argument('--prompt', default='Introduce yourself in one sentence.')
    parser.add_argument('--profile', choices=['coder30b', 'qwen36'], default='coder30b')
    parser.add_argument('--weights-dir', type=Path, help='Optional GGUF download directory, e.g. D:/ForemanModels')
    args = parser.parse_args()
    ACTIVE_CONFIG = 'config-35b.json' if args.profile == 'qwen36' else 'config.json'
    if args.weights_dir is not None:
        WEIGHTS_DIR = args.weights_dir.resolve()
    if args.command == 'setup':
        setup()
    elif args.command == 'start':
        start()
    elif args.command == 'validate':
        rows = [json.loads(line) for line in (ROOT / 'data/style-draft.jsonl').read_text(encoding='utf-8').splitlines() if line]
        print(f'Validated {validate_examples(rows)} draft conversations; human review still required.')
    elif args.command == 'chat':
        print(chat(args.prompt)['message']['content'])
    else:
        start()
        subprocess.run([ollama(), 'run', config()['model']], env=environment(), check=True)

if __name__ == '__main__':
    main()
