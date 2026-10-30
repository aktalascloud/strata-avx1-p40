"""Pinned build copies for Vulkan large views, bounded recursion, CPU SET_ROWS scratch and model-bounded control vectors (MIT)."""
import argparse,hashlib,json,pathlib,re
PIN='b9acf138a1e28ce1fc23b5a4fc4b12444b50f7ea'
FILES={
 'src/llama-grammar.cpp':'97d76071a2ed1b0c4ce827f002f554b12a25593776adb525dde33ac4cb1eb1e9',
 'common/jinja/value.cpp':'14d98a60a2fcf71f84cac250ca6885187c940ec815859f7c398ca48f857e2d63',
 'ggml/src/ggml-vulkan/ggml-vulkan.cpp':'dd4eaec3c5843f687c930b20de500dd61b1b026f55c6b1fb49da9ec7790dd6bb',
 'ggml/src/ggml-cpu/ggml-cpu.c':'45b22f8c83b2cbccabfc2f81a38ef8a5810223e1ce366b7c6f77d42faa5cc6f3',
 'common/common.cpp':'b19cf170b0c6f8d1506e6c9460dd168131c2855de79b1b84b993b472c559f8a6',
 'common/common.h':'f06e8f35170782940cf5572837114e5e21cbb920aa50814057f9c505d334ef1b'}
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
  elif rel=='ggml/src/ggml-cpu/ggml-cpu.c':
   # PR30454: every CPU worker uses its own F16 conversion row; plan for all of them.
   text=replace(text,'        case GGML_OP_OUT_PROD:\n            {\n                n_tasks = n_threads;\n            } break;\n        case GGML_OP_GET_ROWS:\n        case GGML_OP_SET_ROWS:\n','        case GGML_OP_OUT_PROD:\n        case GGML_OP_SET_ROWS:\n            {\n                n_tasks = n_threads;\n            } break;\n        case GGML_OP_GET_ROWS:\n')
   text='#line 1 \"ggml-cpu.c\"\n'+text
  elif rel=='common/common.cpp':
   text=replace(text,'common_control_vector_load(params.control_vectors);','common_control_vector_load(params.control_vectors, llama_model_n_layer(model));')
   text=replace(text,'static common_control_vector_data common_control_vector_load_one(const common_control_vector_load_info & load_info) {','static common_control_vector_data common_control_vector_load_one(const common_control_vector_load_info & load_info, int32_t n_layer) {')
   text=replace(text,'        } else if (layer_idx == 0) {\n            COM_ERR("invalid (zero) direction tensor layer index in %s\\n", load_info.fname.c_str());\n            result.n_embd = -1;\n            break;\n        }\n','        } else if (layer_idx == 0) {\n            COM_ERR("invalid (zero) direction tensor layer index in %s\\n", load_info.fname.c_str());\n            result.n_embd = -1;\n            break;\n        } else if (layer_idx > n_layer) {\n            COM_ERR("direction tensor layer index %d exceeds the model layer count %d in %s\\n", layer_idx, n_layer, load_info.fname.c_str());\n            result.n_embd = -1;\n            break;\n        }\n')
   text=replace(text,'static_cast<size_t>(result.n_embd * layer_idx)','static_cast<size_t>(result.n_embd) * layer_idx')
   text=replace(text,'result.data.data() + result.n_embd * (layer_idx - 1)','result.data.data() + static_cast<size_t>(result.n_embd) * (layer_idx - 1)')
   text=replace(text,'common_control_vector_data common_control_vector_load(const std::vector<common_control_vector_load_info> & load_infos) {','common_control_vector_data common_control_vector_load(const std::vector<common_control_vector_load_info> & load_infos, int32_t n_layer) {')
   text=replace(text,'common_control_vector_load_one(info);','common_control_vector_load_one(info, n_layer);')
   text='#line 1 "common.cpp"\n'+text
  elif rel=='common/common.h':
   text=replace(text,'common_control_vector_data common_control_vector_load(const std::vector<common_control_vector_load_info> & load_infos);','common_control_vector_data common_control_vector_load(const std::vector<common_control_vector_load_info> & load_infos, int32_t n_layer);')
   # Use the original header identity so transitive includes share its pragma-once state.
   # The physical wrapper is found by common.cpp's quote include; its angle include
   # resolves through the unchanged original common/ include directory.
   text='#line 1 "common.h"\n#pragma once\n#include <common.h>\ncommon_control_vector_data common_control_vector_load(const std::vector<common_control_vector_load_info> & load_infos, int32_t n_layer);\n'
  else:
   text=replace(text,'// reject any tensors larger than the max buffer size','// PR31114: non-compute views are bounded by allocation, not shader addressing.\n    const bool non_compute = ggml_op_is_empty(op->op);')
   text=replace(text,'op->src[i] && !tensor_size_supported(ggml_nbytes(op->src[i]))','op->src[i] && !non_compute && !tensor_size_supported(ggml_nbytes(op->src[i]))')
   text=replace(text,'if (!tensor_size_supported(ggml_nbytes(op))) {','if (!non_compute && !tensor_size_supported(ggml_nbytes(op))) {')
  # Stable diagnostic identity for every generated source, including retained compatibility ports.
  if not text.startswith('#line 1 "'):
   text='#line 1 "'+rel+'"\n'+text
  target=output/rel;target.parent.mkdir(parents=True,exist_ok=True);data=text.encode('utf8')
  if not target.exists() or target.read_bytes()!=data:target.write_bytes(data)
  rows.append(dict(path=rel,base_lf_sha256=expected,copy_lf_sha256=hashlib.sha256(data).hexdigest()))
 (output/'proof.json').write_text(json.dumps(dict(pin=PIN,files=rows,originals_unchanged=True),indent=2)+'\n',encoding='utf8')
 return rows
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--output',required=True);a=p.parse_args()
 try:print(json.dumps(prepare(a.source,a.output)))
 except (OSError,ValueError) as e:p.exit(2,str(e)+'\n')
