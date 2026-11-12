#!/usr/bin/env python3
"""Freeze prepared source/input/binary/library hashes. No numerical execution."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parent


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--refresh-preparation',action='store_true')
    args=parser.parse_args()
    target=ROOT/'release_manifest.json'
    if any((c/'runtime').exists() or (c/'referenceEvidence').exists() for c in (ROOT/'prepared').iterdir()):
        raise SystemExit('Runtime evidence exists; cannot re-freeze this release')
    if target.exists() and not args.refresh_preparation:
        raise SystemExit('Refusing to overwrite release; explicit preparation refresh required')
    plan=json.loads((ROOT/'prepared_manifest.json').read_text())
    paths=list(plan['sha256'])+['prepared_manifest.json']
    paths += [str(p.relative_to(ROOT)) for p in ROOT.glob('*.py')]
    paths += ['PROTOCOL.md','run_config.md','README.md','.gitignore',
              'solver/paper1StokesReference.C','solver/Make/files','solver/Make/options',
              'bin/paper1StokesReference','tests/test_postprocess.py']
    for fn,expected in plan['sha256'].items():
        if digest(ROOT/fn)!=expected:raise SystemExit('Prepared input drift: '+fn)
    linked=subprocess.run(['ldd',str(ROOT/'bin/paper1StokesReference')],check=True,
                          capture_output=True,text=True).stdout
    libraries=[Path(p) for p in re.findall(r'=>\s+(/\S+)',linked)]
    # Runtime mesh utilities are also pinned; none is executed here.
    libraries += [Path('/opt/openfoam13/platforms/linux64GccDPInt32Opt/bin')/n
                  for n in ('blockMesh','checkMesh')]
    release=dict(status='PREPARED_NOT_RUN',openfoam='Foundation 13',
                 sha256={fn:digest(ROOT/fn) for fn in sorted(set(paths))},
                 external_sha256={str(p):digest(p) for p in sorted(set(libraries))},
                 formal_review_status='ASTRA_INITIAL_REVIEW_DONE_FIX_RECHECK_PENDING_QUOTA',
                 numerical_execution_authorized=False)
    target.write_text(json.dumps(release,indent=2)+'\n')
    print(f"Frozen {len(release['sha256'])} local and {len(release['external_sha256'])} external identities. No solver run.")


if __name__=='__main__':main()
