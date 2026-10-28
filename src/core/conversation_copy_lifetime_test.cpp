// Host-only coverage of the actual upstream pooled copy helper. No CUDA/device calls.
#include "strata/core/conversation_cache.hpp"
#include "strata/core/progress.hpp"
#include <cuda_runtime.h>
#include <atomic>
#include <cstdio>
#include <cstdlib>
#include <mutex>
#include <thread>
#include <unordered_map>
namespace fixture {
constexpr cudaError_t failure=static_cast<cudaError_t>(1);
std::mutex mu;std::unordered_map<cudaStream_t,int> live;
std::atomic<int> errors{0};int created=0;
thread_local int device=0;
thread_local bool fail_get=false,fail_create=false,fail_copy=false,fail_sync=false;
cudaError_t get(int* d){if(fail_get)return failure;*d=device;return cudaSuccess;}
cudaError_t set(int d){device=d;return cudaSuccess;}
cudaError_t create(cudaStream_t* s,unsigned){std::lock_guard<std::mutex> l(mu);if(fail_create)return failure;*s=reinterpret_cast<cudaStream_t>(uintptr_t(++created));live.emplace(*s,device);return cudaSuccess;}
cudaError_t destroy(cudaStream_t s){std::lock_guard<std::mutex> l(mu);if(!live.erase(s))++errors;return cudaSuccess;}
cudaError_t copy(void*,const void*,size_t,decltype(cudaMemcpyDefault),cudaStream_t s){std::lock_guard<std::mutex> l(mu);if(!live.count(s)||live[s]!=device)++errors;return fail_copy?failure:cudaSuccess;}
cudaError_t sync(cudaStream_t){return fail_sync?failure:cudaSuccess;}
cudaError_t event_create(cudaEvent_t* e,unsigned){*e=reinterpret_cast<cudaEvent_t>(uintptr_t(1+device));return cudaSuccess;}
cudaError_t event_record(cudaEvent_t,cudaStream_t){return cudaSuccess;}
cudaError_t event_wait(cudaStream_t,cudaEvent_t,unsigned){return cudaSuccess;}
void check(bool ok,const char* what){if(!ok){std::fprintf(stderr,"FAIL: %s\n",what);std::exit(1);}}
}
namespace strata::core {int joins=0;void fixture_checkpoint_join(const void*){++joins;}}
#define conversation_checkpoint_join fixture_checkpoint_join
#define cudaGetDevice fixture::get
#define cudaSetDevice fixture::set
#define cudaStreamCreateWithFlags fixture::create
#define cudaStreamDestroy fixture::destroy
#define cudaMemcpyAsync fixture::copy
#define cudaStreamSynchronize fixture::sync
#define cudaEventCreateWithFlags fixture::event_create
#define cudaEventRecord fixture::event_record
#define cudaStreamWaitEvent fixture::event_wait
#include "conversation_copy.hpp"
int main(){
 using namespace fixture;using namespace strata::core;using namespace strata::core::conversation_detail;
 for(int i=0;i<64;++i){
   ConversationCheckpoint c;c.ids={1,2,3};c.used=i;c.pinned=i%2;c.dev_tag=i+1;
   c.gdn.assign(31,uint8_t(i));c.ple.assign(7,2);c.tails.assign(13,3);c.dead.assign(19,4);c.block_pos.assign(5,5);
   const std::vector<ConversationCheckpoint> view{c};
   auto plain=copy_checkpoints_beating(view);
   ConversationCheckpoint spare;spare.gdn.reserve(128);spare.gdn.assign(80,0);
   auto* bytes=spare.gdn.data();std::vector<ConversationCheckpoint> storage;storage.push_back(std::move(spare));
   auto reused=copy_checkpoints_beating(view,&storage);
   check(storage.empty()&&reused[0].gdn.data()==bytes,"reuse capacity from a dropped checkpoint");
   check(reused[0].ids==plain[0].ids&&reused[0].gdn==plain[0].gdn&&reused[0].ple==plain[0].ple&&reused[0].tails==plain[0].tails&&reused[0].dead==plain[0].dead&&reused[0].block_pos==plain[0].block_pos&&reused[0].used==c.used&&reused[0].pinned==c.pinned&&reused[0].dev_tag==c.dev_tag,"pooled state and metadata equal ordinary copy");
   check(view[0].gdn==c.gdn,"source checkpoint remains untouched");
 }
 check(joins==128,"join each source checkpoint before both copy paths");
 for(int i=0;i<64;++i)std::thread([]{check(copy_nonblocking(nullptr,nullptr,0)==cudaSuccess,"copy");check(order_after_queued()==cudaSuccess,"event ordering");}).join();
 check(created==1&&live.size()==1,"64 exited workers retain at most one reusable stream");
 std::atomic<int> ready{0};std::atomic<bool> go{false};std::vector<std::thread> threads;
 for(int i=0;i<16;++i)threads.emplace_back([&]{for(int d:{0,2,3}){device=d;check(copy_nonblocking(nullptr,nullptr,0)==cudaSuccess,"per-device copy");}++ready;while(!go.load())std::this_thread::yield();});
 while(ready.load()!=16)std::this_thread::yield();go=true;for(auto& t:threads)t.join();
 check(created<=48&&errors==0,"pooled streams bounded by peak concurrent workers and devices");
 const int held=created;
 for(int i=0;i<64;++i)std::thread([]{for(int d:{0,2,3}){device=d;check(copy_nonblocking(nullptr,nullptr,0)==cudaSuccess,"reuse after peak");}}).join();
 check(created==held,"no growth after 64 further sequential workers");
 std::thread([]{device=99;fail_get=true;check(copy_nonblocking(nullptr,nullptr,0)==failure,"get-device failure");fail_get=false;fail_create=true;check(copy_nonblocking(nullptr,nullptr,0)==failure,"create failure");fail_create=false;fail_copy=true;check(copy_nonblocking(nullptr,nullptr,0)==failure,"copy failure");fail_copy=false;fail_sync=true;check(copy_nonblocking(nullptr,nullptr,0)==failure,"sync failure");fail_sync=false;}).join();
 check(errors==0&&created==int(live.size()),"valid per-device ownership after error paths");
 std::puts("PASS: 64 exact pooled-checkpoint cases, join-before-copy, bounded worker/device lifetime and errors");
}
