"""Tiny random CPU protocol fixtures. These are not trained models or benchmarks."""
from pathlib import Path
import struct
import numpy as np

class TinyGGUF:
    def __init__(self,path):self.path=Path(path);self.meta={};self.tensors=[]
    def add_tensor(self,name,array):self.tensors.append((name,array))
    @staticmethod
    def string(s):
        value=s.encode('utf8');return struct.pack('<Q',len(value))+value
    @classmethod
    def value(cls,v):
        if isinstance(v,str):return 8,cls.string(v)
        if isinstance(v,bool):return 7,struct.pack('<?',v)
        if isinstance(v,float):return 6,struct.pack('<f',v)
        if isinstance(v,int):return 4,struct.pack('<I',v)
        if isinstance(v[0],bool):return 9,struct.pack('<IQ',7,len(v))+struct.pack('<'+'?'*len(v),*v)
        if isinstance(v[0],int):return 9,struct.pack('<IQ',5,len(v))+struct.pack('<'+'i'*len(v),*v)
        t=cls.value(v[0])[0];return 9,struct.pack('<IQ',t,len(v))+b''.join(cls.value(x)[1] for x in v)
    def write(self):
        header=struct.pack('<IIQQ',0x46554747,3,len(self.tensors),len(self.meta));data=bytearray()
        for k,v in self.meta.items():
            typ,value=self.value(v);header+=self.string(k)+struct.pack('<I',typ)+value
        for k,a in self.tensors:
            data.extend(bytes((-len(data))%32))
            header+=self.string(k)+struct.pack('<I',a.ndim)+struct.pack('<'+'Q'*a.ndim,*reversed(a.shape))+struct.pack('<IQ',0,len(data))
            data.extend(a.tobytes())
        self.path.write_bytes(header+bytes((-len(header))%32)+data)

def byte_tokens():
    raw=list(range(33,127))+list(range(161,173))+list(range(174,256));codes=raw[:];n=0
    for b in range(256):
        if b not in raw:raw.append(b);codes.append(256+n);n+=1
    return list(dict(zip(raw,map(chr,codes))).values())+['AB','<|bos|>','<|eos|>']

def qwen35_mtp(path, *, head=True, output_choices=None, predictor_mix=None, constant_tokens=False, context=256):
    """Recurrent + attention trunk blocks and an optional native NextN block."""
    w=TinyGGUF(path);arch='qwen35';rng=np.random.default_rng(123)
    w.meta={'general.architecture':arch,'general.name':'Synthetic untrained NextN fixture',
      arch+'.context_length':context,arch+'.embedding_length':32,arch+'.block_count':3 if head else 2,
      arch+'.feed_forward_length':64,arch+'.attention.head_count':4,arch+'.attention.head_count_kv':2,
      arch+'.attention.layer_norm_rms_epsilon':1e-5,arch+'.rope.freq_base':10000.,arch+'.rope.dimension_sections':[2,2,0,0],
      arch+'.ssm.conv_kernel':4,arch+'.ssm.inner_size':32,arch+'.ssm.state_size':8,
      arch+'.ssm.time_step_rank':4,arch+'.ssm.group_count':2,arch+'.full_attention_interval':2,
      arch+'.nextn_predict_layers':1 if head else 0,
      'tokenizer.ggml.model':'gpt2','tokenizer.ggml.pre':'gpt-2','tokenizer.ggml.tokens':byte_tokens(),
      'tokenizer.ggml.token_type':[1]*257+[3,3],'tokenizer.ggml.merges':['A B'],
      'tokenizer.ggml.bos_token_id':257,'tokenizer.ggml.eos_token_id':258,'tokenizer.ggml.add_bos_token':False}
    def tensor(name,shape,norm=False):
        w.add_tensor(name,np.ones(shape,dtype=np.float32) if norm else (rng.standard_normal(shape)*.02).astype(np.float32))
    if constant_tokens:w.add_tensor('token_embd.weight',np.full((259,32),.1,dtype=np.float32))
    else:tensor('token_embd.weight',(259,32))
    output=(rng.standard_normal((259,32))*.02).astype(np.float32)
    if output_choices is not None:output[output_choices:]=0
    if constant_tokens:output[:]=0;output[0]=.1
    w.add_tensor('output.weight',output);tensor('output_norm.weight',(32,),True)
    for layer in range(3 if head else 2):
        rows=[('attn_norm.weight',(32,)),('post_attention_norm.weight',(32,)),
          ('ffn_gate.weight',(64,32)),('ffn_up.weight',(64,32)),('ffn_down.weight',(32,64))]
        if layer==0:
            rows += [('attn_qkv.weight',(64,32)),('attn_gate.weight',(32,32)),('ssm_conv1d.weight',(64,4)),
              ('ssm_dt.bias',(4,)),('ssm_beta.weight',(4,32)),('ssm_alpha.weight',(4,32)),
              ('ssm_norm.weight',(8,)),('ssm_out.weight',(32,32))]
            w.add_tensor('blk.0.ssm_a',-np.ones((4,),dtype=np.float32))
        else:
            rows += [('attn_q_norm.weight',(8,)),('attn_k_norm.weight',(8,)),('attn_q.weight',(64,32)),
              ('attn_k.weight',(16,32)),('attn_v.weight',(16,32)),('attn_output.weight',(32,32))]
        for name,shape in rows:
            tensor('blk.'+str(layer)+'.'+name,shape,'norm' in name)
    if head:
        if predictor_mix is None:
            tensor('blk.2.nextn.eh_proj.weight',(32,64))
        else:
            projection=np.concatenate(((1-predictor_mix)*np.eye(32),predictor_mix*np.eye(32)),axis=1).astype(np.float32)
            w.add_tensor('blk.2.nextn.eh_proj.weight',projection)
        for name in ('enorm','hnorm','shared_head_norm'):tensor('blk.2.nextn.'+name+'.weight',(32,),True)
    w.write();return w
