// CPU arithmetic parity on valid GGML rows. No model, GPU, pinning, or unquantized-weight reference.
#include "ggml.h"
#include "ggml-cpu.h"
#include "ggml-quants.h"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <vector>

namespace {
constexpr int kCases = 16;
constexpr double kAbsTolerance = 1e-4, kRelTolerance = 1e-4;

uint64_t random_bits(uint64_t& state) {
    uint64_t value = (state += UINT64_C(0x9e3779b97f4a7c15));
    value = (value ^ (value >> 30)) * UINT64_C(0xbf58476d1ce4e5b9);
    value = (value ^ (value >> 27)) * UINT64_C(0x94d049bb133111eb);
    return value ^ (value >> 31);
}

float uniform(uint64_t& state) {
    return static_cast<float>(random_bits(state) >> 40) * (2.0f / 16777216.0f) - 1.0f;
}

void make_inputs(int which, int n, std::vector<float>& weights, std::vector<float>& activations) {
    uint64_t state = UINT64_C(0x20261020c001d00d) + static_cast<uint64_t>(which) * 12347 + n;
    weights.resize(n);
    activations.resize(n);
    for (int i = 0; i < n; ++i) {
        const float u = uniform(state), v = uniform(state);
        float w = 0.05f * u, y = v;
        switch (which) {
            case 0: w = 0; break;
            case 1: y = 0; break;
            case 2: w = 0.125f; y = 0.25f; break;
            case 3: w = (i & 1) ? -0.125f : 0.125f; y = (i & 1) ? -0.25f : 0.25f; break;
            case 4: w = i == n / 3 ? -0.75f : 0; break;
            case 5: y = i == n - 1 ? 0.75f : 0; break;
            case 6: y = 0.5f * u; break;
            case 7: y = -0.5f * u; break;
            case 8: w = static_cast<float>(i % 15 - 7) * 0.003f; y = static_cast<float>(i % 11 - 5) * 0.1f; break;
            case 9: y = (i & 1) ? -1.0f : 1.0f; break;
            case 10: w = 0.03f * u; y = 0.75f * v; break;
            case 11: w = 0.25f * u; y = 2.0f * v; break;
            case 12: w = 0.001f * u; y = 0.5f * v; break;
            case 13: w *= (i % 7 == 0) ? 8.0f : 0.015625f; break;
            case 14: w = 0.015f * (1.0f + u); y = 0.5f * (1.0f + v); break;
            case 15: w = 0.125f * u; y = (i % 3 == 0) ? -2.0f * v : 0.125f * v; break;
        }
        weights[i] = w;
        activations[i] = y;
    }
}

// Allocation is aligned for float/half access, including types whose CPU trait is an identity conversion.
struct Row {
    explicit Row(size_t size) : bytes(size), storage((size + sizeof(uint64_t) - 1) / sizeof(uint64_t)) {}
    void* data() { return storage.data(); }
    const void* data() const { return storage.data(); }
    size_t bytes;
    std::vector<uint64_t> storage;
};

bool dequantize(ggml_type type, const Row& source, std::vector<float>& output) {
    if (type == GGML_TYPE_Q8_K) {
        dequantize_row_q8_K(static_cast<const block_q8_K*>(source.data()), output.data(),
                            static_cast<int64_t>(output.size()));
        return true;
    }
    if (type == GGML_TYPE_F32) {
        if (source.bytes != output.size() * sizeof(float)) return false;
        std::memcpy(output.data(), source.data(), source.bytes);
        return true;
    }
    const auto* traits = ggml_get_type_traits(type);
    if (traits == nullptr || traits->to_float == nullptr) return false;
    traits->to_float(source.data(), output.data(), static_cast<int64_t>(output.size()));
    return true;
}

int check_type(ggml_type type) {
    const char* name = ggml_type_name(type);
    const auto* traits = ggml_get_type_traits_cpu(type);
    if (traits == nullptr || traits->vec_dot == nullptr) {
        std::fprintf(stderr, "FAIL %s: CPU vec_dot is unavailable\n", name);
        return 1;
    }
    const ggml_type activation_type = traits->vec_dot_type;
    const auto* activation_traits = ggml_get_type_traits_cpu(activation_type);
    if (activation_traits == nullptr || activation_traits->from_float == nullptr) {
        std::fprintf(stderr, "FAIL %s: production activation converter is unavailable\n", name);
        return 1;
    }

    std::printf("CPU parity: %s x %s: initialize quantizer\n", name, ggml_type_name(activation_type));
    const auto started = std::chrono::steady_clock::now();
    ggml_quantize_init(type);
    int failures = 0, checks = 0;
    double max_abs = 0, max_bound_fraction = 0, max_float_abs = 0;
    for (int n : {256, 2560}) {
        if (n % ggml_blck_size(type) != 0 || n % ggml_blck_size(activation_type) != 0) {
            std::fprintf(stderr, "FAIL %s: n=%d violates a weight/activation block size\n", name, n);
            ++failures;
            continue;
        }
        std::vector<float> source, input, weight_ref(n), activation_ref(n), importance(n, 1.0f);
        Row weight_row(ggml_row_size(type, n)), activation_row(ggml_row_size(activation_type, n));
        for (int which = 0; which < kCases; ++which) {
            make_inputs(which, n, source, input);
            const size_t written = ggml_quantize_chunk(type, source.data(), weight_row.data(), 0, 1, n,
                ggml_quantize_requires_imatrix(type) ? importance.data() : nullptr);
            if (written != weight_row.bytes) {
                std::fprintf(stderr, "FAIL %s n=%d case=%d: quantizer wrote %zu, expected %zu bytes\n",
                             name, n, which, written, weight_row.bytes);
                ++failures;
                continue;
            }
            activation_traits->from_float(input.data(), activation_row.data(), n);

            if (!dequantize(type, weight_row, weight_ref) ||
                !dequantize(activation_type, activation_row, activation_ref)) {
                std::fprintf(stderr, "FAIL %s n=%d case=%d: independent operand dequantizer unavailable\n",
                             name, n, which);
                ++failures;
                continue;
            }

            // Quantization affects both operands. Compare arithmetic on their decoded values, never on source floats.
            double reference = 0;
            float float_reference = 0;
            bool finite = true;
            for (int i = 0; i < n; ++i) {
                finite = finite && std::isfinite(weight_ref[i]) && std::isfinite(activation_ref[i]);
                reference += static_cast<double>(weight_ref[i]) * static_cast<double>(activation_ref[i]);
                float_reference += weight_ref[i] * activation_ref[i];
            }
            float got = 0;
            traits->vec_dot(n, &got, 0, weight_row.data(), 0, activation_row.data(), 0, 1);
            const double error = std::fabs(static_cast<double>(got) - reference);
            const double bound = kAbsTolerance + kRelTolerance * std::fabs(reference);
            const bool ok = finite && std::isfinite(reference) && std::isfinite(float_reference) &&
                            std::isfinite(got) && error <= bound;
            max_abs = std::fmax(max_abs, error);
            max_bound_fraction = std::fmax(max_bound_fraction, error / bound);
            max_float_abs = std::fmax(max_float_abs, std::fabs(static_cast<double>(float_reference) - reference));
            ++checks;
            if (!ok) {
                std::fprintf(stderr,
                    "FAIL %s n=%d case=%d: got=%.9g decoded-double=%.17g decoded-float=%.9g error=%.6g bound=%.6g finite=%d\n",
                    name, n, which, got, reference, float_reference, error, bound, static_cast<int>(finite));
                ++failures;
            }
        }
    }
    ggml_quantize_free(); // Keep only one IQ codebook allocation alive at a time.
    const double elapsed = std::chrono::duration<double>(std::chrono::steady_clock::now() - started).count();
    std::printf("%s: %d checks, max_abs=%.6g, max_bound_fraction=%.6g, float_accum_abs=%.6g, %.3fs: %s\n",
                name, checks, max_abs, max_bound_fraction, max_float_abs, elapsed, failures ? "FAIL" : "PASS");
    return failures;
}
} // namespace

int main() {
    setvbuf(stdout, nullptr, _IONBF, 0);
    ggml_cpu_init();
    static_assert(static_cast<int>(GGML_TYPE_Q2_0) == 42, "DavidAU Q2_0 must retain GGUF type ID 42");
    const ggml_type types[] = {
        GGML_TYPE_Q2_0, GGML_TYPE_IQ2_S, GGML_TYPE_IQ3_XXS, GGML_TYPE_IQ3_S,
        GGML_TYPE_IQ4_XS, GGML_TYPE_IQ4_NL, GGML_TYPE_Q4_K, GGML_TYPE_Q5_K,
        GGML_TYPE_Q6_K, GGML_TYPE_Q8_0, GGML_TYPE_F16, GGML_TYPE_BF16, GGML_TYPE_F32,
    };
    int failures = 0;
    for (ggml_type type : types) failures += check_type(type);
    std::printf("CPU format parity: 13 types x 2 lengths x %d cases; arithmetic tolerance %.1e + %.1e*abs(decoded-double); failures=%d\n",
                kCases, kAbsTolerance, kRelTolerance, failures);
    return failures ? 1 : 0;
}
