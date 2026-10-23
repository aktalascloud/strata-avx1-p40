// Windows-only NUMA preference for the existing pinned arena. No CPU affinity changes.
#pragma once
#include <cstdint>
#include <cstdlib>
#include <limits>
#include <string>
#include <vector>

namespace strata::platform::win_numa {
struct Node { int id; uint64_t free_bytes; bool has_cpu; };
struct Decision { int node = -1; bool requested = false; std::string why; };
inline Decision choose(const char* mode, const std::vector<Node>& nodes, int gpu_node, uint64_t bytes) {
    Decision d;
    if (mode == nullptr || *mode == '\0' || std::string(mode) == "off") return d;
    d.requested = true;
    int wanted = -1;
    if (std::string(mode) == "gpu" || std::string(mode) == "auto") {
        wanted = gpu_node;
        if (wanted < 0) { d.why = "GPU host NUMA node unknown; ordinary allocation"; return d; }
    } else {
        unsigned value = 0;
        for (const char* p = mode; *p; ++p) {
            if (*p < '0' || *p > '9' || value > (65535u - unsigned(*p-'0')) / 10u) {
                d.why = "invalid STRATA_WIN_NUMA_NODE (off, gpu or a node number); ordinary allocation"; return d;
            }
            value = value * 10 + unsigned(*p-'0');
        }
        wanted = int(value);
    }
    int count = 0; const Node* selected = nullptr;
    for (const Node& n : nodes) { if (n.has_cpu) ++count; if (n.has_cpu && n.id == wanted) selected = &n; }
    if (count < 2) { d.why = "fewer than two CPU NUMA nodes; ordinary allocation"; return d; }
    if (selected == nullptr) { d.why = "requested NUMA node has no CPUs; ordinary allocation"; return d; }
    constexpr uint64_t headroom = 4ull << 30;
    if (bytes > selected->free_bytes || selected->free_bytes - bytes < headroom) {
        d.why = "preferred NUMA node lacks arena plus 4 GiB headroom; ordinary allocation"; return d;
    }
    d.node = wanted;
    d.why = "NUMA node " + std::to_string(wanted) + " preferred (Windows may fall back); CPU placement unchanged";
    return d;
}
} // namespace strata::platform::win_numa

#if defined(_WIN32)
#include <windows.h>
#include <psapi.h>
namespace strata::platform::win_numa {
inline Decision probe(const char* mode, int gpu_node, uint64_t bytes) {
    if (mode == nullptr || *mode == '\0' || std::string(mode) == "off") return {};
    ULONG highest = 0; std::vector<Node> nodes;
    if (!GetNumaHighestNodeNumber(&highest) || highest > 1024) {
        return {-1, true, "Windows NUMA topology unavailable; ordinary allocation"};
    }
    for (ULONG n = 0; n <= highest; ++n) {
        GROUP_AFFINITY mask{}; ULONGLONG available = 0;
        if (GetNumaNodeProcessorMaskEx(USHORT(n), &mask) && mask.Mask != 0 &&
            GetNumaAvailableMemoryNodeEx(USHORT(n), &available)) nodes.push_back({int(n), available, true});
    }
    return choose(mode, nodes, gpu_node, bytes);
}
inline std::string placement(void* base, SIZE_T bytes, int preferred) {
    if (base == nullptr || bytes == 0 || preferred < 0) return {};
    constexpr SIZE_T page = 4096;
    const SIZE_T pages = (bytes - 1) / page + 1;
    const SIZE_T count = pages < 128 ? pages : 128;
    PSAPI_WORKING_SET_EX_INFORMATION info[128]{};
    for (SIZE_T i = 0; i < count; ++i) {
        const SIZE_T index = count == 1 ? 0 : ((pages - 1) / (count - 1)) * i;
        info[i].VirtualAddress = static_cast<unsigned char*>(base) + index * page;
    }
    if (!QueryWorkingSetEx(GetCurrentProcess(), info, DWORD(count * sizeof(info[0]))))
        return "NUMA page sample unavailable (error " + std::to_string(GetLastError()) + ")";
    unsigned local = 0, remote = 0, not_resident = 0;
    for (SIZE_T i = 0; i < count; ++i) {
        if (!info[i].VirtualAttributes.Valid) ++not_resident;
        else if (int(info[i].VirtualAttributes.Node) == preferred) ++local;
        else ++remote;
    }
    return "NUMA page sample local/remote/not-resident=" + std::to_string(local) + "/" +
        std::to_string(remote) + "/" + std::to_string(not_resident);
}
inline void* allocate(SIZE_T bytes, DWORD flags, const Decision& d, std::string& report) {
    if (d.node >= 0) {
        void* p = VirtualAllocExNuma(GetCurrentProcess(), nullptr, bytes, flags, PAGE_READWRITE, DWORD(d.node));
        if (p != nullptr) { report = d.why + "; " + placement(p, bytes, d.node); return p; }
        const DWORD error = GetLastError();
        report = "NUMA allocation refused (error " + std::to_string(error) + "); ordinary allocation";
    } else if (d.requested) report = d.why;
    void* p = VirtualAlloc(nullptr, bytes, flags, PAGE_READWRITE);
    // Preserve the ordinary allocation's last error for the existing large-page diagnostic.
    const DWORD error = GetLastError(); SetLastError(error); return p;
}
} // namespace strata::platform::win_numa
#endif
