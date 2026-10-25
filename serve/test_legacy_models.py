"""Offline GLM/DeepSeek family and OpenAI protocol checks, without learned weights or speed tests."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
import urllib.error
import urllib.request
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'tools')]
import strata_tokenizer as ST
from serve.glm import GlmOutputParser, to_glm_force
from serve.frontend import ChatTemplate, OutputParser, forced_call
from serve import frontend as F
from serve.server import ByteTokenizer, MockEngine, Service, serve
from serve.server import StrataEngine
from serve.server import apply_saved_tuning
from serve.dsml import DsmlOutputParser,to_ds4_force
from serve.model_backends import checked_bind

TOOLS=[{'name':'files.write','parameters':{'type':'object','properties':{
 'path':{'type':'string'},'n':{'type':'integer'},'content':{'type':'string'}}}}]
VALUE='a literal </tool_call> and </arg_value>\nend'
BODY='files__write<arg_key>path</arg_key><arg_value>doc.md</arg_value><arg_key>n</arg_key><arg_value>3</arg_value><arg_key>content</arg_key><arg_value>'+VALUE+'</arg_value>'

class Parser(unittest.TestCase):
 def tearDown(self):F.use_family(None)
 def events(self,text,step=1,thinking=False,tools=TOOLS,stream=True):
  p=GlmOutputParser(thinking=thinking,tools=tools,stream_tools=stream,declared_only=True)
  events=[]
  for i in range(0,len(text),step):events+=p.feed(text[i:i+step])
  return events+p.finish('stop')
 def test_chunks_alias_and_literal_tags(self):
  for step in (1,2,7,10000):
   for stream in (False,True):
    with self.subTest(step=step,stream=stream):
     ev=self.events('analysis</think>Answer\n<tool_call>'+BODY+'</tool_call>',step,True,stream=stream)
     calls=[x.call for x in ev if x.kind=='tool_call'];self.assertEqual(len(calls),1)
     self.assertEqual(calls[0].name,'files.write');self.assertEqual(calls[0].arguments,{'path':'doc.md','n':3,'content':VALUE})
     self.assertEqual(''.join(x.text for x in ev if x.kind=='reasoning'),'analysis')
     self.assertEqual(''.join(x.text for x in ev if x.kind=='content'),'Answer')
     if stream:
      args=''.join(x.text for x in ev if x.kind=='tool_args');self.assertEqual(json.loads(args),calls[0].arguments)
 def test_zero_arguments(self):
  for step in (1,1000):
   ev=self.events('<tool_call>files.write</tool_call>',step)
   self.assertEqual([x.call.arguments for x in ev if x.kind=='tool_call'],[{}])
 def test_no_undeclared_events(self):
  for tools in ([],TOOLS):
   ev=self.events('<tool_call>unregistered<arg_key>x</arg_key><arg_value>1</arg_value></tool_call>',tools=tools)
   self.assertFalse(any(x.kind.startswith('tool_') for x in ev))
 def test_ambiguous_alias_not_authorized(self):
  tools=[{'name':'one.write'},{'name':'two.write'}]
  ev=self.events('<tool_call>write</tool_call>',tools=tools)
  self.assertFalse(any(x.kind.startswith('tool_') for x in ev))
 def test_quoted_and_fenced_examples_are_text(self):
  for text in ('Example `<tool_call>'+BODY+'</tool_call>`.', '```xml\n<tool_call>'+BODY+'</tool_call>\n```'):
   ev=self.events(text);self.assertFalse(any(x.kind.startswith('tool_') for x in ev))
 def test_reasoning_call_rescue_and_quote(self):
  text='<tool_call>'+BODY+'</tool_call></think>'
  self.assertEqual(len([x for x in self.events(text,thinking=True) if x.kind=='tool_call']),1)
  text='An example is `<tool_call>'+BODY+'</tool_call>`.</think>Answer'
  self.assertFalse(any(x.kind.startswith('tool_') for x in self.events(text,thinking=True)))
 def test_duplicate_arguments_fail(self):
  with self.assertRaises(ValueError):self.events('<tool_call>files.write<arg_key>n</arg_key><arg_value>1</arg_value><arg_key>n</arg_key><arg_value>2</arg_value></tool_call>')
 def test_think_end_after_quote(self):
  ev=self.events('I will say "Paris."</think>Paris',thinking=True)
  self.assertEqual(''.join(x.text for x in ev if x.kind=='content'),'Paris')
 def test_truncated_call_is_never_completed(self):
  for stream in (False,True):
   p=GlmOutputParser(thinking=False,tools=TOOLS,stream_tools=stream,declared_only=True)
   ev=p.feed('<tool_call>files.write<arg_key>content</arg_key><arg_value>unfinished')+p.finish('length')
   self.assertFalse(any(x.kind=='tool_call' for x in ev))
 def test_force_uses_native_spelling(self):
  f=forced_call({'type':'function','function':{'name':'files.write'}},TOOLS)
  self.assertEqual(to_glm_force(f),'<tool_call>files.write\n')
 def test_qwen_marker_unchanged(self):
  p=OutputParser(thinking=False,tools=TOOLS,declared_only=True)
  ev=p.feed('<tool_call><function=files__write><parameter=n>3</parameter></function></tool_call>')+p.finish()
  self.assertEqual([x.call.name for x in ev if x.kind=='tool_call'],['files.write'])
 def test_effort_words_do_not_leak_between_families(self):
  F.use_family('glm');self.assertEqual(F.effort_kwargs('high'),{'enable_thinking':True})
  self.assertEqual(F.effort_kwargs('none'),{'enable_thinking':False})
  F.use_family(None);self.assertEqual(F.effort_kwargs('high'),{'reasoning_effort':'xhigh'})
 def test_optional_sampler_preserves_explicit_zero(self):
  obj=object.__new__(StrataEngine);obj.info={'engine_kind':'ggml'}
  values={'temperature':0,'top_p':1,'min_p':0,'top_k':0,'seed':0}
  keys=obj.request_sampling(values)
  for value in ('temperature=0.0','top_p=1.0','min_p=0.0','top_k=0','seed=0'):self.assertIn(value,keys)
  obj.info={};self.assertEqual(obj.request_sampling(values),StrataEngine.sampling_keys(values))
  del obj.info;self.assertEqual(obj.request_sampling(values),StrataEngine.sampling_keys(values))
 def test_profile_port_does_not_fall_back_to_OWUI(self):
  self.assertEqual(checked_bind({'port':8094},8080,[]),8094)
  self.assertEqual(checked_bind({'port':8094},8095,['--port','8095']),8095)
  with self.assertRaises(ValueError):checked_bind({'port':8094},8080,['--port=8080'])
  with self.assertRaises(ValueError):checked_bind({'port':8093},8080,[])
  self.assertEqual(checked_bind({'port':8094},8093,['--port','8093']),8093)
 def test_native_presets_do_not_rewrite_optional_cli(self):
  cfg={'engine_kind':'ggml','args':['--model','local.gguf'],'env':{}}
  self.assertIs(apply_saved_tuning(cfg),cfg)

class Tokenizer(unittest.TestCase):
 def test_glm_three_digits_and_whole_piece(self):
  vocab=['1','2','3','4','5','12','123','45','a','b','ab'];merges=['1 2','12 3','4 5']
  glm=ST.Tokenizer(vocab,merges,pre='glm5');qwen=ST.Tokenizer(vocab,merges,pre='qwen35')
  self.assertEqual([vocab[i] for i in glm.encode('12345ab')],['123','45','ab'])
  self.assertEqual([vocab[i] for i in qwen.encode('12345ab')],['1','2','3','4','5','a','b'])
 def test_joyai_matches_deepseek_sequence(self):
  vocab=list(ST.bytes_to_unicode().values());a=ST.Tokenizer(vocab,[],pre='joyai-llm');b=ST.Tokenizer(vocab,[],pre='deepseek-v3')
  for text in ('12345 中文','Привет\n世界','x!=foo 1.5'):
   self.assertEqual(a.encode(text),b.encode(text));self.assertEqual(a.decode(a.encode(text)),text)

class DeepSeek(unittest.TestCase):
 def test_native_no_space_calls_alias_and_string_type(self):
  text='<｜DSML｜tool_calls><｜DSML｜invoke name="files__write"><｜DSML｜parameter name="n" string="true">123</｜DSML｜parameter></｜DSML｜invoke></｜DSML｜tool_calls>'
  for step in (1,7,10000):
   p=DsmlOutputParser(thinking=False,tools=TOOLS,stream_tools=True,declared_only=True);ev=[]
   for i in range(0,len(text),step):ev+=p.feed(text[i:i+step])
   ev+=p.finish();calls=[x.call for x in ev if x.kind=='tool_call']
   self.assertEqual([(x.name,x.arguments) for x in calls],[('files.write',{'n':'123'})])
   self.assertEqual(json.loads(''.join(x.text for x in ev if x.kind=='tool_args')),{'n':'123'})
 def test_forced_prefix_preserves_v4_spelling(self):
  f=forced_call({'type':'function','function':{'name':'files.write'}},TOOLS)
  self.assertEqual(to_ds4_force(f),'<｜DSML｜tool_calls>\n<｜DSML｜invoke name="files.write">\n')
 def test_family_stop_ids_use_model_metadata(self):
  tok=ByteTokenizer();tok.pre='joyai-llm';tok.special_ids={'tokenizer.ggml.eos_token_id':2,'tokenizer.ggml.eom_token_id':1000}
  s=Service(MockEngine(tok,'x'),tok,ChatTemplate(ROOT/'serve/chat_template.jinja'));s.set_family(None)
  self.assertEqual(s.family,'deepseek4');self.assertEqual(s.stop_ids,{2,1000});F.use_family(None)

class API(unittest.TestCase):
 def setUp(self):
  self.tok=ByteTokenizer();self.tok.pre='glm5'
  script='analysis</think>\n<tool_call>'+BODY+'</tool_call>'
  self.svc=Service(MockEngine(self.tok,script),self.tok,ChatTemplate(ROOT/'serve/chat_template.jinja'),model_name='synthetic-glm')
  self.svc.set_family(None);self.svc.api_key='unit-fixture-only'
  self.http=serve(self.svc,port=0);self.url='http://127.0.0.1:'+str(self.http.server_address[1])
 def tearDown(self):self.http.shutdown();self.http.server_close();F.use_family(None)
 def request(self,path,body=None,auth=True):
  headers={'Content-Type':'application/json'}
  if auth:headers['Authorization']='Bearer unit-fixture-only'
  req=urllib.request.Request(self.url+path,data=json.dumps(body).encode() if body is not None else None,headers=headers)
  return urllib.request.urlopen(req,timeout=10)
 def body(self,stream=False):return {'model':'synthetic-glm','messages':[{'role':'user','content':'test'}],
  'tools':[{'type':'function','function':TOOLS[0]}],'max_tokens':500,'stream':stream}
 def test_chat_completions(self):
  with self.request('/v1/chat/completions',self.body()) as r:data=json.load(r)
  msg=data['choices'][0]['message'];call=msg['tool_calls'][0]['function']
  self.assertEqual(call['name'],'files.write');self.assertEqual(json.loads(call['arguments'])['content'],VALUE)
  self.assertEqual(msg.get('reasoning_content'),'analysis')
 def test_streamed_calls(self):
  with self.request('/v1/chat/completions',self.body(True)) as r:lines=r.read().decode().splitlines()
  events=[json.loads(x[6:]) for x in lines if x.startswith('data: ') and x[6:]!='[DONE]']
  calls=[c for x in events for choice in x.get('choices',[]) for c in choice.get('delta',{}).get('tool_calls',[])]
  self.assertTrue(calls);self.assertEqual(json.loads(''.join(c.get('function',{}).get('arguments','') for c in calls))['n'],3)
 def test_auth_remains_required(self):
  with self.assertRaises(urllib.error.HTTPError) as e:self.request('/v1/chat/completions',self.body(),False)
  self.assertEqual(e.exception.code,401)
 def test_models_route(self):
  with self.request('/v1/models') as r:data=json.load(r)
  self.assertEqual(data['data'][0]['id'],'synthetic-glm')
 def test_responses_tool_calls(self):
  body={'model':'synthetic-glm','input':'test','tools':[{'type':'function',**TOOLS[0]}],'max_output_tokens':500}
  with self.request('/v1/responses',body) as r:data=json.load(r)
  calls=[x for x in data['output'] if x['type']=='function_call']
  self.assertEqual(calls[0]['name'],'files.write');self.assertEqual(json.loads(calls[0]['arguments'])['content'],VALUE)
 def test_named_choice_seeds_native_prefix(self):
  tail=BODY[BODY.index('<arg_key>'):]+'</tool_call>'
  self.svc.engine=MockEngine(self.tok,tail)
  body=self.body();body['reasoning_effort']='none';body['tool_choice']={'type':'function','function':{'name':'files.write'}}
  with self.request('/v1/chat/completions',body) as r:data=json.load(r)
  self.assertEqual(data['choices'][0]['message']['tool_calls'][0]['function']['name'],'files.write')

if __name__=='__main__':unittest.main()
