"""Install this public, weights-free distribution. No credentials, global environment edits or server start."""
from __future__ import annotations
import argparse, contextlib, datetime, hashlib, json, os, pathlib, shutil, subprocess, sys, time
import http.client, urllib.error, urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[2]

def sha(path):
    h = hashlib.sha256()
    with pathlib.Path(path).open('rb') as f:
        for block in iter(lambda: f.read(8 << 20), b''): h.update(block)
    return h.hexdigest()

def atomic(path, value):
    path = pathlib.Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.tmp')
    with tmp.open('w', encoding='utf8') as f:
        json.dump(value, f, indent=2); f.write('\n'); f.flush(); os.fsync(f.fileno())
    os.replace(tmp, path)

@contextlib.contextmanager
def install_lock(root):
    import msvcrt
    path = root / 'install.lock'
    with path.open('a+b') as f:
        f.seek(0)
        if not f.read(1): f.write(b'0'); f.flush()
        f.seek(0)
        try: msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError: raise RuntimeError('Another installer is active. Partial files are preserved.')
        try: yield
        finally: f.seek(0); msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)

def fetch(entry, target, *, url=None, attempts=8):
    """Never append a 200 response to a partial file; never accept wrong size/hash."""
    target = pathlib.Path(target); target.parent.mkdir(parents=True, exist_ok=True)
    part = target.with_name(target.name + '.part')
    provenance = part.with_name(part.name + '.json')
    receipt = target.with_name(target.name + '.verified.json')
    identity = {k: entry[k] for k in ('repo', 'revision', 'remote', 'size', 'sha256')}
    if target.exists():
        st = target.stat()
        old = json.loads(receipt.read_text()) if receipt.exists() else {}
        if old.get('identity') == identity and old.get('mtime_ns') == st.st_mtime_ns and st.st_size == entry['size']:
            print('Verified receipt:', target.name, flush=True); return target
        if st.st_size != entry['size'] or sha(target) != entry['sha256']:
            raise RuntimeError('Existing final file does not match; preserved: ' + target.name)
    else:
        if part.exists() and (not provenance.exists() or json.loads(provenance.read_text()) != identity):
            raise RuntimeError('Partial provenance mismatch; preserved: ' + part.name)
        atomic(provenance, identity)
        from urllib.parse import quote
        address = url or ('https://huggingface.co/' + entry['repo'] + '/resolve/' + entry['revision'] + '/' + quote(entry['remote'], safe='/') + '?download=true')
        for attempt in range(attempts):
            offset = part.stat().st_size if part.exists() else 0
            if offset > entry['size']: raise RuntimeError('Oversized partial file; preserved')
            if offset == entry['size']: break
            headers = {'User-Agent': 'Strata-AVX1-P40-public-installer/1'}
            if offset: headers['Range'] = f'bytes={offset}-'
            try:
                request = urllib.request.Request(address, headers=headers)
                with urllib.request.urlopen(request, timeout=90) as response:
                    status = response.status
                    if offset and status != 206: raise RuntimeError('Server ignored Range; partial preserved, never appended')
                    if status == 206:
                        content_range = response.headers.get('Content-Range', '')
                        import re
                        match = re.fullmatch(r'bytes (\d+)-(\d+)/(\d+)', content_range)
                        if not match or int(match[1]) != offset or int(match[3]) != entry['size']:
                            raise RuntimeError('Wrong Content-Range; partial preserved')
                    elif status != 200: raise RuntimeError('Unexpected HTTP status')
                    print(f'{target.name}: resume {offset:,}/{entry["size"]:,} bytes', flush=True)
                    with part.open('ab') as f:
                        sync_at = f.tell(); progress_at = sync_at
                        while True:
                            block = response.read(4 << 20)
                            if not block: break
                            if f.tell() + len(block) > entry['size']: raise RuntimeError('Response exceeds pinned size')
                            f.write(block)
                            if f.tell() - sync_at >= 32 << 20: f.flush(); os.fsync(f.fileno()); sync_at = f.tell()
                            if f.tell() - progress_at >= 256 << 20:
                                print(f'  {f.tell():,}/{entry["size"]:,}', flush=True); progress_at = f.tell()
                        f.flush(); os.fsync(f.fileno())
            except (urllib.error.URLError, OSError, TimeoutError, http.client.HTTPException) as error:
                if attempt + 1 == attempts: raise RuntimeError('Download paused; rerun INSTALL.cmd to resume') from error
                print('Connection interrupted; partial preserved, retrying.', flush=True)
                time.sleep(min(2 ** attempt, 30))
        if not part.exists() or part.stat().st_size != entry['size']: raise RuntimeError('Incomplete download; partial preserved')
        print('SHA-256:', target.name, flush=True)
        if sha(part) != entry['sha256']: raise RuntimeError('SHA-256 mismatch; partial preserved for inspection')
        os.replace(part, target)
    atomic(receipt, {'identity': identity, 'mtime_ns': target.stat().st_mtime_ns,
                     'verified_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()})
    return target

def check_bundle(root=ROOT):
    manifest = json.loads((root / 'bundle-manifest.json').read_text(encoding='utf8'))
    for row in manifest['files']:
        p = (root / row['path']).resolve()
        if not p.is_relative_to(root.resolve()) or p.is_symlink(): raise RuntimeError('Unsafe bundle path')
        if not p.is_file() or p.stat().st_size != row['bytes'] or sha(p) != row['sha256']:
            raise RuntimeError('Bundle hash mismatch: ' + row['path'])
    print(f'Bundle verified: {len(manifest["files"])} files; no model downloaded or server started.')
    return manifest

def make_config(root, models, manifest, workers, numa, port=8093):
    weights = [models / e['name'] for e in manifest['files'] if e['kind'] == 'model']
    projector = next(models / e['name'] for e in manifest['files'] if e['kind'] == 'vision')
    pack = root / 'packs/davidau-iq3_s'; mtp = root / 'mtp/rt'
    env = dict(STRATA_NO_CPU_PIN='1', STRATA_ROUTE_TAIL_SKIP='0', STRATA_WIN_NUMA_NODE=str(numa),
        STRATA_DENSE_F32='1', STRATA_IQ_STAGE_TABLES='1', STRATA_IQ_STAGE_GRID_MMVQ='1',
        STRATA_QFUSE='1', STRATA_GR_NORM_FAST='1', STRATA_B6_MMVQ_ROWS='1', STRATA_EXPDEC='1',
        STRATA_EXPDEC_R='1', STRATA_DF_BRANCH='0', STRATA_PCIE_BALANCE='0', STRATA_SIDE_MIXER='0')
    return dict(exe=str(root/'runtime/engine/strata.exe'), cwd=str(root/'app'), tokenizer=str(pack/'tokenizer'),
        args=['--pack',str(pack),'--native',str(weights[0]),'--ple-gguf',str(weights[1]),
              '--expert-profile',str(root/'app/data/expert-profile.bin'),'--expert-cache','auto',
              '--max-context','131072','--kv','q4_0','--prefill','512','--pool-workers',str(workers),
              '--spec','3','--spec-min-p','0.25','--prompt-cache','6','--prompt-cache-every','16384',
              '--prompt-cache-root','2048','--vision','--vram-reserve-mib','1216','--mtp',str(mtp),
              '--suffix-draft','0','--lookup-chain','0','--ple-io','ram','--adapt-async','1','--pool-tasks','0'],
        model_name='davidau-qwen3.8-flash-next-iq3_s',host='127.0.0.1',port=port,
        log=str(root/'logs/engine.log'),mtp=True,open_browser=False,env=env,
        reasoning_effort='high',sampling=dict(temperature=1.0,top_p=0.95,top_k=64,min_p=0.05,repetition_penalty=1.0),
        vision=dict(exe=str(root/'runtime/vision/strata-vision.exe'),model=str(weights[0]),mmproj=str(projector),
                    gpu=False,threads=8,max_tokens=300))

def install(args):
    root = ROOT; bundle = check_bundle(root)
    manifest = json.loads((root/'p40/model-downloads.json').read_text(encoding='utf8'))
    models = pathlib.Path(args.models_dir).expanduser().absolute() if args.models_dir else root/'models/DavidAU-Qwen3.8-IQ3_S'
    if (root/'strata-davidau.json').exists():
        print('Existing local configuration retained. Installer will not overwrite it.')
    (root/'logs').mkdir(exist_ok=True)
    needed = sum(e['size'] for e in manifest['files'])
    models.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(models).free < needed + (3 << 30):
        # Already downloaded data must not count against resumability.
        remaining = 0
        for e in manifest['files']:
            target = (root/'mtp/rt' if e['kind']=='mtp' else models)/e['name']
            p = target if target.exists() else target.with_name(target.name+'.part')
            remaining += max(0, e['size'] - (p.stat().st_size if p.exists() else 0))
        if shutil.disk_usage(models).free < remaining + (3 << 30): raise RuntimeError('Not enough disk space for remaining weights and local pack')
    with install_lock(root):
        for e in manifest['files']:
            if e['repo'] not in manifest['allowed_repositories'] or len(e['revision']) != 40:
                raise RuntimeError('Unpinned download repository/revision')
            target = (root/'mtp/rt' if e['kind']=='mtp' else models)/e['name']
            if pathlib.Path(e['name']).name != e['name']: raise RuntimeError('Unsafe download filename')
            fetch(e, target)
        pack = root/'packs/davidau-iq3_s'; ready = pack/'.ready.json'; owner = pack/'.installer-owner.json'
        fingerprint = sha(root/'p40/model-downloads.json')
        first = next(e['name'] for e in manifest['files'] if e['kind']=='model')
        reuse = False
        if ready.exists():
            old = json.loads(ready.read_text()); reuse = old.get('downloads_sha256') == fingerprint and len(old.get('files',{})) >= 9
            reuse = reuse and all((pack/n).is_file() and sha(pack/n)==h for n,h in old.get('files',{}).items())
        if not reuse:
            if pack.exists() and any(pack.iterdir()) and not owner.exists(): raise RuntimeError('Unowned pack directory; preserved')
            atomic(owner, {'schema':1,'downloads_sha256':fingerprint})
            command = [sys.executable,'-I','-s','-B',str(root/'app/tools/iq_pack.py'),'--gguf',str(models/first),'--out',str(pack)]
            print('Building your own dense/tokenizer pack directly from the selected GGUF. No original checkpoint.', flush=True)
            result = subprocess.run(command,cwd=root/'app')
            if result.returncode: raise RuntimeError('Pack preparation failed; weights are preserved')
            names = ['dense.bin','index.txt','native_experts.txt','conversions.json','tokenizer/vocab.json',
                     'tokenizer/merges.txt','tokenizer/token_type.json','tokenizer/tokenizer.json','tokenizer/chat_template.jinja']
            if not all((pack/n).is_file() and (pack/n).stat().st_size for n in names): raise RuntimeError('Incomplete pack')
            atomic(ready, {'downloads_sha256':fingerprint,'files':{n:sha(pack/n) for n in names}})
        path = root/'strata-davidau.json'
        if not path.exists(): atomic(path, make_config(root,models,manifest,args.workers,args.numa_node,args.port))
        atomic(root/'runtime/active.json',dict(id=bundle['release_tag'],source='app',engine='runtime/engine/strata.exe',vision='runtime/vision/strata-vision.exe',source_sha=bundle['source_sha']))
    port=json.loads(path.read_text(encoding='utf8'))['port']
    print(f'Ready. Run START.cmd. API: http://127.0.0.1:{port}/v1. No API key is shipped or required for this localhost preset.')
    print('NUMA preference:',args.numa_node,'; choose node0 only after confirming your GPU is local to it.')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--check-bundle',action='store_true',help='Verify package hashes only; no downloads, config edits or server')
    p.add_argument('--models-dir',help='Optional directory for GGUF/mmproj; default is inside the portable folder')
    p.add_argument('--workers',type=int,default=max(1,min(14,(os.cpu_count() or 2)-2)))
    p.add_argument('--port',type=int,default=8093,help='Local API port; choose a free port for a separate installation')
    p.add_argument('--numa-node',choices=['off','0','1'],default='off',help='Reference machine used node0; generic default leaves NUMA allocation unchanged')
    args=p.parse_args()
    if args.check_bundle: check_bundle(); return 0
    if os.name!='nt' or sys.maxsize<=2**32: p.error('Windows x64 required')
    if not 1<=args.workers<=256: p.error('workers must be1..256')
    if not 1024<=args.port<=65535: p.error('port must be1024..65535')
    install(args); return 0

if __name__=='__main__':
    try: raise SystemExit(main())
    except (RuntimeError,OSError,ValueError) as error:
        print('ERROR:',error,file=sys.stderr); raise SystemExit(1)
