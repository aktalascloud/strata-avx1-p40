"""Pinned build copies for Vulkan large views and bounded grammar/JSON recursion (MIT)."""
import argparse,hashlib,json,pathlib,re
PIN='b9acf138a1e28ce1fc23b5a4fc4b12444b50f7ea'
FILES={
 'src/llama-grammar.cpp':'97d76071a2ed1b0c4ce827f002f554b12a25593776adb525dde33ac4cb1eb1e9',
 'common/jinja/value.cpp':'14d98a60a2fcf71f84cac250ca6885187c940ec815859f7c398ca48f857e2d63',
 'ggml/src/ggml-vulkan/ggml-vulkan.cpp':'dd4eaec3c5843f687c930b20de500dd61b1b026f55c6b1fb49da9ec7790dd6bb'}
def replace(text,old,new):
 if text.count(old)!=1:raise ValueError('Model library compatibility anchor is not unique: '+old[:90])
 return text.replace(old,new)
def prepare(source,output):
 source=pathlib.Path(source).resolve(strict=True);output=pathlib.Path(output).resolve()
 if source==output or output.is_relative_to(source):raise ValueError('Compatibility copies must be outside the pinned library')
 rows=[]
 for rel,expected in FILES.items():
  original=source/rel;body=original.read_bytes().replace(b'\r\n',b'\n')
  if hashlib.sha256(body).hexdigest()!=expected:raise ValueError('Library source changed; semantically adapt before building: '+rel)
  text=body.decode('utf8')
  if rel=='src/llama-grammar.cpp':
   needle='''        bool                is_nested) {
    llama_grammar_rule rule;'''
   text=replace(text,needle,'''        bool                is_nested) {
    // PR29755 / issue29495: cap nested groups. ABI-preserving backport to the pinned parser.
    // Root plus256 groups; RAII restores the thread-local count on every return/exception.
    static thread_local unsigned nesting = 0;
    if (nesting >=257) throw std::runtime_error("grammar recursion depth limit exceeded");
    struct Depth { unsigned & n; Depth(unsigned & v):n(v){++n;} ~Depth(){--n;} } depth(nesting);
    llama_grammar_rule rule;''')
  elif rel=='common/jinja/value.cpp':
   text=replace(text,'static value from_json(const common_json & j, bool mark_input) {',
    'static value from_json(const common_json & j, bool mark_input, size_t depth = 0) {\n    if (depth >128) throw std::runtime_error("JSON nesting depth exceeds128");')
   text=replace(text,'from_json(item, mark_input)','from_json(item, mark_input, depth + 1)')
   text=replace(text,'obj->insert(it.key(), from_json(it.value(), mark_input));','obj->insert(it.key(), from_json(it.value(), mark_input, depth + 1));')
   # Keep quoted sibling includes valid without adding jinja/ to the system include search;
   # its string.h must never shadow the C runtime's <string.h>.
   text=re.sub(r'^#include "([^"/]+)"',lambda m:'#include "jinja/'+m[1]+'"' if (source/'common/jinja'/m[1]).is_file() else m[0],text,flags=re.M)
  else:
   text=replace(text,'// reject any tensors larger than the max buffer size','// PR31114: non-compute views are bounded by allocation, not shader addressing.\n    const bool non_compute = ggml_op_is_empty(op->op);')
   text=replace(text,'op->src[i] && !tensor_size_supported(ggml_nbytes(op->src[i]))','op->src[i] && !non_compute && !tensor_size_supported(ggml_nbytes(op->src[i]))')
   text=replace(text,'if (!tensor_size_supported(ggml_nbytes(op))) {','if (!non_compute && !tensor_size_supported(ggml_nbytes(op))) {')
  target=output/rel;target.parent.mkdir(parents=True,exist_ok=True);data=text.encode('utf8')
  if not target.exists() or target.read_bytes()!=data:target.write_bytes(data)
  rows.append(dict(path=rel,base_lf_sha256=expected,copy_lf_sha256=hashlib.sha256(data).hexdigest()))
 (output/'proof.json').write_text(json.dumps(dict(pin=PIN,files=rows,originals_unchanged=True),indent=2)+'\n',encoding='utf8')
 return rows
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--output',required=True);a=p.parse_args()
 try:print(json.dumps(prepare(a.source,a.output)))
 except (OSError,ValueError) as e:p.exit(2,str(e)+'\n')
