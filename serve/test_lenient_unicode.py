"""CPU-only regression for malformed XML JSON arguments containing escaped surrogate pairs."""
import json,unittest
from serve.frontend import coerce_value,OutputParser
import serve.test_tool_routes as route_fixture
call=route_fixture.call

class LenientUnicode(unittest.TestCase):
 def test_pairs_are_unicode_scalars(self):
  for cp in [0x10000,0x1f600,0x1f642,0x10ffff,0x041f]:
   text=chr(cp);esc=json.dumps(text,ensure_ascii=True)
   for quote in [esc,"'"+esc[1:-1]+"'"]:
    for kind,raw,want in [('array','['+quote+',]',[text]),('object','{"v":'+quote+',}',{'v':text})]:
     with self.subTest(cp=cp,kind=kind):
      got=coerce_value(raw,kind);self.assertEqual(got,want);json.dumps(got,ensure_ascii=False).encode('utf-8')
 def test_unpaired_lenient_values_keep_safe_raw_text(self):
  for value in [r'["\ud800",]',r'["\udc00",]',r'["\ud800x",]',r'["\ud800\u0041",]',r'["\u0041\udc00",]']:
   with self.subTest(value=value):
    self.assertEqual(coerce_value(value,'array'),value)
    json.dumps(coerce_value(value,'array'),ensure_ascii=False).encode('utf-8')
 def test_declared_strings_and_unknown_names(self):
  for value in [r'["\ud83d\ude00",]',r'["\ud800",]','raw\ntext']:
   self.assertEqual(coerce_value(value,'string'),value)
  raw=call('unknown',todos=r'["\ud83d\ude00",]')
  for chunk in (1,7,len(raw)):
   p=OutputParser(thinking=False,tools=[{'name':'todo_write','parameters':{'properties':{'todos':{'type':'array'}}}}]);ev=[]
   for i in range(0,len(raw),chunk):ev+=p.feed(raw[i:i+chunk])
   ev+=p.finish();self.assertEqual([e for e in ev if e.kind=='tool_call'],[])
 def test_valid_json_unpaired_behavior_is_unchanged(self):
  for raw in [r'["\ud800"]',r'["\udc00"]']:
   self.assertEqual(coerce_value(raw,'array'),json.loads(raw))
 def test_all_mock_http_routes(self):
  routes=route_fixture.Routes()
  for raw,want in [(r'["\ud83d\ude00",]',['😀']),(r'["\ud800",]',r'["\ud800",]')]:
   routes.every_route('Plan.\n</think>\n\n'+call('todo_write',todos=raw),[('todo_write',{'todos':want})])
  literal=r'["\ud83d\ude00",]'
  routes.every_route('Plan.\n</think>\n\n'+call('write_file',path='x.txt',content=literal),[('write_file',{'path':'x.txt','content':literal})])
