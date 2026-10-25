# Strata Legacy GPU

[English](README.md) · [Русский](README.ru.md) · [Релиз Windows](https://github.com/aktalascloud/strata-legacy-gpu/releases/latest)

[Strata](https://github.com/Niko1221/Strata) для **AVX1/Ivy Bridge и Tesla P40 (sm_61)**. Проверенный движок **0.1.49.3**, официальная основа [`7dd5cf18e68c`](https://github.com/Niko1221/Strata/commit/7dd5cf18e68c639a8773e096c5c79f971ea2a9f5). Текущий ZIP — проверенный пакет **Qwen/P40**; новые адаптеры пока экспериментальные.

## Модели, бэкенды и MTP

| Модель / GPU | Бэкенд | Состояние |
| --- | --- | --- |
| Qwen3.8 Flash Next / P40 | Strata CUDA + эксперты на CPU | Проверено; MTP Q2, два draft-токена |
| GLM 5.3 Flash (`glm5-next`) | Дополнительный Poly CUDA | Экспериментально; нужна обученная NextN-голова |
| GLM-DSA, DeepSeek V3/V4 | Встроенный GGML CPU / Vulkan | Экспериментально; MTP требует совместимых NextN-тензоров |
| Polaris / RX580 8 ГБ | Встроенный GGML Vulkan + AVX1 CPU | Экспериментально; на самой RX580 ещё не проверено |

**Для MTP нужна совместимая обученная голова.** Строгий запрос MTP отклоняется, если её нет; поиск повторов и отдельная вспомогательная модель не называются нативным MTP. В пути Poly для DeepSeek V4 графа MTP нет; для него нужен совместимый путь GGML. Новые веса для разработки не скачиваются. RX580 использует Vulkan, а не современный HIP; для 8 ГБ нужна выгрузка части вычислений на CPU.

Источники: [Xolotl](https://github.com/Indras-Mirror/Xolotl), [PolyStrata](https://github.com/VecSzn/PolyStrata), [polaris-local-ai](https://github.com/AvilaCarlosDev/polaris-local-ai) · [Project Maya](https://github.com/mw00/project-maya).

## Замеры Qwen / P40

**16.45 → 48.77 токена/с** в движке; полный API: 11.65 → 44.65. Замер 2026-10-25, движок 0.1.49.3, `45B99DC2`. Исторический холодный ответ без MTP против прогретого MTP/xhigh: разные режимы, не одновременный A/B. Полные 128К и новые модели не измерены. [Методика и доказательства CPU/GPU](p40/BENCHMARKS.md).

## Быстрый запуск Windows

1. Скачайте ZIP и `SHA256SUMS.txt` из [Releases](https://github.com/aktalascloud/strata-legacy-gpu/releases), проверьте SHA-256 и распакуйте.
2. Нужен совместимый с Pascal драйвер NVIDIA с поддержкой CUDA 12.9. Запустите **`INSTALL.cmd`**, затем **`START.cmd`**. GGUF/mmproj/MTP загружаются с **докачкой и SHA-256**, без исходного checkpoint. Около **85,6 ГБ загрузки / 100 ГБ на диске**.
3. Панель: `http://127.0.0.1:8093/`; OpenAI API: `http://127.0.0.1:8093/v1`. **`STOP.cmd`** штатно завершает запросы; **`CHECK.cmd`** проверяет пакет без загрузки весов. **`AUTOSTART.cmd`** регистрирует независимые задачи Windows для запуска и управления; Codex не требуется.

Профиль: **128К / KV q4_0 / авторский xhigh / MTP Q2 / `--spec 3` / 14 потоков / PLE RAM / CPU vision**. Дополнительно: `INSTALL.cmd --models-dir D:\Models --port 8094`; `--numa-node 0` выбирайте после проверки топологии.

CPU: Clang **O3, `-march=ivybridge -mtune=ivybridge`**, базовый путь без AVX2/FMA/F16C, строгая FP. GPU: **CUDA 12.9, O3, sm_61**; host MSVC `/O2 /Ob3 /favor:INTEL64 /fp:precise`. Применены исправления AVX1/управления/NUMA, Pascal MMQ I64/J96, B6, EXPDEC, IQ staging, QFUSE/GR и проверенные исправления кэша/prefill. [Патчи](p40/PATCHES.md) · [Границы проверки](p40/INSTALLATION-VERIFICATION.md).

Уведомления MIT и условия зависимостей: [лицензии](THIRD_PARTY_NOTICES.md). VC Runtime получается у Microsoft с проверкой подписи; лицензии моделей действуют отдельно. В релизе нет весов, ключей, приватных настроек, логов, кэшей и компиляторов.
