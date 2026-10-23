#pragma once

#include <cstdlib>

namespace strata {

// Process-local opt-out for callers that require the OS to place every thread.
// Only the exact value "1" opts out; an unset variable preserves the upstream path.
inline bool no_cpu_pin() noexcept {
    const char* value = std::getenv("STRATA_NO_CPU_PIN");
    return value != nullptr && value[0] == '1' && value[1] == '\0';
}

}  // namespace strata
