"""Bounded GGUF v3 metadata inspection. Never maps or reads tensor payloads."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import struct,re

@dataclass(frozen=True)
class Tensor:
    name:str
    shape:tuple[int,...]
    type:int
    offset:int

class Header:
    LIMIT=256*1024*1024
    FORMATS={0:'B',1:'b',2:'H',3:'h',4:'I',5:'i',6:'f',7:'?',10:'Q',11:'q',12:'d'}
    def __init__(self,path):
        if Path(path).is_symlink():raise ValueError('Model symlinks are not accepted by this profile preflight')
        self.path=Path(path).resolve(strict=True)
        if not self.path.is_file() or self.path.is_symlink():raise ValueError('A regular local GGUF file is required')
        self.size=self.path.stat().st_size;self.metadata={};self.tensors={}
        with self.path.open('rb') as f:
            self._file=f
            magic,version,nt,nm=self._unpack('<IIQQ')
            if magic!=0x46554747 or version!=3:raise ValueError('Expected GGUF version 3')
            if nt>1_000_000 or nm>100_000:raise ValueError('GGUF header count exceeds the safety limit')
            for _ in range(nm):
                name=self._string(4096)
                if name in self.metadata:raise ValueError('Duplicate GGUF metadata key')
                typ,=self._unpack('<I');self.metadata[name]=self._value(typ)
            for _ in range(nt):
                name=self._string(4096);nd,=self._unpack('<I')
                if not 1<=nd<=4:raise ValueError('Invalid GGUF tensor rank')
                shape=self._unpack('<'+'Q'*nd);elements=1
                for n in shape:
                    elements*=n
                    if n<1 or elements>2**63-1:raise ValueError('Invalid GGUF tensor dimensions')
                typ,offset=self._unpack('<IQ')
                if name in self.tensors or offset>self.size:raise ValueError('Invalid GGUF tensor identity or offset')
                self.tensors[name]=Tensor(name,shape,typ,offset)
            alignment=self.metadata.get('general.alignment',32)
            if type(alignment) is not int or alignment<1 or alignment>65536 or alignment&(alignment-1):raise ValueError('Invalid GGUF alignment')
            self.data_start=(f.tell()+alignment-1)//alignment*alignment
            if self.data_start>self.size:raise ValueError('GGUF tensor directory is truncated')
        del self._file
    def _read(self,n):
        if n<0 or self._file.tell()+n>min(self.LIMIT,self.size):raise ValueError('GGUF metadata is too large or truncated')
        data=self._file.read(n)
        if len(data)!=n:raise ValueError('Truncated GGUF metadata')
        return data
    def _unpack(self,fmt):return struct.unpack(fmt,self._read(struct.calcsize(fmt)))
    def _string(self,limit=16*1024*1024):
        n,=self._unpack('<Q')
        if n>limit:raise ValueError('GGUF string exceeds the safety limit')
        return self._read(n).decode('utf8')
    def _value(self,typ):
        if typ==8:return self._string()
        if typ==9:
            element,n=self._unpack('<IQ')
            if n>2_000_000 or element==9:raise ValueError('Invalid GGUF metadata array')
            return [self._value(element) for _ in range(n)]
        if typ not in self.FORMATS:raise ValueError('Unknown GGUF metadata type')
        value,=self._unpack('<'+self.FORMATS[typ]);return value
    @property
    def architecture(self):
        value=self.metadata.get('general.architecture')
        if not isinstance(value,str) or not value:raise ValueError('Missing model architecture')
        return value
    def nextn(self):
        """Candidate tensor contract only; does not establish training or numerical qualification."""
        a=self.architecture;n=self.metadata.get(a+'.nextn_predict_layers',0)
        layers=self.metadata.get(a+'.block_count');embd=self.metadata.get(a+'.embedding_length')
        if type(n) is not int or n!=1 or type(layers) is not int or layers<n or type(embd) is not int or embd<1:return False
        p='blk.'+str(layers-n)+'.nextn.'
        shapes=[('eh_proj.weight',(2*embd,embd)),('enorm.weight',(embd,)),('hnorm.weight',(embd,))]
        if a=='qwen4exp':
            hc=self.metadata.get(a+'.hyper_connection.count');rank=self.metadata.get(a+'.hyper_connection.low_rank')
            if type(hc) is not int or not 2<=hc<=64 or type(rank) is not int or not 1<=rank<=hc*embd:return False
            shapes=[('eh_proj.weight',(2*embd,embd)),('enorm.weight',(embd,)),('hnorm.weight',(embd,hc)),
                ('hc_head_norm.weight',(embd,hc)),('hc_head_down.weight',(embd*hc,rank)),('hc_head_up.weight',(rank,embd*hc))]
        for name,shape in shapes:
            t=self.tensors.get(p+name)
            # The model loader explicitly accepts flattened HC norm tensors via TENSOR_ALLOW_RESHAPE.
            flattened=a=='qwen4exp' and name in ('hnorm.weight','hc_head_norm.weight') and t is not None and t.shape==(embd*hc,)
            if t is None or t.shape!=shape and not flattened:return False
        return True

class ModelHeader(Header):
    """Combine only canonical local split headers; never read model tensor payloads."""
    def __init__(self,path):
        super().__init__(path)
        count=self.metadata.get('split.count',1)
        if type(count) is not int or not 1<=count<=256:raise ValueError('Invalid GGUF shard count')
        self.shards=[self.path]
        if count==1:return
        match=re.fullmatch(r'(.+)-([0-9]{5})-of-([0-9]{5})\.gguf',self.path.name)
        if not match or int(match[2])!=1 or int(match[3])!=count or self.metadata.get('split.no')!=0:
            raise ValueError('Select the first canonical GGUF shard (-00001-of-xxxxx.gguf)')
        for i in range(1,count):
            other=Header(self.path.with_name(f'{match[1]}-{i+1:05d}-of-{count:05d}.gguf'))
            if other.metadata.get('split.count')!=count or other.metadata.get('split.no')!=i:raise ValueError('GGUF shard identity does not match')
            if other.metadata.get('general.architecture',self.architecture)!=self.architecture:raise ValueError('GGUF shard architecture does not match')
            for key in (self.architecture+'.embedding_length',self.architecture+'.block_count','tokenizer.ggml.tokens'):
                if key in other.metadata and other.metadata[key]!=self.metadata.get(key):raise ValueError('GGUF shard model/tokenizer metadata does not match')
            if self.tensors.keys() & other.tensors.keys():raise ValueError('Duplicate tensor across GGUF shards')
            self.tensors.update(other.tensors);self.shards.append(other.path)
            self.data_start+=other.data_start;self.size+=other.size
            if self.data_start>self.LIMIT:raise ValueError('Combined GGUF headers exceed the inspection limit')
        total=self.metadata.get('split.tensors.count')
        if total is not None and (type(total) is not int or total!=len(self.tensors)):raise ValueError('GGUF total tensor count does not match')

def compatible_head(target:Header,draft:Header):
    a=target.architecture
    if draft.architecture!=a or not draft.nextn():raise ValueError('Draft architecture or NextN tensor contract is incompatible')
    if target.metadata.get(a+'.embedding_length')!=draft.metadata.get(a+'.embedding_length'):raise ValueError('Draft embedding dimensions do not match')
    if a=='qwen4exp' and any(target.metadata.get(a+'.'+k)!=draft.metadata.get(a+'.'+k) for k in ('hyper_connection.count','hyper_connection.low_rank')):raise ValueError('Draft hyper-connection dimensions do not match')
    for key in ('tokenizer.ggml.tokens','tokenizer.ggml.merges','tokenizer.ggml.token_type'):
        if key not in target.metadata or target.metadata[key]!=draft.metadata.get(key):raise ValueError('Draft tokenizer does not match the target: '+key)
