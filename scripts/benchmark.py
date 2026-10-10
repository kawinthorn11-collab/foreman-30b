"""Small inference smoke test. Generated code is recorded, never auto-executed."""
import ctypes
import datetime
import json
import subprocess
import threading
import time
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from project import ROOT, chat, config, request

class Memory(ctypes.Structure):
    _fields_ = [('length', ctypes.c_ulong), ('load', ctypes.c_ulong)] + [(name, ctypes.c_ulonglong) for name in ['total', 'available', 'page_total', 'page_available', 'virtual_total', 'virtual_available', 'extended']]

def memory():
    state = Memory()
    state.length = ctypes.sizeof(state)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(state)):
        raise OSError('GlobalMemoryStatusEx failed')
    return {'ram_total_gib': state.total / 1024**3, 'ram_available_gib': state.available / 1024**3}

def gpu():
    result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total,memory.used,temperature.gpu', '--format=csv,noheader,nounits'], capture_output=True, text=True, timeout=5, check=True)
    name, total, used, temp = [value.strip() for value in result.stdout.strip().split(',')]
    return {'name': name, 'total_mib': int(total), 'used_mib': int(used), 'temperature_c': int(temp)}

TASKS = [
    ('identity', 'Introduce yourself in one short English sentence. State your name.'),
    ('clamp', 'Return only Python code for clamp(value, low, high). Return value bounded inclusively between low and high. Raise ValueError if low > high. Do not import modules.'),
    ('deduplicate', 'Return only Python code for deduplicate(items): remove duplicate hashable items while preserving first occurrence order. Do not mutate the input and do not import modules.')
]

def main():
    samples = []
    done = threading.Event()
    def monitor():
        while not done.is_set():
            try:
                samples.append({'time': time.time(), **memory(), 'gpu': gpu()})
            except (OSError, subprocess.SubprocessError, ValueError):
                pass
            done.wait(2)
    thread = threading.Thread(target=monitor, daemon=True)
    thread.start()
    results = []
    failure = None
    try:
        for task, prompt in TASKS:
            print(f'Running {task}...', flush=True)
            began = time.perf_counter()
            output = chat(prompt)
            item = {'task': task, 'prompt': prompt, 'response': output['message']['content'],
                    'wall_seconds': round(time.perf_counter() - began, 2),
                    'prompt_tokens': output.get('prompt_eval_count'), 'output_tokens': output.get('eval_count'),
                    'load_seconds': output.get('load_duration', 0) / 1e9,
                    'tokens_per_second': round(output.get('eval_count', 0) / max(output.get('eval_duration', 1) / 1e9, 0.001), 2)}
            results.append(item)
            print(json.dumps(item), flush=True)
        loaded = request('/api/ps')
    except Exception as error:
        failure = f'{type(error).__name__}: {error}'
        loaded = {}
        raise
    finally:
        done.set()
        thread.join(6)
        report = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'scope': 'Three short smoke tasks; not a coding capability benchmark',
                  'config': config(), 'training_status': 'not_trained', 'results': results, 'failure': failure,
                  'loaded': loaded, 'samples': samples,
                  'minimum_system_available_ram_gib': min((s['ram_available_gib'] for s in samples), default=None),
                  'peak_total_gpu_used_mib': max((s['gpu']['used_mib'] for s in samples), default=None),
                  'memory_note': 'System-wide memory and GPU usage includes OS and other apps; not model-only allocations.'}
        (ROOT / 'docs/benchmark.json').write_text(json.dumps(report, indent=2), encoding='utf-8')

if __name__ == '__main__':
    main()
