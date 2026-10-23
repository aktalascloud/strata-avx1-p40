"""Run the unchanged strict lifecycle checks in the boot task's security context."""
import hashlib
import json
import msvcrt
import os
from pathlib import Path
import subprocess
import time
import uuid
import psutil

ROOT = Path(__file__).resolve().parents[1]
REQUEST = ROOT / 'runtime/state/scheduler-request.json'
RESPONSE = ROOT / 'runtime/state/scheduler-response.json'


def task_context():
    scheduler = psutil.win_service_get('Schedule').pid()
    for parent in psutil.Process().parents()[:6]:
        if parent.pid == scheduler:
            return True
        if parent.name().lower() not in {'python.exe', 'powershell.exe', 'pwsh.exe', 'taskeng.exe', 'taskhostw.exe'}:
            return False
    return False


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pins():
    return {name: sha(ROOT / name) for name in ('strata-server-launch.json', 'strata-davidau.json',
            'tools/service-lifecycle.py', 'tools/scheduler_control.py', 'tools/service-control-review.json', 'tools/start-server.py')}


def dispatch(action):
    if action not in ('--verify', '--stop'):
        raise RuntimeError('Unknown lifecycle action')
    with (ROOT / 'scheduler-control.lock').open('a+b') as lock:
        lock.seek(0)
        msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        try:
            request = dict(schema=1, request_id=uuid.uuid4().hex, action=action, pins=pins())
            REQUEST.write_text(json.dumps(request), encoding='utf-8')
            request_hash = sha(REQUEST)
            powershell = Path(os.environ['WINDIR']) / 'System32/WindowsPowerShell/v1.0/powershell.exe'
            run = subprocess.run([str(powershell), '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
                                  str(ROOT / 'tools/invoke-control-task.ps1')], capture_output=True, text=True)
            if run.returncode:
                raise RuntimeError('Windows control task could not be started')
            deadline = time.monotonic() + 720
            while time.monotonic() < deadline:
                try:
                    value = json.loads(RESPONSE.read_text('utf-8'))
                    if value['request_id'] == request['request_id'] and value['request_sha256'] == request_hash:
                        print(json.dumps(value['result']))
                        return int(value['exit_code'])
                except (OSError, ValueError, KeyError):
                    pass
                time.sleep(.25)
            raise RuntimeError('Windows lifecycle task timed out; no force stop')
        finally:
            lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)


def worker():
    if not task_context():
        raise RuntimeError('Control worker requires Windows Task Scheduler')
    raw = REQUEST.read_bytes()
    request = json.loads(raw)
    result = {'status': 'verification_or_stop_failed', 'stopped': False, 'fail_closed': True}
    code = 2
    try:
        if request['schema'] != 1 or request['action'] not in ('--verify', '--stop') or request['pins'] != pins():
            raise RuntimeError('Lifecycle request/pins changed; no control action')
        python = ROOT / 'runtime/python/python.exe'
        run = subprocess.run([str(python), '-I', '-s', '-B', str(ROOT / 'tools/service-lifecycle.py'), request['action']],
                             capture_output=True, text=True)
        result, code = json.loads(run.stdout), run.returncode
    except Exception as error:
        result.update(error_type=type(error).__name__, error=str(error))
    value = dict(request_id=request['request_id'], request_sha256=hashlib.sha256(raw).hexdigest(), exit_code=code, result=result)
    temporary = RESPONSE.with_suffix('.tmp')
    temporary.write_text(json.dumps(value), encoding='utf-8')
    os.replace(temporary, RESPONSE)


if __name__ == '__main__':
    import sys
    if sys.argv[1:] == ['--check-context']:
        raise SystemExit(0 if task_context() else 2)
    if sys.argv[1:]:raise SystemExit('Unknown control-worker argument')
    worker()
