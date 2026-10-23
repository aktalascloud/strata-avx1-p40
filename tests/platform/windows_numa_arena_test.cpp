#include "strata/platform/win_numa_arena.hpp"
#include <cstdio>
#include <cstring>
using namespace strata::platform::win_numa;
#define CHECK(x) do { ++cases; if (!(x)) { std::fprintf(stderr,"FAIL line %d: %s\n",__LINE__,#x); return 1; } } while(0)
int main() {
    int cases = 0;
    const uint64_t gib = 1ull << 30;
    const std::vector<Node> two{{0,128*gib,true},{3,128*gib,true}};
    CHECK(!choose(nullptr,two,0,gib).requested);
    CHECK(!choose("off",two,0,gib).requested);
    CHECK(choose("gpu",two,3,gib).node==3);
    CHECK(choose("auto",two,0,gib).node==0);
    CHECK(choose("0",two,-1,gib).node==0);
    CHECK(choose("3",two,-1,gib).node==3);
    CHECK(choose("gpu",two,-1,gib).node<0);
    CHECK(choose("1",two,0,gib).node<0);
    CHECK(choose("3",{{0,128*gib,true},{3,128*gib,false}},0,gib).node<0);
    CHECK(choose("0",{{0,128*gib,true}},0,gib).node<0);
    CHECK(choose("0",two,0,125*gib).node<0);
    CHECK(choose("0",two,0,124*gib).node==0);
    CHECK(choose("0",two,0,~uint64_t(0)).node<0);
    CHECK(choose("65536",two,0,gib).node<0);
    CHECK(choose("99999999999999999999",two,0,gib).node<0);
    CHECK(choose("-1",two,0,gib).node<0);
    CHECK(choose(" 0",two,0,gib).node<0);
    CHECK(choose("0x0",two,0,gib).node<0);
    DWORD_PTR before=0,system=0,after=0,system_after=0;
    CHECK(GetProcessAffinityMask(GetCurrentProcess(),&before,&system));
    CHECK(!probe("off",-1,gib).requested);
    // Small real Win32 API positive control. This does not claim a two-node host or enable production policy.
    GROUP_AFFINITY mask{};
    CHECK(GetNumaNodeProcessorMaskEx(0,&mask) && mask.Mask);
    const SIZE_T bytes=2*1024*1024;
    std::string note;
    void* memory=allocate(bytes,MEM_COMMIT|MEM_RESERVE,Decision{0,true,"test node0 preferred"},note);
    CHECK(memory!=nullptr);
    std::memset(memory,0x5a,bytes);
    const auto* data=static_cast<const unsigned char*>(memory);
    bool intact=true; for(SIZE_T i=0;i<bytes;++i) if(data[i]!=0x5a){intact=false;break;}
    CHECK(intact);
    const std::string sample=placement(memory,bytes,0);
    CHECK(sample.find("NUMA page sample local/remote/not-resident=")!=std::string::npos);
    CHECK(VirtualFree(memory,0,MEM_RELEASE));
    CHECK(GetProcessAffinityMask(GetCurrentProcess(),&after,&system_after));
    CHECK(before==after && system==system_after);
    std::printf("Windows NUMA arena: %d cases PASS; no CPU affinity changes; %s\n",cases,sample.c_str());
    return 0;
}
