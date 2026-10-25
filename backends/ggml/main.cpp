// SPDX-License-Identifier: MIT
// Strata line protocol over the pinned ggml library, without a separate HTTP runtime.
// The verifier/checkpoint sequence follows llama.cpp's MIT speculative-simple example.
#include "arg.h"
#include "common.h"
#include "sampling.h"
#include "speculative.h"
#include "llama.h"
#include "gguf.h"
#include <algorithm>
#include <atomic>
#include <cmath>
#include <condition_variable>
#include <cstdio>
#include <filesystem>
#include <iostream>
#include <limits>
#include <mutex>
#include <sstream>
#include <stdexcept>
#include <thread>

namespace {
std::mutex output;
void line(const std::string & s) { std::lock_guard<std::mutex> l(output); std::cout << s << std::endl; }
struct Inbox {
    std::mutex mutex;
    std::condition_variable ready;
    std::string request;
    std::atomic<bool> stop{false}, busy{false};
    bool ended = false;
    void read() {
        std::string s;
        while (std::getline(std::cin, s)) {
            if (!s.empty() && s.back() == '\r') s.pop_back();
            if (s == "STOP") { if (busy.load()) stop.store(true); continue; }
            if (s == "QUIT" || s == "EXIT") break;
            if (s.rfind("GEN ", 0) != 0) { line("ERR only text GEN, STOP and QUIT are supported"); continue; }
            bool expected = false;
            if (!busy.compare_exchange_strong(expected, true)) { line("ERR request already active"); continue; }
            { std::lock_guard<std::mutex> l(mutex); stop.store(false); request = std::move(s); }
            ready.notify_one();
        }
        { std::lock_guard<std::mutex> l(mutex); ended = true; stop.store(true); }
        ready.notify_one();
    }
    bool next(std::string & s) {
        std::unique_lock<std::mutex> l(mutex);
        ready.wait(l, [&] { return ended || !request.empty(); });
        if (request.empty()) return false;
        s = std::move(request); request.clear(); return true;
    }
};
int64_t integer(const std::string & v) {
    size_t n; auto x = std::stoll(v, &n); if (n != v.size()) throw std::runtime_error("invalid integer"); return x;
}
float number(const std::string & v) {
    size_t n; auto x = std::stof(v, &n); if (n != v.size() || !std::isfinite(x)) throw std::runtime_error("invalid number"); return x;
}
struct Request { int limit; llama_tokens ids; common_params_sampling sampling; };
void check_mtp_architecture(const std::string & path) {
    gguf_init_params p{}; p.no_alloc=true;
    auto * meta=gguf_init_from_file(path.c_str(),p);
    if(!meta)throw std::runtime_error("cannot read GGUF metadata");
    struct Close {gguf_context * p;~Close(){gguf_free(p);}} close{meta};
    auto key=gguf_find_key(meta,"general.architecture");
    if(key<0||gguf_get_kv_type(meta,key)!=GGUF_TYPE_STRING)throw std::runtime_error("missing GGUF architecture");
    std::string arch=gguf_get_val_str(meta,key);
    const std::vector<std::string> supported={"deepseek2","deepseek4","glm-dsa","qwen35","qwen35moe"};
    if(std::find(supported.begin(),supported.end(),arch)==supported.end())
        throw std::runtime_error("MTP_REQUIRED: no reviewed native MTP graph for architecture "+arch+" in this embedded backend");
}
Request parse(const std::string & s, const common_params_sampling & defaults, int vocab, uint32_t ctx) {
    std::istringstream in(s); std::string word; in >> word >> word;
    const int64_t lim = integer(word); if (lim < 1 || lim > ctx) throw std::runtime_error("invalid max_new");
    Request r{int(lim), {}, defaults}; std::string tokens;
    while (in >> word) {
        auto at = word.find('=');
        if (at == std::string::npos) { tokens = word; if (in >> word) throw std::runtime_error("unexpected argument"); break; }
        auto k = word.substr(0, at), v = word.substr(at + 1);
        if (k == "temperature") { r.sampling.temp = number(v); if(r.sampling.temp<0) throw std::runtime_error("negative temperature"); }
        else if(k=="top_p") {r.sampling.top_p=number(v);if(r.sampling.top_p<=0||r.sampling.top_p>1)throw std::runtime_error("invalid top_p");}
        else if(k=="min_p") {r.sampling.min_p=number(v);if(r.sampling.min_p<0||r.sampling.min_p>1)throw std::runtime_error("invalid min_p");}
        else if(k=="top_k") {auto x=integer(v);if(x<0||x>vocab)throw std::runtime_error("invalid top_k");r.sampling.top_k=int(x);}
        else if(k=="seed") {auto x=integer(v);if(x<0||x>UINT32_MAX)throw std::runtime_error("invalid seed");r.sampling.seed=uint32_t(x);}
        else if(k=="penalty_repeat") {r.sampling.penalty_repeat=number(v);if(r.sampling.penalty_repeat<=0)throw std::runtime_error("invalid repetition penalty");}
        else if(k=="penalty_freq") r.sampling.penalty_freq=number(v);
        else if(k=="penalty_present") r.sampling.penalty_present=number(v);
        else if(k=="penalty_last_n") {auto x=integer(v);if(x<0||x>ctx)throw std::runtime_error("invalid penalty window");r.sampling.penalty_last_n=int(x);}
        else if(k=="ckpt" || k=="turn_at") { (void)integer(v); } // This adapter advertises no cache reuse.
        else throw std::runtime_error("unsupported sampling key: " + k);
    }
    if (tokens.empty()) throw std::runtime_error("empty prompt");
    std::istringstream ids(tokens);
    while(std::getline(ids,word,',')) { auto t=integer(word); if(t<0||t>=vocab)throw std::runtime_error("token outside vocabulary");r.ids.push_back(llama_token(t));if(r.ids.size()>ctx)throw std::runtime_error("prompt exceeds context"); }
    if(tokens.back()==',' || r.ids.size()+size_t(r.limit)>ctx)throw std::runtime_error("prompt plus max_new exceeds context");
    return r;
}
void check_logits(llama_context * ctx, int rows, int vocab) {
    for(int r=0;r<rows;++r){const float * p=llama_get_logits_ith(ctx,r);if(!p)throw std::runtime_error("missing logits");
        for(int v=0;v<vocab;++v)if(!std::isfinite(p[v]))throw std::runtime_error("nonfinite logits");}
}
void decode(llama_context * ctx, llama_batch & batch, common_speculative * spec) {
    if(llama_decode(ctx,batch)!=0)throw std::runtime_error("decode failed");
    if(spec&&!common_speculative_process(spec,batch))throw std::runtime_error("draft state update failed");
}
void generate(Request & r, common_params & p, llama_context * ctx, llama_model * model,
              common_speculative_init_result * spec_init, Inbox & inbox) {
    auto * dft=spec_init->context();const llama_seq_id seq=0;
    llama_memory_clear(llama_get_memory(ctx),true);
    if(dft)llama_memory_clear(llama_get_memory(dft),true);
    common_speculative_ptr spec(common_speculative_init(p.speculative,1));
    if(!spec&&dft)throw std::runtime_error("cannot initialize requested native speculation");
    common_sampler_ptr smpl(common_sampler_init(model,r.sampling));
    if(!smpl)throw std::runtime_error("cannot initialize sampler");
    auto * vocab=llama_model_get_vocab(model);const int nv=llama_vocab_n_tokens(vocab);
    const bool ck_t=common_context_can_seq_rm(ctx)==COMMON_CONTEXT_SEQ_RM_TYPE_FULL;
    const bool ck_d=dft&&common_context_can_seq_rm(dft)==COMMON_CONTEXT_SEQ_RM_TYPE_FULL;
    const int cap=int(llama_n_batch(ctx));
    llama_batch b=llama_batch_init(cap,0,1);
    struct FreeBatch {llama_batch & b;~FreeBatch(){llama_batch_free(b);}} free_batch{b};
    auto t0=ggml_time_us();size_t pos=0;
    while(pos+1<r.ids.size()&&!inbox.stop.load()){
        common_batch_clear(b);size_t n=std::min(size_t(cap),r.ids.size()-pos-1);
        for(size_t j=0;j<n;++j)common_batch_add(b,r.ids[pos+j],llama_pos(pos+j),{seq},false);
        decode(ctx,b,spec.get());pos+=n;
        line("PP "+std::to_string(pos)+" "+std::to_string(r.ids.size())+" "+std::to_string((ggml_time_us()-t0)/1000.0));
    }
    const auto t1=ggml_time_us();int produced=0,drafted=0,accepted=0;std::string finish="length";
    llama_tokens prompt(r.ids.begin(),r.ids.begin()+pos),draft;
    llama_token last=r.ids[pos];int past=int(pos);common_prompt_checkpoint ckpt;
    common_speculative_begin(spec.get(),seq,prompt);
    // Repetition penalties include the actual prompt, without consuming RNG draws.
    for(auto t:r.ids)common_sampler_accept(smpl.get(),t,false);
    while(produced<r.limit&&!inbox.stop.load()){
        if(draft.empty()){
            ckpt.update_pos(prompt.size(),llama_memory_seq_pos_min(llama_get_memory(ctx),seq),llama_memory_seq_pos_max(llama_get_memory(ctx),seq));
            if(ck_d)ckpt.update_dft(dft,seq,LLAMA_STATE_SEQ_FLAGS_PARTIAL_ONLY);
            int maximum=std::max(0,std::min({r.limit-produced-1,int(llama_n_ctx(ctx))-past-2,cap-1}));
            if(spec){common_speculative_get_draft_params(spec.get(),seq)={true,maximum,past,last,&prompt,&draft};common_speculative_draft(spec.get());}
            if(!draft.empty()&&ck_t)ckpt.update_tgt(ctx,seq,LLAMA_STATE_SEQ_FLAGS_PARTIAL_ONLY);
            if(dft){if(ck_d)ckpt.load_dft(dft,seq,LLAMA_STATE_SEQ_FLAGS_PARTIAL_ONLY);if(!llama_memory_seq_rm(llama_get_memory(dft),seq,ckpt.pos_max+1,-1))throw std::runtime_error("draft rollback failed");}
        }
        common_batch_clear(b);common_batch_add(b,last,past++,{seq},true);
        for(size_t j=0;j<draft.size();++j)common_batch_add(b,draft[j],past+int(j),{seq},true);
        decode(ctx,b,spec.get());check_logits(ctx,b.n_tokens,nv);
        common_sampler_ptr saved;if(ck_t)saved.reset(common_sampler_clone(smpl.get()));
        size_t nd=draft.size();auto chosen=common_sampler_sample_and_accept_n(smpl.get(),ctx,draft);
        if(chosen.empty())throw std::runtime_error("empty verification result");
        if(ck_t&&chosen.size()-1<nd){
            draft=std::move(chosen);ckpt.load_tgt(ctx,seq,LLAMA_STATE_SEQ_FLAGS_PARTIAL_ONLY);
            if(!llama_memory_seq_rm(llama_get_memory(ctx),seq,ckpt.pos_max+1,-1))throw std::runtime_error("target rollback failed");
            if(dft){if(ck_d)ckpt.load_dft(dft,seq,LLAMA_STATE_SEQ_FLAGS_PARTIAL_ONLY);if(!llama_memory_seq_rm(llama_get_memory(dft),seq,ckpt.pos_max+1,-1))throw std::runtime_error("draft rollback failed");}
            prompt.resize(ckpt.n_tokens);smpl=std::move(saved);past=int(prompt.size());continue;
        }
        if(spec)common_speculative_accept(spec.get(),seq,uint16_t(chosen.size()-1));
        past+=int(chosen.size())-1;drafted+=int(nd);accepted+=int(chosen.size())-1;
        bool eog=false;
        for(auto token:chosen){prompt.push_back(last);last=token;
            if(llama_vocab_is_eog(vocab,token)){finish="stop";eog=true;break;}
            if(produced>=r.limit)throw std::runtime_error("verification exceeded output budget");
            line("T "+std::to_string(token));++produced;
        }
        draft.clear();
        if(!llama_memory_seq_rm(llama_get_memory(ctx),seq,past,-1))throw std::runtime_error("target trim failed");
        if(dft&&!llama_memory_seq_rm(llama_get_memory(dft),seq,past,-1))throw std::runtime_error("draft trim failed");
        if(eog)break;
    }
    if(inbox.stop.load())finish="cancel";
    auto t2=ggml_time_us();
    std::ostringstream done;done<<"DONE "<<produced<<' '<<r.ids.size()<<' '<<(t1-t0)/1000.0<<' '<<(t2-t1)/1000.0<<' '<<finish<<' '<<accepted<<' '<<drafted<<" 0 0 0 0 0 0 0 0";
    // Publish completion only after admission is free for the client's next serial GEN.
    inbox.busy.store(false);line(done.str());
}
}
int main(int argc,char ** argv){
    std::setlocale(LC_NUMERIC,"C");
    if(argc==2&&std::string(argv[1])=="--version"){line("strata-ggml adapter 0.1 (" STRATA_DEVICE_NAME ")");return 0;}
    if(argc==2&&std::string(argv[1])=="--capabilities"){
        line("{\"backend\":\"" STRATA_DEVICE_NAME "\",\"trained_mtp\":true,\"universal_mtp\":false,\"model_downloads\":false,\"images\":false,\"cache_reuse\":false}");return 0;}
    if(argc==2&&std::string(argv[1])=="--protocol-self-test"){
        common_params_sampling defaults;defaults.temp=0;
        const std::vector<std::string> bad={"GEN 0 1,2","GEN -1 1,2","GEN 3 -1,2","GEN 3 256,2","GEN 3 1,,2","GEN 3 1,2,", "GEN 3 1,2 trailing", "GEN 3 temperature=nan 1,2", "GEN 3 top_p=0 1,2", "GEN 3 min_p=2 1,2", "GEN 3 seed=4294967296 1,2", "GEN 3 penalty_repeat=0 1,2", "GEN 3 unsupported=1 1,2", "GEN 63 1,2"};
        for(const auto & s:bad){bool rejected=false;try{(void)parse(s,defaults,256,64);}catch(const std::exception &){rejected=true;}if(!rejected){line("FAIL rejected input accepted");return 1;}}
        auto r=parse("GEN 3 temperature=0.7 top_p=0.95 min_p=0.05 top_k=64 seed=123 penalty_repeat=1.1 penalty_last_n=64 ckpt=0 turn_at=0 1,2",defaults,256,64);
        if(r.limit!=3||r.ids!=llama_tokens({1,2})||r.sampling.seed!=123||r.sampling.top_k!=64){line("FAIL valid sampling changed");return 1;}
        line("PASS 15 protocol boundary cases");return 0;
    }
    bool serve=false,require=false;std::vector<char*> args{argv[0]};
    for(int i=1;i<argc;++i){std::string a=argv[i];if(a=="--serve")serve=true;else if(a=="--require-mtp")require=true;
        else if(a.find("hf-")!=std::string::npos||a.find("url")!=std::string::npos||a=="--rpc"){std::cerr<<"remote model sources are disabled"<<std::endl;return 2;}else args.push_back(argv[i]);}
    common_params p;p.sampling.temp=0;p.speculative.draft.n_max=2;common_init();
    try{
        if(!common_params_parse(int(args.size()),args.data(),p,LLAMA_EXAMPLE_SPECULATIVE))return 1;
        if(!serve)throw std::runtime_error("--serve is required; no separate HTTP server is installed");
        auto remote=[](const common_params_model & m){return !m.url.empty()||!m.hf_repo.empty()||!m.hf_file.empty()||!m.docker_repo.empty();};
        if(remote(p.model)||remote(p.speculative.draft.mparams))throw std::runtime_error("remote model sources are disabled, including environment overrides");
        if(!std::filesystem::is_regular_file(p.model.path))throw std::runtime_error("a local --model GGUF is required; downloads are disabled");
        if(require)p.speculative.types={COMMON_SPECULATIVE_TYPE_DRAFT_MTP};
        require=require||std::find(p.speculative.types.begin(),p.speculative.types.end(),COMMON_SPECULATIVE_TYPE_DRAFT_MTP)!=p.speculative.types.end();
        if(require)check_mtp_architecture(p.model.path);
        if(!p.speculative.draft.mparams.path.empty()&&!std::filesystem::is_regular_file(p.speculative.draft.mparams.path))throw std::runtime_error("draft GGUF is not a local file");
        auto limits=common_speculative_get_output_limits(p.n_batch,1,common_speculative_n_max(&p.speculative));p.n_outputs_max=limits.total;p.n_outputs_max_per_seq=limits.per_seq;
        llama_backend_init(); // No affinity/NUMA/power policy is installed by this adapter.
        auto target=common_init_from_params(p);auto * model=target->model();auto * ctx=target->context();
        if(!model||!ctx)throw std::runtime_error("model initialization failed");
        auto dp=common_base_params_to_speculative(p);auto si=common_speculative_init_from_params(dp,model,ctx);
        p.speculative.draft.ctx_tgt=ctx;p.speculative.draft.ctx_dft=si->context();
        if(require&&!si->context())throw std::runtime_error("MTP_REQUIRED: compatible trained NextN head/context unavailable");
        Inbox inbox;std::thread reader([&]{inbox.read();});
        line("INFO backend=" STRATA_DEVICE_NAME " mtp="+std::to_string(require&&si->context()!=nullptr));
        line("READY "+std::to_string(llama_n_ctx(ctx))+" stop");
        std::string s;
        while(inbox.next(s)){
            try{auto request=parse(s,p.sampling,llama_vocab_n_tokens(llama_model_get_vocab(model)),llama_n_ctx(ctx));generate(request,p,ctx,model,si.get(),inbox);}
            catch(const std::exception & e){inbox.busy.store(false);line(std::string("ERR ")+e.what());}
        }
        reader.join();return 0;
    }catch(const std::exception & e){std::cerr<<"strata-ggml: "<<e.what()<<std::endl;return 2;}
}
