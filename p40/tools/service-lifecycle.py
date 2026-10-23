"""Verify this saved Strata server. Stop fails closed until a reviewed atomic drain is available."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import hashlib
import re
import time
from pathlib import Path
import urllib.request

import psutil

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / 'strata-davidau.json'
STATE = ROOT / 'strata-server-launch.json'
PORT = 8093
BASE = 'http://127.0.0.1:8093'


def norm(path):
    return str(Path(path).resolve()).casefold()


def local_path(value, label):
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError('Missing local path: ' + label)
    path = Path(value)
    if '..' in path.parts or (path.drive and not path.is_absolute()):
        raise RuntimeError('Traversal/drive-relative path rejected: ' + label)
    resolved = (path if path.is_absolute() else ROOT / path).resolve(strict=True)
    if not resolved.is_relative_to(ROOT.resolve()):
        raise RuntimeError('Path leaves this project root: ' + label)
    return resolved


def portable_paths(state, cfg):
    active_file = ROOT / 'runtime/active.json'
    active = (json.loads(active_file.read_text(encoding='utf-8-sig')) if active_file.exists() else
              {'id': 'initial', 'source': 'runtime/source',
               'engine': 'runtime/engine/strata.exe', 'vision': 'runtime/vision/strata-vision.exe'})
    if not isinstance(active, dict) or not isinstance(active.get('id'), str) or not active['id']:
        raise RuntimeError('Invalid active runtime identity')
    if state.get('version') != active['id']:
        raise RuntimeError('Saved runtime version differs from active runtime')
    expected = {key: local_path(active.get(key), 'active.' + key) for key in ('source', 'engine', 'vision')}
    if not expected['source'].is_dir() or any(not expected[key].is_file() for key in ('engine', 'vision')):
        raise RuntimeError('Active runtime source/engine/vision has an unexpected file type')
    for key, path in expected.items():
        saved = local_path(state.get(key), 'state.' + key)
        if norm(saved) != norm(path):
            raise RuntimeError('Saved path differs from active runtime: ' + key)
        state[key] = str(saved)
    if (norm(cfg['cwd']) != norm(expected['source']) or norm(cfg['exe']) != norm(expected['engine']) or
            norm(cfg['vision']['exe']) != norm(expected['vision'])):
        raise RuntimeError('Config source/engine/vision differs from active runtime')


def arg(cmd, flag):
    if cmd.count(flag) != 1 or cmd.index(flag) + 1 >= len(cmd):
        raise RuntimeError('Expected exactly one ' + flag)
    return cmd[cmd.index(flag) + 1]


def identity(p, expected_names=None):
    row = {'pid': p.pid, 'ppid': p.ppid(), 'created': p.create_time(), 'name': p.name()}
    try:
        return {**row, 'exe': p.exe(), 'cmd': p.cmdline(), 'restricted': False}
    except psutil.AccessDenied:
        if expected_names is None or row['name'].casefold() not in expected_names:
            raise RuntimeError('Process identity unavailable for unrecognized PID ' + str(p.pid))
        return {**row, 'restricted': True}


def listener():
    owners = {c.pid for c in psutil.net_connections(kind='tcp')
              if c.status == psutil.CONN_LISTEN and c.laddr.port == PORT}
    if len(owners) != 1 or None in owners:
        raise RuntimeError(f'Unique port{PORT} owner cannot be verified')
    return owners.pop()


def server(row, state, schema):
    if row.get('restricted') or row['name'].casefold() != 'python.exe':
        return False
    cmd = row['cmd']
    try:
        if norm(arg(cmd, '--config')) != norm(CONFIG):
            return False
        if schema == 1:
            return '-m' in cmd and arg(cmd, '-m') == 'serve.server' and arg(cmd, '--port') == str(PORT)
        control_ok=(schema!=3 or (norm(arg(cmd,'--control-path'))==norm(state['control']['path']) and
                                 arg(cmd,'--control-nonce')==state['control']['nonce']))
        return (control_ok and norm(row['exe']) == norm(state['python']) and '-I' in cmd and '-s' in cmd and
                any(norm(part) == norm(ROOT/'tools/start-server.py') for part in cmd if part.endswith('.py')) and
                norm(arg(cmd, '--source')) == norm(state['source']))
    except (RuntimeError, OSError, ValueError):
        return False


def verified_console(row, wrapper_pid, rows, native_exes, expected_native):
    """Allow only the Windows console for this wrapper or an exactly identified native child."""
    conhost = Path(os.environ.get('SystemRoot', 'C:\\Windows'))/'System32/conhost.exe'
    if (row.get('restricted') or row['name'].casefold()!='conhost.exe' or
            norm(row['exe'])!=norm(conhost) or row['cmd'][1:]!=['0x4']):
        return False
    if row['ppid']==wrapper_pid:
        return True
    parent=next((r for r in rows if r['pid']==row['ppid']),None)
    return bool(parent and not parent.get('restricted') and
                parent['name'].casefold() in expected_native and norm(parent['exe']) in native_exes and
                row['created']>=parent['created'])


def verify(cfg):
    state = json.loads(STATE.read_text(encoding='utf-8-sig'))
    schema = state.get('schema', 1)
    if schema not in (1, 2, 3) or norm(state['config']) != norm(CONFIG):
        raise RuntimeError('Unsupported launch-state schema/config')
    expected_python = ROOT / ('.venv/Scripts/python.exe' if schema == 1 else 'runtime/python/python.exe')
    if norm(state['python']) != norm(expected_python):
        raise RuntimeError('Saved Python is outside the expected local runtime')
    if schema >= 2:
        portable_paths(state, cfg)
    wrapper = psutil.Process(int(state['pid']))
    owner = psutil.Process(listener())
    wr, own = identity(wrapper), identity(owner)
    if not server(wr, state, schema) or not server(own, state, schema):
        raise RuntimeError('Saved wrapper/listener command identity does not match this server')
    if norm(wr['exe']) != norm(state['python']):
        raise RuntimeError('Wrapper executable does not match saved Python')
    started = dt.datetime.fromisoformat(state['started_utc'].replace('Z', '+00:00')).timestamp()
    if abs(wr['created'] - started) > 10:
        raise RuntimeError('Saved PID creation time differs; possible PID reuse')
    if owner.pid != wrapper.pid and wrapper.pid not in [p.pid for p in owner.parents()]:
        raise RuntimeError('Port owner is not in the saved wrapper parent tree')
    expected_native = {Path(cfg['exe']).name.casefold(), Path(cfg['vision']['exe']).name.casefold()}
    allowed_exe = {norm(cfg['exe']), norm(cfg['vision']['exe']), norm(state['python'])}
    rows = [wr] + [identity(p, expected_native) for p in wrapper.children(recursive=True)]
    ids = {r['pid'] for r in rows}
    native_exes={norm(cfg['exe']),norm(cfg['vision']['exe'])}
    for row in rows:
        if row['pid'] != wrapper.pid and row['ppid'] not in ids:
            raise RuntimeError('Child parent is outside the captured tree')
        if row.get('restricted'):
            row['native_child'] = True
            continue  # Only official /unload may end this owner-protected child.
        if server(row, state, schema):
            continue
        if verified_console(row,wrapper.pid,rows,native_exes,expected_native):
            row['console'] = True
            continue
        if norm(row['exe']) not in allowed_exe or row['name'].casefold() not in expected_native:
            raise RuntimeError('Unrecognized child PID ' + str(row['pid']) + '; no stop performed')
        row['native_child'] = True
    return {'schema': schema, 'wrapper': wr, 'owner': own, 'rows': rows, 'state':state}


def control_paths(state):
    control=state.get('control') or {}
    nonce=control.get('nonce','')
    if control.get('protocol')!='local_file_drain_v1' or not re.fullmatch('[0-9a-f]{64}',nonce):
        raise RuntimeError('Unsupported/missing schema3 control identity')
    path=Path(control.get('path','')).resolve()
    if path.parent!=(ROOT/'runtime/state').resolve() or path.name!='control-'+nonce+'.json':
        raise RuntimeError('Control path differs from this launch nonce/root')
    for key,file in (('bootstrap_sha256','start-server.py'),('review_sha256','service-control-review.json')):
        if hashlib.sha256((ROOT/'tools'/file).read_bytes()).hexdigest().casefold()!=str(control.get(key,'')).casefold():
            raise RuntimeError('Loaded control bootstrap/review changed; inspect before stop')
    return path,path.with_suffix('.ack.json'),nonce


def same_process(row):
    try:return psutil.Process(row['pid']).create_time()==row['created']
    except psutil.NoSuchProcess:return False


def controlled_stop(tree,cfg,timeout=600):
    state=tree['state'];path,ack,nonce=control_paths(state)
    if tree['owner']['pid']!=tree['wrapper']['pid']:raise RuntimeError('Schema3 control requires its direct Python owner')
    receipt=json.loads(ack.read_text(encoding='utf-8'))
    if receipt.get('schema')!=1 or receipt.get('pid')!=tree['wrapper']['pid'] or receipt.get('nonce')!=nonce or receipt.get('status') not in ('armed','draining','drained'):
        raise RuntimeError('Control acknowledgement is not owned/ready')
    fresh=verify(cfg)
    if fresh['owner']!=tree['owner'] or fresh['wrapper']!=tree['wrapper']:raise RuntimeError('Owner identity changed before control request')
    temporary=path.with_name(path.name+f'.tmp-{os.getpid()}')
    temporary.write_text(json.dumps({'action':'drain_stop','nonce':nonce,'pid':tree['wrapper']['pid']}),encoding='utf-8')
    os.replace(temporary,path)
    captured={(r['pid'],r['created']):r for r in fresh['rows']}
    expected={Path(cfg['exe']).name.casefold(),Path(cfg['vision']['exe']).name.casefold()}
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        if same_process(tree['wrapper']):
            try:
                # Include later engine/vision children started by a call admitted just before the drain.
                for child in psutil.Process(tree['wrapper']['pid']).children(recursive=True):
                    row=identity(child,expected)
                    if row['name'].casefold() not in expected|{'conhost.exe','python.exe'}:raise RuntimeError('Unrecognized later child; no force stop')
                    captured[(row['pid'],row['created'])]=row
            except psutil.NoSuchProcess:pass
        if not any(same_process(row) for row in captured.values()):
            receipt=json.loads(ack.read_text(encoding='utf-8'))
            if receipt.get('schema')!=1 or receipt.get('pid')!=tree['wrapper']['pid'] or receipt.get('nonce')!=nonce or receipt.get('status')!='drained' or receipt.get('pending_inference')!=0:
                raise RuntimeError('Owner exited without a proved zero-pending drain')
            if any(c.status==psutil.CONN_LISTEN and c.laddr.port==PORT for c in psutil.net_connections(kind='tcp')):
                raise RuntimeError(f'Port{PORT} remains owned; no new launch')
            return {'status':'stopped','stopped':True,'drained_without_cancel':True,'captured_processes':len(captured)}
        time.sleep(.25)
    return {'status':'draining_pending','stopped':False,'fail_closed':True,'reason':'Accepted calls/process closure still pending; no cancel/terminate/kill'}


def http(cfg, path, body=None):
    headers = {'Host': f'127.0.0.1:{PORT}', 'Origin': BASE, 'Content-Type': 'application/json'}
    key = cfg.get('api_key')
    if isinstance(key, list):
        key = key[0] if key else ''
    if isinstance(key, str) and key.strip():
        headers['Authorization'] = 'Bearer ' + key.split(',')[0].strip()
    req = urllib.request.Request(BASE+path, data=json.dumps(body).encode() if body is not None else None,
                                 headers=headers, method='POST' if body is not None else 'GET')
    with urllib.request.urlopen(req, timeout=60 if body is not None else 10) as response:
        return json.load(response)


def idle(cfg):
    health, slots, status = http(cfg, '/health'), http(cfg, '/slots'), http(cfg, '/v1/status')
    if not isinstance(health, dict) or type(health.get('loaded')) is not bool:
        raise RuntimeError('Health loaded state is unknown; idle cannot be proven')
    if not isinstance(slots, list) or (health['loaded'] and not slots):
        raise RuntimeError('Slots are missing/empty for a loaded model; idle cannot be proven')
    if any(not isinstance(slot, dict) or type(slot.get('is_processing')) is not bool for slot in slots):
        raise RuntimeError('Slot processing state is unknown; idle cannot be proven')
    activity = status.get('activity') if isinstance(status, dict) else None
    in_flight = activity.get('in_flight') if isinstance(activity, dict) else None
    if type(in_flight) is not int or in_flight < 0:
        raise RuntimeError('Explicit activity.in_flight is missing/invalid; idle cannot be proven')
    return in_flight == 0 and not any(slot['is_processing'] for slot in slots)


def public_tree(tree):
    # No cmdlines, API keys, prompts or reasoning in output.
    return {'schema': tree['schema'], 'wrapper_pid': tree['wrapper']['pid'], 'owner_pid': tree['owner']['pid'],
            'processes': [{**{k:r.get(k) for k in ('pid','ppid','created','name','exe','restricted','native_child','console')},
                           'proof': ('owner_tree_name_parent_creation_only' if r.get('restricted') else
                                     'executable_command_parent_creation')}
                          for r in tree['rows']]}


def main():
    global PORT, BASE
    ap = argparse.ArgumentParser(description=__doc__)
    action = ap.add_mutually_exclusive_group(required=True)
    action.add_argument('--verify', action='store_true')
    action.add_argument('--stop', action='store_true')
    args = ap.parse_args()
    result = {'status': 'checking', 'stopped': False}
    try:
        if os.name == 'nt':
            state = json.loads(STATE.read_text(encoding='utf-8-sig'))
            if state.get('launcher', {}).get('broker') == 'PortableWindowsTaskScheduler' and state['launcher'].get('logon_type') == 'S4U':
                import runpy
                broker = runpy.run_path(str(ROOT/'tools/scheduler_control.py'))
                if not broker['task_context']():
                    return broker['dispatch']('--stop' if args.stop else '--verify')
        cfg = json.loads(CONFIG.read_text(encoding='utf-8-sig'))
        # Canonical portable config may keep paths relative to its project root.
        for container, key in ((cfg, 'exe'), (cfg, 'cwd'), (cfg['vision'], 'exe')):
            container[key] = str(local_path(container.get(key), 'config.' + key))
        if cfg.get('host') != '127.0.0.1' or type(cfg.get('port')) is not int or not 1024 <= cfg['port'] <= 65535:
            raise RuntimeError('Only a valid localhost profile is allowed')
        PORT = cfg['port']; BASE = f'http://127.0.0.1:{PORT}'
        tree = verify(cfg)
        result.update(public_tree(tree))
        health = http(cfg, '/health')  # API unavailable => fail closed, even with a live saved PID.
        if health.get('service') != 'strata' or health.get('model') != cfg['model_name']:
            raise RuntimeError('Live API identity mismatch')
        result['loaded'] = health.get('loaded')
        if not idle(cfg):
            result['status'] = 'not_idle'
            print(json.dumps(result))
            return 3
        if args.verify:
            result['status'] = 'verified_idle'
            print(json.dumps(result))
            return 0
        if tree['schema']==3:
            result.update(controlled_stop(tree,cfg))
            print(json.dumps(result))
            return 0 if result.get('stopped') else 5
        # /unload is not an admission barrier: a new request can autoload immediately.
        # Do not terminate an owner until an atomic drain has been reviewed and installed.
        result.update(status='atomic_drain_required', fail_closed=True,
                      reason='Upstream has no public atomic drain; controlled owner stop is required')
        print(json.dumps(result))
        return 4
    except Exception as exc:
        result.update(status='verification_or_stop_failed', error_type=type(exc).__name__,
                      error=str(exc), fail_closed=True)
        print(json.dumps(result))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
