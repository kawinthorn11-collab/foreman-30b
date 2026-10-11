"""Apply the Foreman persona to an installed Ollama model without training weights."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parent))
from project import ROOT, make_installed_profile, ollama


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', required=True, help='Exact already-installed Ollama model name')
    parser.add_argument('--name', required=True, help='New Foreman Ollama model name')
    parser.add_argument('--port', type=int, default=11434)
    parser.add_argument('--context', type=int, default=2048)
    parser.add_argument('--output', type=int, default=512)
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error('Invalid loopback port')
    prompt = (ROOT / 'prompt.txt').read_text(encoding='utf-8')
    profile = make_installed_profile(args.base, prompt, args.context, args.output)
    make_installed_profile(args.name, prompt, args.context, args.output)
    host = f'http://127.0.0.1:{args.port}'
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(host + '/api/tags', timeout=10) as response:
        names = {item['name'] for item in json.load(response)['models']}
    if args.base not in names:
        raise SystemExit('Base model is not installed on this server. No profile created.')
    folder = ROOT / 'profiles-local'
    folder.mkdir(exist_ok=True)
    path = folder / (args.name.replace('/', '_').replace(':', '_') + '.Modelfile')
    path.write_text(profile, encoding='utf-8')
    env = os.environ.copy()
    env['OLLAMA_HOST'] = host
    subprocess.run([ollama(), 'create', args.name, '-f', str(path)], env=env, check=True)
    print(f'Created {args.name} from {args.base}. Prompt customization only; no weight training performed.')


if __name__ == '__main__':
    main()
