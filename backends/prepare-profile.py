"""Prepare an isolated local-model profile. Never downloads weights, changes tasks or starts an API."""
from __future__ import annotations
import argparse,hashlib,json,os,pathlib,re,secrets,subprocess
from gguf_meta import Header,compatible_head

ARCHITECTURES={'glm5-next','glm-dsa','deepseek4','qwen35','qwen35moe'}
def prepare(model,engine,output,*,backend='cpu',draft=None,context=131072,port=8094,mtp='require',workers=14,device=None):
    model=pathlib.Path(model).resolve(strict=True);engine=pathlib.Path(engine).resolve(strict=True);output=pathlib.Path(output).absolute()
    if backend not in ('cpu','cuda','vulkan') or mtp not in ('require','off'):raise ValueError('Unknown backend or MTP policy')
    if draft and mtp=='off':raise ValueError('A draft model cannot be supplied with MTP off')
    if backend!='cpu' and (not isinstance(device,str) or not re.fullmatch(('Vulkan' if backend=='vulkan' else 'CUDA')+r'[0-9]+',device)):
        raise ValueError('Select the intended GPU explicitly with --device VulkanN or CUDA<N>; no automatic fallback onto the working P40')
    if type(port) is not int or not 1024<=port<=65535 or port in (8080,8093):raise ValueError('Choose a separate API port; 8080 and 8093 are reserved')
    if type(workers) is not int or not 1<=workers<=256:raise ValueError('Invalid CPU worker count')
    if output.exists():raise ValueError('Output directory already exists; existing profiles are never overwritten')
    header=Header(model);md=header.metadata;arch=header.architecture
    if arch not in ARCHITECTURES:raise ValueError('This model family is not reviewed by the optional backend profile builder')
    trained=md.get(arch+'.context_length')
    if type(context) is not int or context<64 or type(trained) is not int or context>trained:raise ValueError('Requested context exceeds the model metadata; RoPE is not changed automatically')
    if not engine.is_file():raise ValueError('A local reviewed engine executable is required')
    result=subprocess.run([str(engine),'--capabilities'],capture_output=True,text=True,encoding='utf8')
    if result.returncode or len(result.stdout)>16384:raise ValueError('Engine capability probe failed; no model or server was started')
    caps=json.loads(result.stdout);kind='ggml' if 'library_pin' in caps else 'poly'
    if caps.get('backend')!=backend or caps.get('model_downloads') is not False:raise ValueError('Engine backend or offline model policy does not match')
    if kind=='ggml' and arch=='glm5-next' and not caps.get('glm5_next'):raise ValueError('GLM5Next needs the separate model-library build; production GGML remains unchanged')
    if kind=='poly' and (backend!='cuda' or arch not in ('glm5-next','qwen35moe','deepseek4')):raise ValueError('This Poly architecture/backend combination is not reviewed')
    candidate=header
    if draft:
        draft=pathlib.Path(draft).resolve(strict=True);candidate=Header(draft);compatible_head(header,candidate)
        if draft==model:draft=None
    if mtp=='require':
        if caps.get('trained_mtp') is not True and arch not in caps.get('native_mtp_architectures',[]):raise ValueError('Engine has no native MTP graph for this family')
        if not candidate.nextn():raise ValueError('MTP_REQUIRED: compatible NextN tensors are absent; provide a matching local draft GGUF or explicitly use --mtp off')
    vocab=md.get('tokenizer.ggml.tokens');merges=md.get('tokenizer.ggml.merges');types=md.get('tokenizer.ggml.token_type')
    if md.get('tokenizer.ggml.model')!='gpt2' or not isinstance(vocab,list) or not vocab or not all(isinstance(t,str) for t in vocab) or len(set(vocab))!=len(vocab):raise ValueError('A complete supported BPE vocabulary is required')
    if not isinstance(merges,list) or not all(isinstance(t,str) for t in merges) or not isinstance(types,list) or len(types)!=len(vocab):raise ValueError('Tokenizer merge/type metadata is missing or inconsistent')
    template=md.get('tokenizer.chat_template')
    if not isinstance(template,str) or not template.strip():raise ValueError('The model must carry its own chat template; a Qwen template is not substituted')
    pre=md.get('tokenizer.ggml.pre','qwen35')
    if arch=='glm5-next' and pre not in ('glm4','glm5'):raise ValueError('Unexpected GLM5Next tokenizer metadata')
    if kind=='ggml':
        args=['--serve','--model',str(model),'--ctx-size',str(context),'--batch-size','512','--ubatch-size','512','--threads',str(workers),'--threads-batch',str(workers),
              '--gpu-layers','0' if backend=='cpu' else '-1','--fit-ctx',str(context),'--cache-type-k','f16','--cache-type-v','f16']
        args+=['--device','none' if backend=='cpu' else device]
        args+=['--fit','off'] if backend=='cpu' else ['--fit','on','--fit-target','1024']
        if mtp=='require':args+=['--require-mtp','--mtp-draft-tokens','2','--mtp-min-p','0.25']
        if draft:args+=['--model-draft',str(draft),'--device-draft','none','--gpu-layers-draft','0']
    else:
        args=['--serve','--model',str(model),'--max-context',str(context),'--threads',str(workers),'--window','3','--lookup','0','--kv-whole','--any-node','--tail-skip','0']
        args+=['--require-mtp'] if mtp=='require' else ['--no-draft']
        if draft:args+=['--draft-model',str(draft)]
    config={'engine_kind':kind,'backend':backend,'arch':arch,'model_name':arch+'-local','exe':str(engine),
      'cwd':str(output),'tokenizer':str(output/'tokenizer'),'args':args,'host':'127.0.0.1','port':port,
      'api_key':secrets.token_urlsafe(32),'mtp_policy':mtp,'env':{'STRATA_NO_CPU_PIN':'1','STRATA_ROUTE_TAIL_SKIP':'0'},
      'sampling':{'min_p':0.05,'temperature':1.0,'top_p':0.95,'top_k':64},'api_monitor':False}
    if kind=='poly':
        config['gpus']=[int(device[4:])];config['env']['CUDA_VISIBLE_DEVICES']=device[4:]
    output.mkdir(parents=True);tok=output/'tokenizer';tok.mkdir()
    (output/'.gitignore').write_text('*\n',encoding='utf8',newline='\n')
    def js(path,obj):path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
    js(tok/'vocab.json',{v:i for i,v in enumerate(vocab)});(tok/'merges.txt').write_text('\n'.join(merges),encoding='utf8',newline='\n')
    js(tok/'merges.json',merges)
    js(tok/'token_type.json',types);js(tok/'tokenizer.json',{'pre':pre,'special_ids':{k:v for k,v in md.items() if k.startswith('tokenizer.ggml.') and k.endswith('_token_id')}})
    (tok/'chat_template.jinja').write_text(template,encoding='utf8',newline='\n');js(output/'profile.json',config)
    report={'schema':1,'status':'prepared_not_launched','backend':backend,'device':device,'engine_kind':kind,'architecture':arch,'context':context,
      'kv_format':'f16','mtp_policy':mtp,'head_tensors_detected':candidate.nextn(),
      'external_head_device':'cpu' if kind=='ggml' and draft else None,
      'engine_sha256':hashlib.sha256(engine.read_bytes()).hexdigest(),'library_pin':caps.get('library_pin'),
      'model_downloads':False,'tasks_registered':False,'production_changed':False,'trained_model_qualified':False,
      'notes':'Local metadata and engine capability preflight only. No trained-model/GPU qualification or speed claim. Existing Qwen 128K/Q4 preset is unchanged.'}
    js(output/'preflight.json',report);return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--model',required=True);p.add_argument('--engine',required=True);p.add_argument('--output',required=True)
    p.add_argument('--backend',choices=('cpu','cuda','vulkan'),default='cpu');p.add_argument('--draft-model');p.add_argument('--context',type=int,default=131072)
    p.add_argument('--port',type=int,default=8094);p.add_argument('--workers',type=int,default=14);p.add_argument('--device');p.add_argument('--mtp',choices=('require','off'),default='require');a=p.parse_args()
    try:print(json.dumps(prepare(a.model,a.engine,a.output,backend=a.backend,draft=a.draft_model,context=a.context,port=a.port,mtp=a.mtp,workers=a.workers,device=a.device),ensure_ascii=False))
    except (OSError,ValueError) as e:p.exit(2,str(e)+'\n')
