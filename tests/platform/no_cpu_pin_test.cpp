// Exercise production CPU placement with counted imports. No test path calls a Windows placement setter.
#include "strata/kernels/cpu/pool.hpp"
#include "strata/platform/cpu_pinning.hpp"
#include "../../src/kernels/cpu/pool_affinity_win.hpp"

#include <tlhelp32.h>
#include <algorithm>
#include <atomic>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <thread>
#include <vector>

namespace cpu = strata::kernels::cpu;

namespace {
std::atomic<unsigned> group_calls{0}, cpu_set_calls{0};
int failures = 0;

bool check(bool ok, const char* what) {
    if (!ok) {
        std::fprintf(stderr, "no_cpu_pin_test: %s (error %lu)\n", what, (unsigned long) GetLastError());
        ++failures;
    }
    return ok;
}

BOOL WINAPI count_group(HANDLE, const GROUP_AFFINITY*, PGROUP_AFFINITY) {
    ++group_calls;
    SetLastError(ERROR_ACCESS_DENIED);
    return FALSE;
}

BOOL WINAPI count_cpu_sets(HANDLE, const ULONG*, ULONG) {
    ++cpu_set_calls;
    SetLastError(ERROR_ACCESS_DENIED);
    return FALSE;
}

// Hook only this test executable's two import slots. SDK import libraries can group
// several imports in one object, so defining __imp_* symbols would cause duplicate symbols.
struct ImportHooks {
    struct Entry { void** slot; void* original; };
    std::vector<Entry> entries;

    bool install() {
        auto* image = reinterpret_cast<unsigned char*>(GetModuleHandleW(nullptr));
        const auto* dos = reinterpret_cast<const IMAGE_DOS_HEADER*>(image);
        if (dos->e_magic != IMAGE_DOS_SIGNATURE) return false;
        const auto* nt = reinterpret_cast<const IMAGE_NT_HEADERS64*>(image + dos->e_lfanew);
        if (nt->Signature != IMAGE_NT_SIGNATURE) return false;
        const DWORD rva = nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_IMPORT].VirtualAddress;
        if (!rva) return false;
        const auto* descriptor = reinterpret_cast<const IMAGE_IMPORT_DESCRIPTOR*>(image + rva);
        for (; descriptor->Name; ++descriptor) {
            if (!descriptor->OriginalFirstThunk) continue;
            const auto* names = reinterpret_cast<const IMAGE_THUNK_DATA64*>(image + descriptor->OriginalFirstThunk);
            auto* imports = reinterpret_cast<IMAGE_THUNK_DATA64*>(image + descriptor->FirstThunk);
            for (; names->u1.AddressOfData; ++names, ++imports) {
                if (IMAGE_SNAP_BY_ORDINAL64(names->u1.Ordinal)) continue;
                const auto* named = reinterpret_cast<const IMAGE_IMPORT_BY_NAME*>(image + names->u1.AddressOfData);
                void* replacement = nullptr;
                if (std::strcmp(reinterpret_cast<const char*>(named->Name), "SetThreadGroupAffinity") == 0)
                    replacement = reinterpret_cast<void*>(count_group);
                else if (std::strcmp(reinterpret_cast<const char*>(named->Name), "SetThreadSelectedCpuSets") == 0)
                    replacement = reinterpret_cast<void*>(count_cpu_sets);
                if (!replacement) continue;
                auto** slot = reinterpret_cast<void**>(&imports->u1.Function);
                DWORD protection = 0;
                if (!VirtualProtect(slot, sizeof(*slot), PAGE_READWRITE, &protection)) return false;
                void* original = InterlockedExchangePointer(slot, replacement);
                DWORD ignored = 0;
                if (!VirtualProtect(slot, sizeof(*slot), protection, &ignored)) return false;
                entries.push_back({slot, original});
            }
        }
        return entries.size() == 2;
    }

    ~ImportHooks() {
        for (const auto& entry : entries) {
            DWORD protection = 0;
            if (VirtualProtect(entry.slot, sizeof(*entry.slot), PAGE_READWRITE, &protection)) {
                InterlockedExchangePointer(entry.slot, entry.original);
                DWORD ignored = 0;
                VirtualProtect(entry.slot, sizeof(*entry.slot), protection, &ignored);
            }
        }
    }
};

struct Placement {
    GROUP_AFFINITY thread{};
    DWORD_PTR process_mask = 0, system_mask = 0;
    std::vector<ULONG> selected, defaults;
    std::vector<USHORT> groups;
};

bool read_placement(HANDLE thread, Placement& out) {
    if (!GetThreadGroupAffinity(thread, &out.thread) ||
        !GetProcessAffinityMask(GetCurrentProcess(), &out.process_mask, &out.system_mask)) return false;

    ULONG count = 0;
    if (!GetThreadSelectedCpuSets(thread, nullptr, 0, &count) &&
        GetLastError() != ERROR_INSUFFICIENT_BUFFER) return false;
    out.selected.resize(count);
    if (count && !GetThreadSelectedCpuSets(thread, out.selected.data(), count, &count)) return false;
    out.selected.resize(count);

    count = 0;
    if (!GetProcessDefaultCpuSets(GetCurrentProcess(), nullptr, 0, &count) &&
        GetLastError() != ERROR_INSUFFICIENT_BUFFER) return false;
    out.defaults.resize(count);
    if (count && !GetProcessDefaultCpuSets(GetCurrentProcess(), out.defaults.data(), count, &count)) return false;
    out.defaults.resize(count);

    USHORT group_count = GetActiveProcessorGroupCount();
    out.groups.resize(group_count);
    if (!GetProcessGroupAffinity(GetCurrentProcess(), &group_count, out.groups.data())) return false;
    out.groups.resize(group_count);
    std::sort(out.selected.begin(), out.selected.end());
    std::sort(out.defaults.begin(), out.defaults.end());
    std::sort(out.groups.begin(), out.groups.end());
    return true;
}

bool same(const Placement& a, const Placement& b) {
    return a.thread.Group == b.thread.Group && a.thread.Mask == b.thread.Mask &&
           a.process_mask == b.process_mask && a.system_mask == b.system_mask &&
           a.selected == b.selected && a.defaults == b.defaults && a.groups == b.groups;
}

bool unchanged(HANDLE thread, const Placement& before, const char* what) {
    Placement after;
    return check(read_placement(thread, after) && same(before, after), what);
}

bool process_threads(std::vector<DWORD>& ids) {
    const HANDLE snapshot = CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0);
    if (snapshot == INVALID_HANDLE_VALUE) return false;
    THREADENTRY32 entry{};
    entry.dwSize = sizeof(entry);
    bool ok = Thread32First(snapshot, &entry) != 0;
    if (ok) {
        do {
            if (entry.th32OwnerProcessID == GetCurrentProcessId()) ids.push_back(entry.th32ThreadID);
            entry.dwSize = sizeof(entry);
        } while (Thread32Next(snapshot, &entry));
        ok = GetLastError() == ERROR_NO_MORE_FILES;
    }
    CloseHandle(snapshot);
    std::sort(ids.begin(), ids.end());
    return ok;
}

void exercise_caller(int core, bool disabled) {
    Placement before;
    if (!check(read_placement(GetCurrentThread(), before), "read inherited caller placement")) return;
    const auto previous = cpu::pin_current_thread(core);
    check(!previous.valid, "a disabled or rejected host pin must not return a restorable assignment");
    unchanged(GetCurrentThread(), before, "host pin preserves inherited placement");
    cpu::restore_thread_affinity(previous);
    unchanged(GetCurrentThread(), before, "invalid restore preserves inherited placement");

    // An otherwise valid snapshot must also do nothing when pinning is disabled.
    cpu::ThreadAffinity synthetic;
    synthetic.valid = true;
    synthetic.cpu_sets.assign(before.selected.begin(), before.selected.end());
    cpu::restore_thread_affinity(synthetic);
    unchanged(GetCurrentThread(), before, "valid restore preserves inherited placement");

    check(!cpu::detail::set_thread_group_affinity(core, 7), "disabled or rejected worker pin reports false");
    unchanged(GetCurrentThread(), before, "worker helper preserves inherited placement");
    if (disabled) check(group_calls.load() == 0 && cpu_set_calls.load() == 0,
                        "disabled caller paths must make zero placement calls");
}

void exercise_pool(bool disabled) {
    Placement caller;
    std::vector<DWORD> before, during;
    if (!check(read_placement(GetCurrentThread(), caller), "read caller before pool") ||
        !check(process_threads(before), "enumerate threads before pool")) return;

    {
        cpu::ExpertPool pool(2, true, false);
        check(pool.workers() == 2, "production pool creates requested workers");
        if (check(process_threads(during), "enumerate production pool workers")) {
            unsigned observed = 0;
            for (DWORD id : during) {
                if (std::binary_search(before.begin(), before.end(), id)) continue;
                const HANDLE thread = OpenThread(THREAD_QUERY_INFORMATION, FALSE, id);
                if (!check(thread != nullptr, "open own pool worker for readback")) continue;
                Placement inherited;
                if (check(read_placement(thread, inherited), "read own pool worker placement")) {
                    check(inherited.process_mask == caller.process_mask &&
                          inherited.system_mask == caller.system_mask && inherited.defaults == caller.defaults &&
                          inherited.groups == caller.groups, "pool worker keeps inherited process scope");
                    check(inherited.thread.Group == caller.thread.Group && inherited.thread.Mask == caller.thread.Mask &&
                          inherited.selected == caller.selected, "pool worker keeps inherited thread mask and CPU Sets");
                    unchanged(thread, inherited, "pool worker placement stays unchanged during readback");
                    ++observed;
                }
                CloseHandle(thread);
            }
            check(observed == 2, "read back both production pool workers");
        }
    } // Join workers before checking counts, so every startup pin has finished.
    unchanged(GetCurrentThread(), caller, "pool lifetime preserves caller placement");
    if (disabled) check(group_calls.load() == 0 && cpu_set_calls.load() == 0,
                        "production pool must make zero placement calls");
}
} // namespace

int main(int argc, char** argv) {
    const bool disabled = argc == 1;
    if (!disabled && (argc != 2 || std::strcmp(argv[1], "--positive-control") != 0)) {
        std::fprintf(stderr, "usage: no_cpu_pin_test [--positive-control]\n");
        return 2;
    }
    ImportHooks hooks;
    if (!check(hooks.install(), "replace both placement imports in this test process")) return 1;
    if (!check(_putenv_s("STRATA_NO_CPU_PIN", disabled ? "1" : "0") == 0, "set process-local opt-in") ||
        !check(strata::no_cpu_pin() == disabled, "read exact process-local opt-in")) return 1;

    const auto cores = cpu::physical_cores(false);
    if (!check(!cores.empty(), "find valid target CPU")) return 1;
    ULONG id = 0;
    if (!check(cpu::detail::cpu_set_for_core(cores.front(), id), "resolve valid target CPU Set")) return 1;

    Placement original;
    if (!check(read_placement(GetCurrentThread(), original), "read original placement")) return 1;
    exercise_caller(cores.front(), disabled);
    std::thread inherited([&] { exercise_caller(cores.front(), disabled); });
    inherited.join();
    exercise_pool(disabled);
    unchanged(GetCurrentThread(), original, "final process/thread placement matches original");
    if (disabled) check(group_calls.load() == 0 && cpu_set_calls.load() == 0, "zero placement calls overall");
    else check(group_calls.load() >= 4 && cpu_set_calls.load() >= 4,
               "positive control reaches both real production import paths");

    std::printf("no_cpu_pin_test: %s: group calls=%u, CPU Set calls=%u, failures=%d; no OS placement setters executed\n",
                disabled ? "disabled" : "positive control", group_calls.load(), cpu_set_calls.load(), failures);
    return failures ? 1 : 0;
}
