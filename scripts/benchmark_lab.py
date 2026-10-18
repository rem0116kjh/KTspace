"""Reproducible, sequential CPU/byte comparison; no external services or user data.

Run: python3 -S scripts/benchmark_lab.py --baseline e626955
The renderer uses Node with a stub canvas. These timings are NOT browser FPS.
"""
import argparse
import gzip
import hashlib
import importlib
import json
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
CASES = [
    ('sun_mass', {}),
    ('blackhole', {'scenario': 'blackhole', 'mass': 10, 'distance': 1}),
    ('sirius', {'scenario': 'sirius', 'distance': 5}),
    ('earth_rotation', {'scenario': 'earth_rotation', 'hours': 12}),
]


def worker(root, variant, fixtures):
    sys.path.insert(0, root)
    workspace = importlib.import_module('scenario_workspace')
    preview = importlib.import_module('preview')
    results, payloads = {}, {}
    for name, settings in CASES:
        def operation():
            if variant:
                return preview.response_bytes(settings, compressed=True)[0]
            payload = workspace.build_workspace(settings)
            return json.dumps(payload, ensure_ascii=False, allow_nan=False).encode()

        if variant:
            preview._encoded_workspace.cache_clear()
        # Cold here includes integration, serialization and compression, not imports.
        started = time.perf_counter_ns()
        body = operation()
        cold_ms = (time.perf_counter_ns() - started) / 1e6
        for _ in range(8):
            operation()
        batches = []
        for _ in range(5):
            start = time.perf_counter_ns()
            for _ in range(80):
                body = operation()
            batches.append((time.perf_counter_ns() - start) / 1e6 / 80)
        payload = json.loads(gzip.decompress(body) if variant else body)
        payloads[name] = payload
        canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
        results[name] = dict(warm_median_ms=statistics.median(batches), warm_batches_ms=batches,
                             cold_ms=cold_ms, wire_bytes=len(body),
                             payload_sha256=hashlib.sha256(canonical.encode()).hexdigest())
    Path(fixtures).write_text(json.dumps(payloads, ensure_ascii=False))
    print(json.dumps(results))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', default='e626955')
    parser.add_argument('--worker', nargs=3, metavar=('ROOT', 'VARIANT', 'FIXTURES'))
    args = parser.parse_args()
    if args.worker:
        worker(args.worker[0], args.worker[1] == '1', args.worker[2])
        return
    baseline = subprocess.check_output(['git', 'rev-parse', args.baseline], cwd=ROOT, text=True).strip()
    with tempfile.TemporaryDirectory(prefix='orbit-benchmark-') as tmp:
        tmp = Path(tmp)
        before = tmp / 'baseline'
        before.mkdir()
        for name in ['preview.py', 'scenario_workspace.py', 'orbital_dynamics.py', 'learning_content.py',
                     'simulation_engine.py', 'solar_scene.py', 'orbit_ui/solar-view.js']:
            target = before / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(subprocess.check_output(['git', 'show', f'{baseline}:{name}'], cwd=ROOT))
        results = {}
        # Repeat baseline -> candidate as two sequential pairs, without file IO in timed loops.
        for repeat in range(2):
            for label, root, variant in [('baseline', before, '0'), ('candidate', ROOT, '1')]:
                fixtures = tmp / f'{label}.json'
                run = subprocess.check_output([sys.executable, '-S', str(Path(__file__).resolve()),
                                                '--worker', str(root), variant, str(fixtures)], text=True)
                results.setdefault(label, []).append(json.loads(run))
        for name, _ in CASES:
            fingerprints = {run[name]['payload_sha256'] for repeats in results.values() for run in repeats}
            if len(fingerprints) != 1:
                raise AssertionError(f'Payload changed for {name}')
        renderer = subprocess.check_output(['node', str(ROOT / 'scripts/benchmark_solar_view.mjs'),
                                            str(before / 'orbit_ui/solar-view.js'),
                                            str(ROOT / 'orbit_ui/solar-view.js'),
                                            str(tmp / 'baseline.json')], text=True)
        print(json.dumps(dict(baseline=baseline, python=sys.version.split()[0], host=platform.platform(),
                              backend=results, renderer=json.loads(renderer)), indent=2))


if __name__ == '__main__':
    main()
