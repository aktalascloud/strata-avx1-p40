// Numerical-only qualification of PR4039's absolute bounds and compact per-group destination.
// Uses the existing MIT Pascal fixture's data generators; no model, speed measurement or tolerances.
#define main original_pascal_screen_main
#include "pascallama_mmq_screen.cpp"
#undef main
#include <cstring>

namespace {
std::vector<uint8_t> weights(ggml_type t, int64_t nr, int64_t nc, int e) {
    if (ggml_get_type_traits(t)->from_float_ref || t == GGML_TYPE_IQ3_S)
        return make_matrix(t, nr, nc, e, 7);
    const size_t rb = ggml_row_size(t, nc), bs = ggml_type_size(t);
    std::vector<uint8_t> out(size_t(nr) * rb);
    for (int64_t r = 0; r < nr; ++r)
        for (size_t b = 0; b < rb / bs; ++b) {
            auto* p = out.data() + size_t(r) * rb + b * bs;
            for (size_t k = 0; k < bs; ++k) p[k] = uint8_t(k * 37 + b * 19 + r * 11 + e * 23);
            p[0] = 0; p[1] = 0x24;
        }
    return out;
}
void scratch_case(mmq::Context& ctx, cudaStream_t s, ggml_type t, int64_t nr, int64_t nc,
                  const std::vector<int>& counts) {
    const int ne = int(counts.size()), rows = std::accumulate(counts.begin(), counts.end(), 0);
    std::vector<int32_t> bounds(size_t(ne) + 1), ids(static_cast<size_t>(rows));
    for (int e = 0; e < ne; ++e) bounds[size_t(e) + 1] = bounds[size_t(e)] + counts[size_t(e)];
    std::iota(ids.begin(), ids.end(), 0);
    const size_t eb = mmq::matrix_bytes(int(t), nr, nc);
    std::vector<uint8_t> host(size_t(ne) * eb + 4096);
    for (int e = 0; e < ne; ++e) {
        auto w = weights(t, nr, nc, e);
        std::copy(w.begin(), w.end(), host.begin() + ptrdiff_t(size_t(e) * eb));
    }
    auto x = make_x(rows, nc, 11);
    const size_t bytes = size_t(rows) * size_t(nr) * 4;
    const int cap = *std::max_element(counts.begin(), counts.end());
    Dev dw(host.size()), dx(x.size()*4), dxq(mmq::q8_bytes(rows,nc)), db(bounds.size()*4), di(ids.size()*4),
        dy(bytes), compact(size_t(cap)*size_t(nr)*4 + 256), joined(bytes);
    ck(cudaMemcpy(dw.p,host.data(),host.size(),cudaMemcpyHostToDevice),"weights");
    ck(cudaMemcpy(dx.p,x.data(),x.size()*4,cudaMemcpyHostToDevice),"input");
    ck(cudaMemcpy(db.p,bounds.data(),bounds.size()*4,cudaMemcpyHostToDevice),"bounds");
    ck(cudaMemcpy(di.p,ids.data(),ids.size()*4,cudaMemcpyHostToDevice),"ids");
    ck(cudaDeviceSynchronize(),"input ordering");
    mmq::quantize(static_cast<float*>(dx.p),nullptr,dxq.p,int(t),nc,nc,rows,s);
    mmq::Product p; p.w=dw.p;p.type=int(t);p.w_rows=nr;p.w_cols=nc;p.expert_bytes=eb;p.n=ne;
    p.xq=dxq.p;p.bounds=static_cast<int32_t*>(db.p);p.ids=static_cast<int32_t*>(di.p);
    p.total_rows=rows;p.max_rows=cap;p.dst=static_cast<float*>(dy.p);p.ld_dst=nr;
    ctx.run(p,s);ck(cudaStreamSynchronize(s),"whole product");
    std::vector<float> reference(size_t(rows)*size_t(nr)), got(reference.size());
    ck(cudaMemcpy(reference.data(),dy.p,bytes,cudaMemcpyDeviceToHost),"reference");
    auto run=[&] {
        for(int e=0;e<ne;++e) {
            if(!counts[size_t(e)])continue;
            auto part=p;part.w=static_cast<uint8_t*>(dw.p)+size_t(e)*eb;part.n=1;
            part.bounds=static_cast<int32_t*>(db.p)+e;part.max_rows=counts[size_t(e)];
            const auto shift=uint64_t(bounds[size_t(e)])*uint64_t(nr)*4;
            part.dst=reinterpret_cast<float*>(reinterpret_cast<uintptr_t>(compact.p)-shift);
            ctx.run(part,s);
            ck(cudaMemcpyAsync(static_cast<uint8_t*>(joined.p)+shift,compact.p,
                size_t(counts[size_t(e)])*size_t(nr)*4,cudaMemcpyDeviceToDevice,s),"compact result");
        }
    };
    run();ck(cudaStreamSynchronize(s),"compact product");
    ck(cudaMemcpy(got.data(),joined.p,bytes,cudaMemcpyDeviceToHost),"compact readback");
    if(std::memcmp(reference.data(),got.data(),bytes))throw std::runtime_error("compact product differs from whole");
    cudaGraph_t graph=nullptr;cudaGraphExec_t exec=nullptr;
    ck(cudaStreamBeginCapture(s,cudaStreamCaptureModeGlobal),"capture");run();
    ck(cudaStreamEndCapture(s,&graph),"end capture");ck(cudaGraphInstantiate(&exec,graph,0),"instantiate");
    ck(cudaGraphLaunch(exec,s),"launch graph");ck(cudaStreamSynchronize(s),"graph sync");
    ck(cudaMemcpy(got.data(),joined.p,bytes,cudaMemcpyDeviceToHost),"graph readback");
    if(std::memcmp(reference.data(),got.data(),bytes))throw std::runtime_error("compact graph differs from whole");
    cudaGraphExecDestroy(exec);cudaGraphDestroy(graph);
    std::printf("PASS compact/whole/graph type%d shape%lldx%lld rows%d\n",int(t),(long long)nr,(long long)nc,rows);
}
}
int main() {
    try {
        cudaDeviceProp prop{};ck(cudaGetDeviceProperties(&prop,0),"device");
        if(prop.major!=6||prop.minor!=1)return 77;
        cudaStream_t s=nullptr;ck(cudaStreamCreateWithFlags(&s,cudaStreamNonBlocking),"stream");
        { mmq::Context ctx;
          for(auto t:{GGML_TYPE_IQ3_S,GGML_TYPE_IQ3_XXS,GGML_TYPE_IQ2_S,GGML_TYPE_IQ4_XS,GGML_TYPE_IQ4_NL,GGML_TYPE_Q2_0,GGML_TYPE_Q8_0}) {
            ggml_quantize_init(t);
            for(const auto& counts:std::vector<std::vector<int>>{{0,1,3,7},{3,0,1,3}}) {
                scratch_case(ctx,s,t,1280,2560,counts);
                if(640 % ggml_blck_size(t)==0) scratch_case(ctx,s,t,2560,640,counts);
            }
          }
        }
        ck(cudaStreamDestroy(s),"destroy");ggml_quantize_free();return 0;
    } catch(const std::exception& e){std::fprintf(stderr,"FAIL scratch parity: %s\n",e.what());return 1;}
}
