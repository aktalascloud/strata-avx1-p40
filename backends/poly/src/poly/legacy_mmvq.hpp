// SPDX-License-Identifier: MIT
// PolyStrata's optional multi-matrix API over the reviewed Strata kernel library.
// False means nothing was launched, as its API specifies. Callers take their
// original per-matrix path; no unqualified foreign CUDA kernel is substituted.
#pragma once
#include "strata/kernels/native_mmvq.hpp"
#include "strata/poly/kernels.hpp"
namespace strata::kernels {
struct MmvqSlots { const void* w[8]; const void* x[8]; float* y[8]; };
inline bool native_mmvq_slots(int, const MmvqSlots&, int, int, int, void*) { return false; }
struct MmvqIds {
    const void* const* table;
    const int32_t* ids;
    std::size_t offset;
    const void* x;
    std::size_t x_stride;
    int x_every;
    float* y;
    std::size_t y_stride;
};
inline bool native_mmvq_ids_supported(int) { return false; }
inline bool native_mmvq_ids(int, const MmvqIds&, int, int, int, void*) { return false; }
inline void native_add_rms_norm_q8_1(float* x, const float* add, const float* w, float* y,
                                   void* q, int n, int rows, float eps, int, void* stream) {
    // Preserve the reference operations until the foreign fused kernel has its own parity proof.
    if (add) strata::poly::axpy(add, 1.0f, x, n * rows, true, stream);
    strata::poly::rms_norm(x, w, y, n, rows, eps, stream);
    native_quantize_q8_1(y, q, n, rows, stream);
}
}
