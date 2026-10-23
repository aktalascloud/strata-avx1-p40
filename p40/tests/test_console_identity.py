"""Pure identity-policy tests; never starts/stops a service or sends HTTP."""
import copy,os,pathlib,runpy,unittest
R=pathlib.Path(__file__).resolve().parents[2]
M=runpy.run_path(str(R/'p40/tools/service-lifecycle.py'))
N=M['norm'];check=M['verified_console']
class ConsolePolicy(unittest.TestCase):
    def setUp(self):
        self.native={'pid':20,'ppid':10,'created':100.,'name':'strata.exe','exe':str(R/'runtime/engine/strata.exe'),'restricted':False}
        self.row={'pid':30,'ppid':20,'created':100.1,'name':'conhost.exe','exe':str(pathlib.Path(os.environ['SystemRoot'])/'System32/conhost.exe'),'cmd':['conhost.exe','0x4'],'restricted':False}
    def allow(self,row=None,parent=None):
        return check(row or self.row,10,[parent or self.native],{N(self.native['exe'])},{'strata.exe','strata-vision.exe'})
    def test_native_child(self):self.assertTrue(self.allow())
    def test_wrapper_child(self):r=copy.deepcopy(self.row);r['ppid']=10;self.assertTrue(self.allow(r))
    def test_wrong_exe(self):r=copy.deepcopy(self.row);r['exe']=str(R/'conhost.exe');self.assertFalse(self.allow(r))
    def test_wrong_name(self):r=copy.deepcopy(self.row);r['name']='python.exe';self.assertFalse(self.allow(r))
    def test_extra_args(self):r=copy.deepcopy(self.row);r['cmd']+=['extra'];self.assertFalse(self.allow(r))
    def test_wrong_mode(self):r=copy.deepcopy(self.row);r['cmd'][-1]='0x5';self.assertFalse(self.allow(r))
    def test_unknown_parent(self):r=copy.deepcopy(self.row);r['ppid']=99;self.assertFalse(self.allow(r))
    def test_restricted_console(self):r=copy.deepcopy(self.row);r['restricted']=True;self.assertFalse(self.allow(r))
    def test_restricted_parent(self):p=copy.deepcopy(self.native);p['restricted']=True;self.assertFalse(self.allow(parent=p))
    def test_parent_exe_mismatch(self):p=copy.deepcopy(self.native);p['exe']=str(R/'other.exe');self.assertFalse(self.allow(parent=p))
    def test_parent_name_mismatch(self):p=copy.deepcopy(self.native);p['name']='other.exe';self.assertFalse(self.allow(parent=p))
    def test_parent_born_later(self):r=copy.deepcopy(self.row);r['created']=99.;self.assertFalse(self.allow(r))
if __name__=='__main__':unittest.main()
