"""Offline installer tests: tiny local HTTP fixtures only, never a model or a Strata API request."""
import contextlib, hashlib, http.server, importlib.util, json, pathlib, tempfile, threading, unittest

P=pathlib.Path(__file__).resolve().parents[1]/'windows/installer.py'
spec=importlib.util.spec_from_file_location('public_installer',P);kit=importlib.util.module_from_spec(spec);spec.loader.exec_module(kit)
DATA=b'local resumable fixture, not model weights\n'*257

def entry():return dict(repo='public/test',revision='1'*40,remote='fixture.bin',size=len(DATA),sha256=hashlib.sha256(DATA).hexdigest())

@contextlib.contextmanager
def server(ignore_range=False):
    calls=[]
    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_GET(self):
            calls.append(self.headers.get('Range'))
            offset=int(self.headers.get('Range','bytes=0-').split('=')[1].split('-')[0])
            if offset and not ignore_range:
                self.send_response(206);self.send_header('Content-Range',f'bytes {offset}-{len(DATA)-1}/{len(DATA)}');body=DATA[offset:]
            else:self.send_response(200);body=DATA
            self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
    srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=srv.serve_forever,daemon=True);thread.start()
    try:yield f'http://127.0.0.1:{srv.server_port}/test',calls
    finally:srv.shutdown();thread.join(timeout=3);srv.server_close()

class InstallerTests(unittest.TestCase):
    def setUp(self):self.temp=tempfile.TemporaryDirectory();self.root=pathlib.Path(self.temp.name);self.target=self.root/'fixture.bin'
    def tearDown(self):self.temp.cleanup()
    def partial(self,count=137):
        p=self.target.with_name('fixture.bin.part');p.write_bytes(DATA[:count]);kit.atomic(p.with_name(p.name+'.json'),entry());return p
    def test_resume_is_byte_exact(self):
        self.partial()
        with server() as (url,calls):kit.fetch(entry(),self.target,url=url)
        self.assertEqual(calls,['bytes=137-']);self.assertEqual(self.target.read_bytes(),DATA)
    def test_receipt_reuse_sends_no_request(self):
        with server() as (url,calls):
            kit.fetch(entry(),self.target,url=url);kit.fetch(entry(),self.target,url=url)
        self.assertEqual(len(calls),1)
    def test_ignored_range_never_appends(self):
        p=self.partial();before=p.read_bytes()
        with server(ignore_range=True) as (url,calls):
            with self.assertRaisesRegex(RuntimeError,'ignored Range'):kit.fetch(entry(),self.target,url=url)
        self.assertEqual(p.read_bytes(),before);self.assertFalse(self.target.exists())
    def test_wrong_sha_keeps_partial_and_never_creates_final(self):
        e=entry();e['sha256']='0'*64
        with server() as (url,calls):
            with self.assertRaisesRegex(RuntimeError,'SHA-256 mismatch'):kit.fetch(e,self.target,url=url)
        self.assertFalse(self.target.exists());self.assertEqual(self.target.with_name('fixture.bin.part').read_bytes(),DATA)
    def test_provenance_mismatch_stops_before_network(self):
        p=self.partial();e=entry();e['revision']='2'*40
        with server() as (url,calls):
            with self.assertRaisesRegex(RuntimeError,'provenance mismatch'):kit.fetch(e,self.target,url=url)
        self.assertEqual(calls,[]);self.assertEqual(p.stat().st_size,137)
    def test_corrupt_final_is_not_overwritten(self):
        self.target.write_bytes(b'bad')
        with server() as (url,calls):
            with self.assertRaisesRegex(RuntimeError,'Existing final'):kit.fetch(entry(),self.target,url=url)
        self.assertEqual(calls,[]);self.assertEqual(self.target.read_bytes(),b'bad')
    def test_oversized_partial_is_preserved(self):
        p=self.partial();p.write_bytes(DATA+b'extra')
        with server() as (url,calls):
            with self.assertRaisesRegex(RuntimeError,'Oversized'):kit.fetch(entry(),self.target,url=url)
        self.assertEqual(calls,[]);self.assertEqual(p.read_bytes(),DATA+b'extra')
    def test_bundle_traversal_rejected(self):
        kit.atomic(self.root/'bundle-manifest.json',dict(files=[dict(path='../outside',bytes=1,sha256='0'*64)]))
        with self.assertRaisesRegex(RuntimeError,'Unsafe bundle path'):kit.check_bundle(self.root)
    def test_generated_preset_has_no_authentication_material(self):
        manifest=dict(files=[dict(kind='model',name='one.gguf'),dict(kind='model',name='two.gguf'),dict(kind='vision',name='vision.gguf')])
        cfg=kit.make_config(self.root,self.root/'models',manifest,14,'0')
        self.assertFalse(any(k in cfg for k in ('api_key','token','password')))
        for flag,value in [('--max-context','131072'),('--kv','q4_0'),('--pool-workers','14'),('--spec','3'),('--spec-min-p','0.25'),('--ple-io','ram')]:self.assertEqual(cfg['args'][cfg['args'].index(flag)+1],value)
        self.assertFalse(cfg['vision']['gpu']);self.assertEqual(cfg['host'],'127.0.0.1');self.assertEqual(cfg['env']['STRATA_ROUTE_TAIL_SKIP'],'0')
    def test_separate_installation_port_and_paths_are_local(self):
        manifest=dict(files=[dict(kind='model',name='one.gguf'),dict(kind='model',name='two.gguf'),dict(kind='vision',name='vision.gguf')])
        cfg=kit.make_config(self.root,self.root/'models',manifest,14,'0',8094)
        self.assertEqual(cfg['port'],8094)
        for value in (cfg['exe'],cfg['cwd'],cfg['tokenizer'],cfg['log'],cfg['vision']['exe'],cfg['vision']['model'],cfg['vision']['mmproj']):
            self.assertTrue(pathlib.Path(value).is_relative_to(self.root))
        for flag in ('--pack','--native','--ple-gguf','--expert-profile','--mtp'):
            self.assertTrue(pathlib.Path(cfg['args'][cfg['args'].index(flag)+1]).is_relative_to(self.root))

if __name__=='__main__':unittest.main()
