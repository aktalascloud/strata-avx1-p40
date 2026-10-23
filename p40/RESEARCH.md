# External sources reviewed

Pinned source review on2026-10-22. This table records applicability, not measured gains on this model.
The audit sampled up to100 recent default-branch commits/issues per large repository, not every historical branch.



| Источник / точный HEAD | Применимость и действие |
|---|---|
| [Niko1221/Strata](https://github.com/Niko1221/Strata/tree/011c9e600a93bbc9fd451c563501b5831c32bbca) `011c9e600a93` | Основной native CUDA/AVX1 engine; точный SHA собран и проверен. |
| [TheHubUser4860938/Strata](https://github.com/TheHubUser4860938/Strata/tree/e6a54f584a89dc486787596d7df661d380763a0a) `e6a54f584a89` | Собственные memory/soul/frontend изменения; C++/CUDA ускорения для текущего пути не обнаружены. Memory не включена. |
| [madsteph74/pascallama.cpp](https://github.com/madsteph74/pascallama.cpp/tree/e6a28bcba735f702584520362a96f670224ae5ea) `e6a28bcba735` | Полный sm61 J96/unroll overlay уже сохранён, собран и проверен; повторно поверх него legacy patch не применять. |
| [andrewdhannah/vulkan-polaris-llama](https://github.com/andrewdhannah/vulkan-polaris-llama/tree/e29790e07978c5826d23752d4416a173e5b731db) `e29790e07978` | Заявленные 10x относятся к переносу маленькой модели с CPU на RX570; Vulkan очереди не являются AVX1 ускорением Strata. |
| [ponyol/llama.cpp.patch.speed](https://github.com/ponyol/llama.cpp.patch.speed/tree/4bcc0364b3ab8484b3693aa0b31739e63f635b9c) `4bcc0364b3ab` | GGML graph fusions/reuse/prefetch сопоставлены с native GR/GDN/IQ. Не все generic GGML операции вызываются Strata. |
| [cubetitled-ui/llama.cpp](https://github.com/cubetitled-ui/llama.cpp/tree/124ac98237f6701ffc30cb5708a7220207f14031) `124ac98237f6` | Часть CUDA/graph изменений родственная предыдущему fork; CPU kernel не даёт нового AVX1 пути. Не переносить recurrence со сменой арифметики. |
| [N1k0droid/avx-llama-manager](https://github.com/N1k0droid/avx-llama-manager/tree/d066ba3ca76dc28b56a7bbdc9309c8a512f54824) `d066ba3ca76d` | Менеджер запуска и флаги; собственного ускоряющего kernel нет. |
| [superexp1/llama2c-avx2-tuning](https://github.com/superexp1/llama2c-avx2-tuning/tree/d04f9740b0aafbdee3f33edeb68c7ad3f846fc0e) `d04f9740b0aa` | PGO/LTO идея реально проверена отдельно и вместе. AVX2/FMA/fast-math и pinning не включены. |
| [guarismo/llama-cuda-builder](https://github.com/guarismo/llama-cuda-builder/tree/78d32c7aeae5357600336aefa420b00a15ec36b1) `78d32c7aeae5` | Рецепт FX8350/RTX3060: не переносить march/sm86 на Ivy/P40. Ivy ISA уже задана точно. |
| [lassehol/llama.cpp-ph2](https://github.com/lassehol/llama.cpp-ph2/tree/9168b4db6f36562c1106359e222ce36bbca2a64b) `9168b4db6f36` | Старая Phenom/Fermi/CUDA8 ветка; sm21 и её ограничения не являются оптимизацией sm61. |
| [dhaern/VelociQ8](https://github.com/dhaern/VelociQ8/tree/fadbc689932795ecac52ed94d8cfb1cddf3fa4b6) `fadbc6899327` | Закрытые Q8A64 kernels и AVX2/FMA; исходного совместимого kernel для текущих GGUF/AVX1 нет. |
| [cjml555/llama-native](https://github.com/cjml555/llama-native/tree/98703b3536e00b4bf47b5c2d271832f701b6bda3) `98703b3536e0` | Build wrapper с native/LTO; соответствующие compiler сочетания проверены на этой машине. |
| [layfhaker/llama.cpp-x86-neon](https://github.com/layfhaker/llama.cpp-x86-neon/tree/d79c52fcf72aec5e712502000f61cddab8bb2e4b) `d79c52fcf72a` | STQ1_0 AVX2 patch: другой формат и ISA, текущие IQ3_S/Q2_0 не переинтерпретировать. |
| [ikawrakow/ik_llama.cpp](https://github.com/ikawrakow/ik_llama.cpp/tree/55d5dd9f215df6f3c93a863aa0bcaf68599fd7eb) `55d5dd9f215d` | 10 выбранных PR сохранены. #2721 имеет тот же SASS на sm61; #2701 не выбирает sm61. Cache/PLE/Windows pinning рассмотрены отдельно. |
| [JakeATX/llamAmpere](https://github.com/JakeATX/llamAmpere/tree/5c9c97aa8cc1ebb8b7a8af68334c368f7b7e89ef) `5c9c97aa8cc1` | IQ staging, q8 producer reuse, add/RMS fusions, GDN state gather сопоставлены с native. sm86/width5–8 и новые KV форматы не переносить вслепую. |
| [pauldmartinphd/llm-performance-engineering-notebook](https://github.com/pauldmartinphd/llm-performance-engineering-notebook/tree/76eb7c0936ab04fedd487c2db17a3176a49f44f7) `76eb7c0936ab` | Полезна методика прогретого измерения. Собственный patch — multi-GPU prefill, автор не заявляет decode прирост. AMD NPS1 не заменяет тест двух Xeon. |
| [shinbunbun/llama-cpp-p100-patches](https://github.com/shinbunbun/llama-cpp-p100-patches/tree/28ac0d68dc3f3d840a6d0437028c18e811492b05) `28ac0d68dc3f` | Все45 patch файлов сохранены с Git blob proof; подробная карта ниже. IQ staging и GR/QFUSE проверены на P40. |
| [christopherrobertbrooks-tech/volta-kernel-bakeoff](https://github.com/christopherrobertbrooks-tech/volta-kernel-bakeoff/tree/7d2bfb48a1336c34111f6df52ab6cfb59f924d4e) `7d2bfb48a133` | 4 fusion scripts сохранены, не исполнялись. Producer identity обязателен: ранний q8 cache имел stale-data ошибку. WMMA требует sm70. |
| [christopherrobertbrooks-tech/legacy-gpu-llm-notes](https://github.com/christopherrobertbrooks-tech/legacy-gpu-llm-notes/tree/0bcff057cd6bb7b3de5fff9a361e2ecbcd51b9dd) `0bcff057cd6b` | Изучены GTX1070/Strata findings. V100 Coder целиком в VRAM и урезанное число экспертов не сравнимы с полной текущей моделью. |
| [1115714829/llama.cpp-v100](https://github.com/1115714829/llama.cpp-v100/tree/a8cc639d01b33618c74fe87f785c0e6077bc2bcc) `a8cc639d01b3` | V100/мульти-GPU kernels и GPL3 реализация. Не копировать sm70 tensor-core код/лицензию в MIT пакет без отдельного анализа. |
| [qr0n/p100-llama-cpp](https://github.com/qr0n/p100-llama-cpp/tree/dc5c644c45f35167edfa041110f8c9bd75404b34) `dc5c644c45f3` | Все18 patch файлов + README сохранены с Git blob proof; карта ниже. GP100 FP16 ветви не принуждать на P40. |
| [sarge18/p40-llm-engine-bakeoff](https://github.com/sarge18/p40-llm-engine-bakeoff/tree/0c7242bce32e1ac2c8dc26a3d39952a6b8fb6485) `0c7242bce32e` | Запрошенные7 sweep файлов и финальный REPORT прочитаны. 2P40/Broadwell/Linux и IQ2_XS отличаются. Ошибочная Vulkan метка у автора исправлена. |
| [cycle-five/pascal-mmq-autorunner](https://github.com/cycle-five/pascal-mmq-autorunner/tree/76dab0aee6f139ebb7f8307dac609c201a2e6070) `76dab0aee6f1` | 72 MMQ sweep строки: +16.31% относится к prefill Q4_0 Llama2-7B, не decode IQ3_S. J64/I128 нельзя объявить выигрышем этой модели. |
| [ArtyomITA/bonsai2-ternary-pascal](https://github.com/ArtyomITA/bonsai2-ternary-pascal/tree/a3be1f5a09f3e2659120c3b6bdc17f3adeaec412) `a3be1f5a09f3` | Полный1164-строчный patch сохранён. PQ2_0/FWHT — другой формат; native graphs/GR/GDN уже есть. Не менять top_k64 на32 ради ветви. |
| [Warabii1248/qwen38-v100-patches](https://github.com/Warabii1248/qwen38-v100-patches/tree/adf692aa236cc8cd28537f1ca246bc89d46be579) `adf692aa236c` | Все56 feature patches сохранены; применимость по группам ниже. Persistent GDN требует72/80SM, P40 имеет30: guard сохраняется. |
| [sirfyyn/FastLocalExperts](https://github.com/sirfyyn/FastLocalExperts/tree/d05482eb0bed6c52af9b3ce89a3675bae2f35f59) `d05482eb0bed` | Прочитаны ENV, NOTICE-Strata, CPU diff и frequency admission/eviction. AVX2+FMA Q2 и AVX512 не подходят. Native Strata уже имеет AVX1 и adaptive overlap/cache. |


The active patch list and actual measured deltas are in PATCHES.md. Do not copy Ampere/Volta/P100 flags blindly to SM6.1.
