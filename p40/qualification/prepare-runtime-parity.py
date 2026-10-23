"""Build host test drivers around existing immutable native libraries, never rebuild those libraries."""
import argparse,hashlib,json,os
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--build',required=True);p.add_argument('--output',required=True);p.add_argument('--cuda',default=os.environ.get('CUDA_PATH'));a=p.parse_args()
if not a.cuda:raise RuntimeError('Provide --cuda or CUDA_PATH for the qualified CUDA12.9 toolkit')
R=Path(a.root).resolve();B=Path(a.build).resolve();O=Path(a.output).resolve()
assert B.is_relative_to(R/'work') and O.is_relative_to(R/'work')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
pins=json.loads((R/'p40/qualification/source-pins.json').read_text(encoding='utf-8-sig'))
for name,h in pins.items():
 if sha(R/name)!=h:raise RuntimeError('Parity source changed; review before adapting: '+name)
P=O/'runtime-parity-src';P.mkdir(parents=True,exist_ok=False)
def replace(s,old,new):
 if s.count(old)!=1:raise RuntimeError('Parity adaptation anchor is not unique: '+old[:70])
 return s.replace(old,new)
b=(R/'src/kernels/b6_mmvq_bench.cpp').read_text(encoding='utf-8-sig')
b=replace(b,'    {"head Q5_K", 13, 2560, 248320, 256, 176, {0, 2}},','    {"head Q5_K", 13, 2560, 248320, 256, 176, {0, 2}},\n    {"actual head Q6_K", 14, 2560, 248320, 256, 210, {208, -1}},\n    {"MTP fc Q8_0", 8, 2560, 2560, 32, 34, {0, -1}},\n    {"MTP out Q8_0", 8, 6144, 2560, 32, 34, {0, -1}},')
b=replace(b,'                call(c, b, 0, T, yb, s);','''                call(c, b, 0, T, yb, s); // warm lazy state before capture
                cudaGraph_t graph = nullptr; cudaGraphExec_t exec = nullptr;
                if (!ck(cudaStreamBeginCapture(s, cudaStreamCaptureModeGlobal), "b6 capture")) return 1;
                call(c, b, 0, T, yb, s);
                if (!ck(cudaStreamEndCapture(s, &graph), "b6 end capture") ||
                    !ck(cudaGraphInstantiate(&exec, graph, nullptr, nullptr, 0), "b6 instantiate") ||
                    !ck(cudaGraphLaunch(exec, s), "b6 graph launch") || !ck(cudaStreamSynchronize(s), "b6 graph sync")) return 1;
                cudaGraphExecDestroy(exec); cudaGraphDestroy(graph);''')
b=replace(b,'const double ta = median_ms(c, b, T, reps, s, ev);','const double ta = 0.0; // numerical-only driver: no timing loop')
b=replace(b,'const double tb = median_ms(c, b, T, reps, s, ev);','const double tb = 0.0; // numerical-only driver: no timing loop')
b=replace(b,'    setvbuf(stdout, nullptr, _IONBF, 0);','    setvbuf(stdout, nullptr, _IONBF, 0);\n    std::puts("# NUMERICAL_ONLY: timing columns are disabled placeholders, not measurements");')
(P/'b6_runtime_parity.cpp').write_text(b,encoding='utf-8')
e=(R/'src/kernels/expdec_bench.cpp').read_text(encoding='utf-8-sig')
e=replace(e,'constexpr int kMaxEntries = kMaxT * kTop;','constexpr int kMaxEntries = kMaxT * kTop;\nint qualification_grid_groups = 0;')
e=replace(e,'dout, stream, 0);','dout, stream, qualification_grid_groups);')
e=replace(e,'const int reps = argc > 1 ?', 'qualification_grid_groups = argc > 7 ? std::atoi(argv[7]) : 0;\n    if (qualification_grid_groups < 0 || qualification_grid_groups > 8) return 1;\n    std::printf("# qualification grid_groups=%d (0 VRAM, 1..8 strided PCIe)\\n", qualification_grid_groups);\n    const int reps = argc > 1 ?')
e=replace(e,'                bool same = true;','''                cudaGraph_t graph = nullptr; cudaGraphExec_t exec = nullptr;
                if (!ck(cudaStreamBeginCapture(se.s, cudaStreamCaptureModeGlobal), "expdec capture")) return false;
                cudaMemsetAsync(dout, 0, (size_t) NE * kEmbd * sizeof(float), se.s); call(0);
                if (!ck(cudaStreamEndCapture(se.s, &graph), "expdec end capture") ||
                    !ck(cudaGraphInstantiate(&exec, graph, nullptr, nullptr, 0), "expdec instantiate") ||
                    !ck(cudaGraphLaunch(exec, se.s), "expdec graph launch") || !ck(cudaStreamSynchronize(se.s), "expdec graph sync")) return false;
                std::vector<float> graph_out(res.size());
                if (!ck(cudaMemcpy(graph_out.data(), dout, graph_out.size()*sizeof(float), cudaMemcpyDeviceToHost), "expdec graph copy")) return false;
                if (std::memcmp(graph_out.data(),res.data(),res.size()*sizeof(float))) { ++bad; std::puts("GRAPH DIFFERENT"); }
                cudaGraphExecDestroy(exec); cudaGraphDestroy(graph);
                bool same = true;''')
e=replace(e,'if (nonfinite) std::printf(', 'if (nonfinite) ++bad;\n                    if (nonfinite) std::printf(')
e=replace(e,'                timed(0, 5, us[0]);\n                timed(1, 3, us[1]);\n                timed(2, 3, us[2]);','                // Numerical-only driver: no timing or warmup loops.\n                us[0] = us[1] = us[2] = 0.0;')
e=replace(e,'const double gbps = (double) G * (double) L.bytes / (us[0] * 1e-6) / 1e9;','const double gbps = 0.0; // timing disabled')
(P/'expdec_runtime_parity.cpp').write_text(e,encoding='utf-8')
m=(R/'tests/cuda/pascallama_mmq_screen.cpp').read_text(encoding='utf-8-sig')
m=replace(m,'#include <algorithm>','#include <algorithm>\n#include <cstdlib>')
m=replace(m,'if (t != GGML_TYPE_IQ3_S) throw','if (t != GGML_TYPE_IQ3_S && t != GGML_TYPE_IQ2_S && t != GGML_TYPE_IQ3_XXS && t != GGML_TYPE_IQ4_XS) throw')
m=replace(m,'GGML_TYPE_Q2_0, GGML_TYPE_Q8_0})','GGML_TYPE_Q2_0, GGML_TYPE_Q8_0, GGML_TYPE_IQ2_S, GGML_TYPE_IQ3_XXS, GGML_TYPE_IQ4_XS})')
anchor='                ++trial;'
addition=''
for ty in ['IQ2_S','IQ3_XXS','IQ4_XS']:
 addition+=f'                product(ctx,s,("{ty}"+tag).c_str(),GGML_TYPE_{ty},640,2560,counts,trial+13);\n'
m=replace(m,anchor,addition+anchor)
m=replace(m,'    double err2 = 0, ref2 = 0, max_abs = 0, zero_max = 0;','''    if (const char* dump = std::getenv("STRATA_PARITY_OUTPUT")) {
        FILE* f = std::fopen(dump, "ab"); if (!f) throw std::runtime_error("parity dump open failed");
        const uint64_t n = got.size();
        const bool ok = std::fwrite(&n,sizeof(n),1,f)==1 && std::fwrite(got.data(),sizeof(float),got.size(),f)==got.size();
        std::fclose(f); if (!ok) throw std::runtime_error("parity dump write failed");
    }
    double err2 = 0, ref2 = 0, max_abs = 0, zero_max = 0;''')
(P/'mmq_tile_parity.cpp').write_text(m,encoding='utf-8')
cuda=Path(a.cuda).resolve();libs=[B/'strata_kernels.lib',B/'strata_core.lib',B/'strata_mmq.lib',B/'strata_mmq_w4a4.lib',B/'ggml/src/ggml-cpu.lib',B/'ggml/src/ggml-base.lib']
for v in libs:
 if not v.is_file():raise RuntimeError('Missing existing native library '+str(v))
q=lambda x:'"'+str(x).replace('\\','/')+'"'
text='cmake_minimum_required(VERSION 3.24)\nproject(strata_runtime_checks LANGUAGES CXX)\nset(CMAKE_CXX_STANDARD 17)\nset(CMAKE_RUNTIME_OUTPUT_DIRECTORY '+q(O)+')\n'
for name in ['b6_runtime_parity','expdec_runtime_parity','mmq_tile_parity']:
 text+=f'add_executable({name} {name}.cpp)\n'
 text+=f'target_include_directories({name} PRIVATE '+ ' '.join(q(x) for x in [R/'include',R/'.p40-deps/llama.cpp/ggml/include',cuda/'include'])+')\n'
 selected=libs[:2] if name!='mmq_tile_parity' else libs[2:]
 text+=f'target_link_libraries({name} PRIVATE '+ ' '.join(q(x) for x in selected+[cuda/'lib/x64/cudart.lib',cuda/'lib/x64/cudadevrt.lib',cuda/'lib/x64/cuda.lib'])+')\n'
(P/'CMakeLists.txt').write_text(text,encoding='utf-8')
manifest={'schema':1,'source_pins':pins,'libraries':[{ 'path':str(x.relative_to(R)),'sha256':sha(x)} for x in libs],'generated_sources':{str(x.relative_to(R)):sha(x) for x in P.iterdir()},'engine':str((B/'strata.exe').relative_to(R)),'engine_sha256':sha(B/'strata.exe'),'output':str(O.relative_to(R)),'gpu_tests_run':False}
(O/'runtime-parity-build-inputs.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
print(str(P))
