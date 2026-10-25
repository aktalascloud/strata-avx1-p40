"""No learned weights, model downloads, tasks, live API or GPU access."""
import importlib.util,json,pathlib,struct,sys,tempfile,unittest
from unittest.mock import patch
from types import SimpleNamespace
B=pathlib.Path(__file__).resolve().parents[1];sys.path[:0]=[str(B),str(B/'tests')]
from gguf_meta import Header
from tiny_gguf import qwen35_mtp
spec=importlib.util.spec_from_file_location('profiles',B/'prepare-profile.py');profiles=importlib.util.module_from_spec(spec);spec.loader.exec_module(profiles)

class Profiles(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=pathlib.Path(self.temp.name);self.model=self.root/'tiny.gguf'
        writer=qwen35_mtp(self.model);writer.meta['tokenizer.chat_template']='{{ messages[0].content }}';writer.write();self.writer=writer
        self.engine=self.root/'engine.exe';self.engine.write_bytes(b'fixture-not-executed')
    def tearDown(self):self.temp.cleanup()
    def caps(self,backend='cpu'):
        return patch.object(profiles.subprocess,'run',return_value=SimpleNamespace(returncode=0,stdout=json.dumps({'backend':backend,'model_downloads':False,'trained_mtp':True,'glm5_next':True,'library_pin':'b9acf138a1e28ce1fc23b5a4fc4b12444b50f7ea'})))
    def test_profile_is_private_local_and_not_launched(self):
        out=self.root/'new'
        with self.caps() as capability_call:result=profiles.prepare(self.model,self.engine,out,context=256)
        self.assertEqual(capability_call.call_args.args[0],[str(self.engine),'--capabilities'])
        self.assertEqual(capability_call.call_count,1)
        self.assertEqual(result['status'],'prepared_not_launched');self.assertEqual((out/'.gitignore').read_text().strip(),'*')
        config=json.loads((out/'profile.json').read_text());self.assertIn('--require-mtp',config['args'])
        self.assertEqual(config['port'],8094);self.assertGreater(len(config['api_key']),32)
        self.assertFalse(result['tasks_registered']);self.assertFalse(result['production_changed'])
    def test_missing_head_fails_before_any_output(self):
        self.writer=qwen35_mtp(self.model,head=False);self.writer.meta['tokenizer.chat_template']='x';self.writer.write()
        with self.caps(),self.assertRaisesRegex(ValueError,'MTP_REQUIRED'):profiles.prepare(self.model,self.engine,self.root/'missing',context=256)
        self.assertFalse((self.root/'missing').exists())
    def test_reserved_ports_and_context_do_not_write(self):
        for kw in ({'port':8080},{'port':8093},{'context':257}):
            with self.assertRaises(ValueError):profiles.prepare(self.model,self.engine,self.root/'bad',context=kw.pop('context',256),**kw)
        self.assertFalse((self.root/'bad').exists())
    def test_output_is_never_overwritten(self):
        out=self.root/'existing';out.mkdir();(out/'keep').write_text('keep')
        with self.assertRaises(ValueError):profiles.prepare(self.model,self.engine,out,context=256)
        self.assertEqual((out/'keep').read_text(),'keep')
    def test_gpu_device_must_be_explicit(self):
        with self.assertRaisesRegex(ValueError,'explicitly'):profiles.prepare(self.model,self.engine,self.root/'gpu',backend='vulkan',context=256)
        with self.caps('vulkan'):result=profiles.prepare(self.model,self.engine,self.root/'gpu',backend='vulkan',device='Vulkan1',context=256)
        cfg=json.loads((self.root/'gpu/profile.json').read_text());self.assertIn('Vulkan1',cfg['args']);self.assertEqual(result['device'],'Vulkan1')
    def test_malformed_header_counts_are_bounded(self):
        self.model.write_bytes(struct.pack('<IIQQ',0x46554747,3,2**63,0))
        with self.assertRaisesRegex(ValueError,'count'):Header(self.model)
    def test_duplicate_tensor_is_rejected(self):
        self.writer.tensors.append(self.writer.tensors[0]);self.writer.write()
        with self.assertRaisesRegex(ValueError,'identity'):Header(self.model)
    def test_wrong_head_shape_is_rejected(self):
        import numpy as np
        self.writer.tensors=[(n,np.zeros((32,32),dtype=np.float32) if n.endswith('eh_proj.weight') else x) for n,x in self.writer.tensors];self.writer.write()
        self.assertFalse(Header(self.model).nextn())
    def test_metadata_reads_stop_before_payload(self):
        header=Header(self.model);self.assertLess(header.data_start,self.model.stat().st_size)
        self.assertTrue(header.nextn());self.assertEqual(header.architecture,'qwen35')
        original=pathlib.Path.open;limit=header.data_start;read_bytes=[]
        class Guard:
            def __init__(self,f):self.f=f
            def __enter__(self):return self
            def __exit__(self,*args):self.f.close()
            def tell(self):return self.f.tell()
            def read(self,n):
                if self.f.tell()+n>limit:raise AssertionError('Tensor payload was read')
                read_bytes.append(n);return self.f.read(n)
        def guarded(path,*args,**kwargs):return Guard(original(path,*args,**kwargs))
        with patch.object(pathlib.Path,'open',guarded):Header(self.model)
        self.assertGreater(sum(read_bytes),0);self.assertLessEqual(sum(read_bytes),limit)

if __name__=='__main__':unittest.main()
