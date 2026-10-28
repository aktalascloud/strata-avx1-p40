// Scheduling parity for the semantically ported StrataFast PR16.
// No GPU/model, pinning, benchmark or timing-based assertions.
#include "strata/kernels/cpu/pool.hpp"
#include "strata/kernels/cpu/expert_layout.hpp"
#include "ggml.h"
#include "ggml-cpu.h"
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <random>
#include <string>
#include <vector>

namespace cpu = strata::kernels::cpu;
constexpr int kH = 2560, kFF = 640;

static int type(const char* name) {
    for (int t = 0; t < GGML_TYPE_COUNT; ++t) {
        const char* candidate = ggml_type_name((ggml_type) t);
        if (candidate != nullptr && std::strcmp(candidate, name) == 0) return t;
    }
    return -1;
}

static void blob(const cpu::NativeFmt& f, std::vector<uint8_t>& bytes) {
    std::mt19937 rng(12345);
    std::normal_distribution<float> nd(0.f, 0.02f);
    std::vector<float> row(kH), importance(kH, 1.f);
    auto quant = [&](int kind, uint8_t* dst, int width) {
        for (int i = 0; i < width; ++i) row[i] = nd(rng);
        ggml_quantize_chunk((ggml_type) kind, row.data(), dst, 0, 1, width,
                           ggml_quantize_requires_imatrix((ggml_type) kind) ? importance.data() : nullptr);
    };
    for (int i = 0; i < 2 * kFF; ++i) quant(f.gu_type, bytes.data() + i * f.gu_row, kH);
    for (int i = 0; i < kH; ++i) quant(f.d_type, bytes.data() + f.down_off + i * f.d_row, kFF);
}

int main() {
#ifdef _WIN32
    _putenv_s("STRATA_POOL_GUIDED", "1");
    if (std::getenv("STRATA_POOL_GUIDED_MIN") == nullptr) _putenv_s("STRATA_POOL_GUIDED_MIN", "128");
#else
    setenv("STRATA_POOL_GUIDED", "1", 1);
    if (std::getenv("STRATA_POOL_GUIDED_MIN") == nullptr) setenv("STRATA_POOL_GUIDED_MIN", "128", 1);
#endif
    ggml_cpu_init();
    int cases = 0;
    for (const auto pair : {std::pair{"iq3_s", "q2_0"}, std::pair{"q2_0", "q2_0"},
                            std::pair{"q8_0", "q8_0"}, std::pair{"iq3_s", "iq4_nl"}}) {
        const char* gu = pair.first; const char* down = pair.second;
        cpu::NativeFmt f; std::string error;
        if (!cpu::native_fmt(type(gu), type(down), kH, kFF, f, error)) {
            std::fprintf(stderr, "format: %s\n", error.c_str()); return 1;
        }
        std::vector<uint8_t> weights(f.bytes); blob(f, weights);
        auto padded = f; padded.up_off += 64; padded.down_off += 128; padded.bytes += 128;
        std::vector<uint8_t> scattered(padded.bytes);
        std::memcpy(scattered.data(), weights.data(), f.up_off);
        std::memcpy(scattered.data() + padded.up_off, weights.data() + f.up_off, f.down_off - f.up_off);
        std::memcpy(scattered.data() + padded.down_off, weights.data() + f.down_off, f.bytes - f.down_off);
        std::vector<float> x(kH);
        for (int i = 0; i < kH; ++i) x[i] = 0.1f * std::sin((float) i);
        cpu::ActQ aq[3];
        std::vector<std::vector<uint8_t>> native(3, std::vector<uint8_t>(cpu::kNativeActBytes));
        for (int t = 0; t < 3; ++t) {
            cpu::act_quant_any(x.data(), kH, aq[t]);
            if (!cpu::q2_native_kernels(f.gu_type)) cpu::native_quant_act(f, x.data(), native[t].data());
        }
        for (int setup : {1, 4, 14, -4}) {
            const int workers = std::abs(setup);
            cpu::ExpertPool pool(workers, false, setup > 0);
            for (int n : {0, 1, 4, 14, 97}) for (int nt : {1, 3}) {
                std::vector<cpu::ExpertJobMulti> jobs(n);
                std::vector<std::vector<float>> expected(n * nt, std::vector<float>(kH + 8, -777.f));
                std::vector<std::vector<float>> actual = expected;
                for (int e = 0; e < n; ++e) {
                    auto& j = jobs[e]; j.nt = nt;
                    j.blob = e % 2 ? scattered.data() : weights.data();
                    j.fmt = e % 2 ? &padded : nullptr;
                    for (int t = 0; t < nt; ++t) {
                        j.act[t] = &aq[t]; j.nact[t] = native[t].data();
                        j.out[t] = expected[e * nt + t].data();
                    }
                }
                pool.run_split_multi_native(f, jobs.data(), n);
                for (int round = 0; round < 3; ++round) {
                    for (int e = 0; e < n; ++e) for (int t = 0; t < nt; ++t)
                        jobs[e].out[t] = actual[e * nt + t].data();
                    pool.run_fused_native(f, jobs.data(), n);
                    for (int e = 0; e < n * nt; ++e) {
                        if (std::memcmp(expected[e].data(), actual[e].data(), (kH + 8) * sizeof(float))) {
                            std::fprintf(stderr, "mismatch %s/%s workers=%d n=%d nt=%d round=%d\n", gu, down, workers, n, nt, round);
                            return 1;
                        }
                        for (int i = 0; i < kH; ++i) if (!std::isfinite(actual[e][i])) return 2;
                        for (int i = kH; i < kH + 8; ++i) if (actual[e][i] != -777.f) return 3;
                    }
                    ++cases;
                }
            }
        }
    }
    std::printf("cpu_pool_guided_parity: %d bitwise scheduling/reset/batching/offset cases passed\n", cases);
    return 0;
}
