#!/usr/bin/env python3
"""User-started, fixed matrix only. No build, automatic analysis or next Gate."""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import sys

BASE = Path(__file__).resolve().parent
BATCH_ID = 'source3d_translation_20261022_v1'
DIRECTIONS = ('x+', 'x-', 'y+', 'y-', 'z+', 'z-', 'xyz+', 'xyz-', 'zero')

def cases():
    for n in (16, 32):
        for direction in DIRECTIONS:
            for variant in ('old', 'new'):
                tag = direction.replace('+', 'p').replace('-', 'm')
                yield f'{BATCH_ID}_{variant}_n{n}_{tag}', variant, n, direction

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def check_binding():
    binding = json.loads((BASE/'evidence/build_binding.json').read_text())
    bad = [name for name, digest in binding['sha256'].items()
           if not Path(name).is_file() or sha(name) != digest]
    if bad:
        raise RuntimeError(f'build binding mismatch: {bad}')
    if (BASE/'output'/BATCH_ID).exists():
        raise RuntimeError('batch already exists; no overwrite or resume')
    if (BASE/'evidence'/BATCH_ID).exists():
        raise RuntimeError('batch evidence already exists')
    return binding

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run', action='store_true', help='explicitly start the fixed 36-case matrix')
    args = p.parse_args()
    binding = check_binding()
    print(f'PRECHECK_OK: {len(binding["sha256"])} hashes; 36 cases; no solver started yet', flush=True)
    if not args.run:
        return 0
    evidence = BASE/'evidence'/BATCH_ID
    output = BASE/'output'/BATCH_ID
    evidence.mkdir(parents=True, exist_ok=False)
    output.mkdir(parents=True, exist_ok=False)
    manifest = dict(batch_id=BATCH_ID, started_utc=now(), source_binding=binding,
                    openlb_head=binding['openlb_head'], cases=[],
                    NUMERICAL_GATE='NOT_EVALUATED', RESULT_PASS='NOT_EVALUATED',
                    geometry_PASS='NOT_EVALUATED')
    manifest_path = evidence/'manifest.json'
    code = 0
    try:
        for run_id, variant, n, direction in cases():
            sub = evidence/run_id
            sub.mkdir()
            command = [str(BASE/'build/translation_check'), variant, str(n), direction, str(output/run_id)]
            entry = dict(run_id=run_id, variant=variant, N=n, direction=direction,
                         command=command, cwd=str(BASE), started_utc=now())
            manifest['cases'].append(entry)
            manifest_path.write_text(json.dumps(manifest, indent=2)+'\n')
            print('START', run_id, flush=True)
            with (sub/'console.log').open('w') as log:
                result = subprocess.run(command, cwd=BASE, stdout=log, stderr=subprocess.STDOUT)
            (sub/'exit_code.txt').write_text(str(result.returncode)+'\n')
            entry.update(finished_utc=now(), independent_exit_code=result.returncode)
            (sub/'manifest.json').write_text(json.dumps(entry, indent=2)+'\n')
            manifest_path.write_text(json.dumps(manifest, indent=2)+'\n')
            if result.returncode != 0:
                code = result.returncode
                break
    except KeyboardInterrupt:
        manifest['exception'] = 'KeyboardInterrupt; incomplete child evidence retained'
        code = 130
    except Exception as exc:
        manifest['exception'] = repr(exc)
        code = 3
    finally:
        bad = [name for name, digest in binding['sha256'].items()
               if not Path(name).is_file() or sha(name) != digest]
        if bad:
            code = code or 5
        manifest.update(finished_utc=now(), source_hashes_unchanged=not bad,
                        source_mismatches=bad, independent_exit_code=code)
        manifest_path.write_text(json.dumps(manifest, indent=2)+'\n')
        (evidence/'exit_code.txt').write_text(str(code)+'\n')
    print(f'BATCH_EXIT={code}; analysis not run; no physical Gate released', flush=True)
    return code

if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as exc:
        print(f'PRECHECK_FAILED: {exc}', file=sys.stderr)
        sys.exit(2)
