// SPDX-License-Identifier: MIT
// Small synthetic tensor parity, without model weights, timing loops or throughput claims.
#include "ggml.h"
#include "ggml-backend.h"
#include "ggml-cpu.h"
#include "ggml-alloc.h"
#include <cmath>
#include <cstdio>
#include <stdexcept>
#include <string>
#include <vector>
std::vector<float> compute(ggml_backend_t backend,ggml_type type,int cols,const std::vector<unsigned char>& weights,const std::vector<float>& input){
    ggml_context * ctx=ggml_init({2*1024*1024,nullptr,true});if(!ctx)throw std::runtime_error("context allocation failed");
    auto w=ggml_new_tensor_2d(ctx,type,256,16);auto x=ggml_new_tensor_2d(ctx,GGML_TYPE_F32,256,cols);
    auto mm=ggml_mul_mat(ctx,w,x);auto out=ggml_silu(ctx,ggml_rms_norm(ctx,mm,1e-5f));
    if(!ggml_backend_supports_op(backend,mm)||!ggml_backend_supports_op(backend,out)||!ggml_backend_supports_op(backend,out->src[0])){ggml_free(ctx);return {};}
    auto graph=ggml_new_graph_custom(ctx,256,false);ggml_build_forward_expand(graph,out);
    auto buffer=ggml_backend_alloc_ctx_tensors(ctx,backend);if(!buffer){ggml_free(ctx);throw std::runtime_error("backend allocation failed");}
    ggml_backend_tensor_set(w,weights.data(),0,weights.size());ggml_backend_tensor_set(x,input.data(),0,input.size()*sizeof(float));
    if(ggml_backend_graph_compute(backend,graph)!=GGML_STATUS_SUCCESS)throw std::runtime_error("graph compute failed");
    std::vector<float> result(16*cols);ggml_backend_tensor_get(out,result.data(),0,result.size()*sizeof(float));
    ggml_backend_buffer_free(buffer);ggml_free(ctx);return result;
}
int main(int argc,char**argv){
    if(argc!=2){std::fprintf(stderr,"Expected explicit CPU,CUDA0 or Vulkan0\n");return 2;}
    ggml_backend_load_all();auto device=ggml_backend_dev_by_name(argv[1]);if(!device){std::fprintf(stderr,"Device not available\n");return 3;}
    auto test=ggml_backend_dev_init(device,nullptr),cpu=ggml_backend_cpu_init();if(!test||!cpu)return 4;
    int passed=0,skipped=0;double worst=0;
    try{
      std::vector<float> source(256*16),importance(256,1.0f);
      for(size_t i=0;i<source.size();++i)source[i]=float(std::sin(double(i)*0.017)+0.3*std::cos(double(i)*0.037));
      for(auto type:{GGML_TYPE_F32,GGML_TYPE_F16,GGML_TYPE_Q4_0,GGML_TYPE_IQ3_S,GGML_TYPE_IQ2_S,GGML_TYPE_IQ3_XXS}){
        ggml_quantize_init(type);std::vector<unsigned char> weights(ggml_row_size(type,256)*16);
        auto bytes=ggml_quantize_chunk(type,source.data(),weights.data(),0,16,256,importance.data());if(bytes!=weights.size())throw std::runtime_error("quantized tensor size mismatch");
        for(int cols:{1,4,8}){
          std::vector<float> input(256*cols);for(size_t i=0;i<input.size();++i)input[i]=float(std::sin(double(i)*0.023)+0.1*std::cos(double(i)*0.11));
          auto want=compute(cpu,type,cols,weights,input),got=compute(test,type,cols,weights,input);
          if(want.empty())throw std::runtime_error("CPU reference operation unsupported");
          if(got.empty()){++skipped;std::printf("SKIP %s cols%d: backend operation unsupported, scheduler needs CPU fallback\n",ggml_type_name(type),cols);continue;}
          double error=0,signal=0;for(size_t i=0;i<want.size();++i){if(!std::isfinite(got[i])||!std::isfinite(want[i]))throw std::runtime_error("nonfinite tensor result");error+=std::pow(double(got[i])-want[i],2);signal+=double(want[i])*want[i];}
          double nmse=error/(signal+1e-20);double bound=ggml_is_quantized(type)?1e-4:1e-6;
          if(nmse>bound)throw std::runtime_error(std::string("tensor numerical bound exceeded: ")+ggml_type_name(type)+" NMSE="+std::to_string(nmse));
          worst=std::max(worst,nmse);++passed;std::printf("PASS %s cols%d NMSE %.9g\n",ggml_type_name(type),cols,nmse);
        }
      }
      std::printf("RESULT passed=%d skipped=%d worst_nmse=%.9g no_model_no_timing=1\n",passed,skipped,worst);
      ggml_backend_free(test);ggml_backend_free(cpu);return passed>=3?0:5;
    }catch(const std::exception &e){std::fprintf(stderr,"FAIL %s\n",e.what());return 1;}
}
