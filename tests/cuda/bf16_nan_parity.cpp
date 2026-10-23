// Numerical-only regression for the actual prefill BF16 conversion (PR2955).
#include "strata/kernels/bf16_bits.hpp"
#include "strata/prefill/kernels.hpp"
#include <cuda_runtime.h>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <stdexcept>
#include <string>
#include <vector>
static void ck(cudaError_t e, const char* what) {
    if (e != cudaSuccess) throw std::runtime_error(std::string(what) + ": " + cudaGetErrorString(e));
}
int main() {
    try {
        std::vector<float> input;
        std::vector<uint16_t> expected;
        for (uint32_t hi = 0; hi < 65536; ++hi) {
            for (uint32_t lo : {0u, 1u, 0x7fffu, 0x8000u, 0xffffu}) {
                const uint32_t bits = (hi << 16) | lo;
                float f; std::memcpy(&f, &bits, sizeof(f));
                input.push_back(f); expected.push_back(strata::kernels::bf16_from_f32(f));
            }
        }
        float* x = nullptr; uint16_t* y = nullptr;
        ck(cudaMalloc(reinterpret_cast<void**>(&x), input.size()*sizeof(float)), "input allocation");
        ck(cudaMalloc(reinterpret_cast<void**>(&y), expected.size()*sizeof(uint16_t)), "output allocation");
        ck(cudaMemcpy(x,input.data(),input.size()*sizeof(float),cudaMemcpyHostToDevice), "input copy");
        cudaStream_t stream; ck(cudaStreamCreateWithFlags(&stream,cudaStreamNonBlocking), "stream");
        strata::prefill::set_act_f16(false);
        auto check = [&](const char* mode) {
            std::vector<uint16_t> got(expected.size());
            ck(cudaStreamSynchronize(stream), "conversion sync");
            ck(cudaMemcpy(got.data(),y,got.size()*sizeof(uint16_t),cudaMemcpyDeviceToHost), "result copy");
            for (size_t i=0;i<got.size();++i) {
                if (got[i]!=expected[i]) {
                    std::fprintf(stderr,"%s: case %zu got %04x expected %04x\n",mode,i,got[i],expected[i]);
                    throw std::runtime_error("BF16 bit mismatch");
                }
            }
            std::printf("PASS %s: %zu finite/tie/Inf/NaN bit cases\n",mode,got.size());
        };
        strata::prefill::to_bf16(x,y,(int64_t)input.size(),stream);
        check("direct");
        cudaGraph_t graph=nullptr; cudaGraphExec_t exec=nullptr;
        ck(cudaStreamBeginCapture(stream,cudaStreamCaptureModeGlobal),"capture");
        strata::prefill::to_bf16(x,y,(int64_t)input.size(),stream);
        ck(cudaStreamEndCapture(stream,&graph),"end capture");
        ck(cudaGraphInstantiate(&exec,graph,nullptr,nullptr,0),"instantiate");
        ck(cudaGraphLaunch(exec,stream),"graph launch");
        check("graph");
        cudaGraphExecDestroy(exec);cudaGraphDestroy(graph);cudaStreamDestroy(stream);cudaFree(x);cudaFree(y);
        return 0;
    }catch(const std::exception& e){std::fprintf(stderr,"%s\n",e.what());return 1;}
}
