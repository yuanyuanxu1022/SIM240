"""Run software tests under an audit hook forbidding native/VTK/build processes."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import json,sys,unittest
ROOT=Path('/home/dell/yuanyuanxu/SIM240');OUT=Path(__file__).resolve().parent
CHECK=ROOT/'CASE/unseen_v2_reference_checker_S4_reuse_v1';events=[]
def audit(event,args):
    if event=='subprocess.Popen':
        executable,argv,_,_=args
        if not (Path(executable).resolve()==Path(sys.executable).resolve() and
                isinstance(argv,(list,tuple)) and str(CHECK/'analysis/check_results.py') in argv and '-B' in argv):
            raise AssertionError('Native/VTK/build process forbidden in S4 software checks')
        events.append(dict(executable=str(executable),argv=list(argv),role='Python checker CLI on synthetic packet'))
    if event in ['os.system','os.exec','os.posix_spawn','os.posix_spawnp']:
        raise AssertionError('No shell/native exec in software checks')
sys.addaudithook(audit)
suite=unittest.defaultTestLoader.discover(str(CHECK/'tests'),pattern='test_*.py')
result=unittest.TextTestRunner(verbosity=2).run(suite)
data=dict(at=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),tests_run=result.testsRun,
    failures=len(result.failures),errors=len(result.errors),successful=result.wasSuccessful(),
    allowed_Python_CLI_subprocesses=events,native_invocations=0,VTK_invocations=0,build_invocations=0,
    fixtures='labelled SYNTHETIC; temp directories only; no real field or numerical acceptance')
with (OUT/'software_verification.json').open('x') as f:json.dump(data,f,ensure_ascii=False,indent=2);f.write('\n')
raise SystemExit(0 if result.wasSuccessful() else 1)
