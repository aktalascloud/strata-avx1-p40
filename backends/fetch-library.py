"""Fetch the fixed official model-library source, excluding all model/weight blobs."""
import argparse,json,os,pathlib,shutil,subprocess
REPOSITORY='https://github.com/ggml-org/llama.cpp.git'
PIN='b9acf138a1e28ce1fc23b5a4fc4b12444b50f7ea'
def fetch(output,*,resume=False,plan=False):
    output=pathlib.Path(output).absolute()
    if plan:return dict(repository=REPOSITORY,pin=PIN,source_only=True,model_downloads=False,writes=False)
    exe=shutil.which('git')
    if not exe:raise ValueError('Git is required for the pinned source checkout')
    env=dict(os.environ,GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL=os.devnull,GIT_TERMINAL_PROMPT='0',GIT_LFS_SKIP_SMUDGE='1')
    def git(*args):
        q=subprocess.run([exe,'-c','core.hooksPath='+os.devnull,'-c','core.autocrlf=false',*map(str,args)],env=env,capture_output=True,text=True,encoding='utf8')
        if q.returncode:raise RuntimeError(q.stderr[-800:])
        return q.stdout.strip()
    marker=output/'.git/strata-model-source.json'
    if output.exists():
        if not resume or not marker.is_file():raise ValueError('Existing directory is preserved; --resume requires this downloader\'s source marker')
        state=json.loads(marker.read_text(encoding='utf8'))
        if state.get('repository')!=REPOSITORY or state.get('pin')!=PIN or git('-C',output,'remote','get-url','origin')!=REPOSITORY:
            raise ValueError('Source resume identity mismatch')
        if state.get('ready'):
            if git('-C',output,'rev-parse','HEAD')!=PIN or git('-C',output,'status','--porcelain'):
                raise ValueError('Existing source edits must be reviewed, not overwritten')
            return dict(repository=REPOSITORY,pin=PIN,source_ready=True,model_downloads=False,unchanged=True)
    else:
        git('clone','--filter=blob:none','--no-checkout','--depth=1',REPOSITORY,output)
        marker.write_text(json.dumps(dict(repository=REPOSITORY,pin=PIN,ready=False)),encoding='utf8')
    git('-C',output,'sparse-checkout','init','--no-cone')
    patterns=['/CMakeLists.txt','/LICENSE','/README.md','/cmake/','/src/','/include/','/common/','/ggml/','/vendor/']
    for suffix in ('gguf','bin','safetensors','pt','pth','onnx','npy','npz','h5','hdf5','bf16','f16','fp4','xq','exe','dll','lib','pdb','a','so','zip','7z','tar','gz','xz','png','jpg','jpeg','webp','pdf'):
        patterns.append('!**/*.'+suffix)
    (output/'.git/info/sparse-checkout').write_text('\n'.join(patterns)+'\n',encoding='utf8',newline='\n')
    git('-C',output,'fetch','--filter=blob:none','--depth=1','origin',PIN)
    git('-C',output,'checkout','--detach',PIN)
    if git('-C',output,'rev-parse','HEAD')!=PIN or git('-C',output,'status','--porcelain'):
        raise ValueError('Pinned source must be unchanged')
    marker.write_text(json.dumps(dict(repository=REPOSITORY,pin=PIN,ready=True)),encoding='utf8')
    return dict(repository=REPOSITORY,pin=PIN,source_ready=True,model_downloads=False)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',default=str(pathlib.Path(__file__).resolve().parent/'.deps-models'))
    p.add_argument('--resume',action='store_true');p.add_argument('--plan',action='store_true');a=p.parse_args()
    try:print(json.dumps(fetch(a.output,resume=a.resume,plan=a.plan)))
    except (OSError,ValueError,RuntimeError) as e:p.exit(2,str(e)+'\n')
