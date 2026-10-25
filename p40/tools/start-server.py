"""Start the local source snapshot; a nonce control file drains accepted calls before normal shutdown."""
from __future__ import annotations
import _thread,argparse,ast,datetime,hashlib,importlib,json,os,re,sys,threading,time
from pathlib import Path
from urllib.parse import urlsplit

def control_handler(base,service):
    """Count the other POST operations too; inference keeps its original admission/queue limit."""
    class DrainAwareHandler(base):
        def do_POST(self):
            if urlsplit(self.path).path in ('/v1/chat/completions','/v1/messages','/v1/responses'):
                return super().do_POST()
            with service.admission_changed:
                rejected=service.draining
                if not rejected:service._local_control_pending+=1
            if rejected:
                self._json(503,{'error':{'type':'server_error','code':'server_draining',
                                        'message':'This instance is draining; retry later'}},retry_after=1)
                return
            try:return super().do_POST()
            finally:
                with service.admission_changed:
                    service._local_control_pending-=1
                    service.admission_changed.notify_all()
    return DrainAwareHandler

def atomic_json(path,value):
    temporary=path.with_name(path.name+f'.tmp-{os.getpid()}')
    temporary.write_text(json.dumps(value,indent=2),encoding='utf-8')
    os.replace(temporary,path)

def source_review(root,source):
    reviewed=json.loads((root/'tools/service-control-review.json').read_text(encoding='utf-8-sig'))
    raw=(source/'serve/server.py').read_bytes()
    if (reviewed.get('schema')!=1 or reviewed.get('semantic_reviewed') is not True or
            type(reviewed.get('guarded_wait_line')) is not int or reviewed['guarded_wait_line']<1 or
            hashlib.sha256(raw).hexdigest()!=reviewed.get('server_sha256')):
        raise SystemExit('Source changed: review admission/drain/main contracts before using schema3 control')
    main=next(n for n in ast.parse(raw.decode('utf-8-sig')).body if isinstance(n,ast.FunctionDef) and n.name=='main')
    protected={n.lineno for block in main.body if isinstance(block,ast.Try) and block.finalbody
               for statement in block.body for n in ast.walk(statement) if isinstance(n,ast.Call)
               and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name)
               and n.func.value.id=='time' and n.func.attr=='sleep'}
    if reviewed['guarded_wait_line'] not in protected:raise SystemExit('Control gate is outside the protected main loop')
    return reviewed

def control_paths(root,value,nonce):
    if not re.fullmatch(r'[0-9a-f]{64}',nonce):raise ValueError('Invalid control nonce')
    folder=(root/'runtime/state').resolve(strict=True)
    path=Path(value).resolve()
    if path.parent!=folder or path.name!='control-'+nonce+'.json':raise ValueError('Control path is outside this launch state')
    return path,path.with_suffix('.ack.json')

def valid_request(path,nonce,pid):
    try:
        value=json.loads(path.read_text(encoding='utf-8'))
        return value.get('action')=='drain_stop' and value.get('nonce')==nonce and value.get('pid')==pid
    except (OSError,ValueError,AttributeError):return False

def main_location(code):
    frame=sys._current_frames().get(threading.main_thread().ident)
    while frame is not None:
        if frame.f_code is code:return frame.f_lineno
        frame=frame.f_back
    return None

def await_guarded(location,line):
    # The reviewed main first binds HTTP, then enters its shutdown-protected wait loop.
    while True:
        current=location()
        if current is None or current>line:return False
        if current==line:return True
        time.sleep(.01)

def drain_service(service,publish,interrupt):
    pending=service.begin_drain()  # Official admission lock closes before observing existing calls.
    if type(pending) is not int or pending<0:raise RuntimeError('Unknown admission state')
    with service.admission_changed:controls=service._local_control_pending
    publish('draining',pending+controls)
    while True:
        pending=service.wait_for_drain(1.0)
        if type(pending) is not int or pending<0:raise RuntimeError('Unknown drain state')
        with service.admission_changed:
            controls=service._local_control_pending
            if pending==0 and controls==0:break
            if pending==0:service.admission_changed.wait(1.0)
        publish('draining',pending+controls)
    publish('drained',0)
    interrupt()  # Normal server.main finally; no cancellation/terminate/kill.

def watch_control(service,path,ack,nonce,pid,location,guarded_line):
    def publish(status,pending):
        atomic_json(ack,{'schema':1,'pid':pid,'nonce':nonce,'status':status,'pending_inference':pending,
                         'updated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
    publish('starting',0)
    if not await_guarded(location,guarded_line):return
    publish('armed',0)
    while not valid_request(path,nonce,pid):time.sleep(.25)
    def interrupt():
        if await_guarded(location,guarded_line):_thread.interrupt_main()
    try:drain_service(service,publish,interrupt)
    except BaseException as exc:
        atomic_json(ack,{'schema':1,'pid':pid,'nonce':nonce,'status':'control_failed',
                         'error_type':type(exc).__name__})

def main():
    options=argparse.ArgumentParser()
    options.add_argument('--source',required=True);options.add_argument('--config',required=True)
    options.add_argument('--control-path',required=True);options.add_argument('--control-nonce',required=True)
    args=options.parse_args()
    root=Path(__file__).resolve().parents[1]
    source,config=Path(args.source).resolve(),Path(args.config).resolve()
    if not source.is_relative_to(root) or not config.is_relative_to(root):raise SystemExit('Source/config must stay inside this project')
    settings=json.loads(config.read_text(encoding='utf-8-sig'))
    port=settings.get('port',8093)
    if settings.get('host','127.0.0.1')!='127.0.0.1' or type(port) is not int or not 1024<=port<=65535:
        raise SystemExit('Expected a valid localhost port in this installation config')
    path,ack=control_paths(root,args.control_path,args.control_nonce)
    if path.exists() or ack.exists():raise SystemExit('Control path already exists; use a new launch nonce')
    reviewed=source_review(root,source)
    server_file=source/'serve/server.py'
    mutable=(root/'upstream').resolve()
    sys.path=[str(source)]+[value for value in sys.path if Path(value).resolve()!=mutable]
    os.chdir(source);os.environ['PYTHONNOUSERSITE']='1';os.environ['OMP_PROC_BIND']='FALSE'
    # Private bundle runtime directories only; no global PATH or driver changes.
    runtime=(root/'runtime').resolve(strict=True)
    binaries=[runtime/'engine',runtime/'vision']
    for folder in sorted((runtime/'backends').glob('*')) if (runtime/'backends').is_dir() else []:
        if folder.is_symlink() or not folder.resolve().is_relative_to(runtime):raise SystemExit('Unsafe backend runtime directory')
        if folder.is_dir():binaries.append(folder)
    os.environ['PATH']=os.pathsep.join(map(str,binaries))+os.pathsep+os.environ.get('PATH','')
    server=importlib.import_module('serve.server')
    if Path(server.__file__).resolve()!=server_file:raise SystemExit('Unexpected serving module path')
    original=server.Service
    for name in ('begin_drain','wait_for_drain'):
        if not callable(getattr(original,name,None)):raise SystemExit('Reviewed drain methods unavailable')
    captured=[]
    class ControlledService(original):
        def __init__(self,*positional,**keywords):
            super().__init__(*positional,**keywords)
            if captured:raise RuntimeError('Schema3 control supports one Service instance only')
            self._local_control_pending=0
            captured.append(self)
            threading.Thread(target=watch_control,args=(self,path,ack,args.control_nonce,os.getpid(),
                             lambda:main_location(server.main.__code__),reviewed['guarded_wait_line']),
                             name='strata-local-drain-control',daemon=True).start()
    server.Service=ControlledService
    make_handler=server.make_handler
    server.make_handler=lambda service:control_handler(make_handler(service),service)
    return server.main(['--engine','strata','--config',str(config),'--host','127.0.0.1','--port',str(port),
                        '--offline','--shutdown-timeout','300'])

if __name__=='__main__':raise SystemExit(main())
