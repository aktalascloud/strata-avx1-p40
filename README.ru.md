# Strata Legacy GPU

[English](README.md) · [Русский](README.ru.md) · [Windows ZIP](https://github.com/aktalascloud/strata-legacy-gpu/releases/latest)

**Локальные LLM на процессорах AVX1, NVIDIA P40 и AMD Polaris/RX580.** Один пакет для Windows, OpenAI-совместимый API, независимый автозапуск.

| Железо | Движок | Проверка |
| --- | --- | --- |
| Ivy Bridge / AVX1, без AVX2 и BMI2 | CPU | Численные проверки, MTP и API на тестовых данных |
| Tesla P40 / Pascal sm_61 | CUDA 12.9 | Рабочая native Qwen; численные проверки CUDA-компонента |
| Polaris / RX580 8 ГБ | Vulkan + выгрузка на CPU | Экспериментальный движок включён; проверка на RX580 пока не выполнена |

**Модели:** Qwen3.8 Flash Next, GLM-5.3-Flash, DeepSeek-V4. Для MTP нужны совместимые обученные веса NextN; без них выводится ошибка. V4.1/Engram/DSpark остаётся отдельным экспериментом в исходниках. [Поддержка и ограничения](backends/API-AND-MTP.md).

## Запуск

1. Скачайте ZIP, проверьте `SHA256SUMS.txt`, распакуйте.
2. Откройте **INSTALL.cmd**: выберите native Qwen, CPU, CUDA, Vulkan/RX580 или Poly CUDA. Для других моделей укажите локальный GGUF.
3. Откройте **START.cmd**. API: `http://127.0.0.1:8093/v1`. Для отдельной установки выберите свободный `--port`; 8080 зарезервирован.

**STOP.cmd** завершает принятые запросы. **CHECK.cmd** проверяет файлы. **AUTOSTART.cmd** создаёт задачи запуска при загрузке Windows; Codex не требуется. Qwen скачивается с **докачкой и SHA-256**, исходный checkpoint не нужен. Веса в архив не входят.

## Измеренный прогресс Qwen

**16.45 → 48.77 токена/с** в движке; полный API: 11.65 → 44.65. Замер 2026-10-25, движок 0.1.49.3, `45B99DC2`. Исторический холодный ответ без MTP против прогретого MTP/xhigh: разные режимы, не одновременный A/B. Полные 128К и новые модели не измерены. [Методика и доказательства CPU/GPU](p40/BENCHMARKS.md).

Native-профиль: **128К · KV Q4 · MTP Q2/два черновых токена · xhigh · vision на CPU**. Сборка: **Ivy Bridge O3/AVX1**, CUDA **O3/sm_61**, MSVC host **O2/Ob3**. Остальные профили начинают с F16 KV и ограничений своей модели.

[Патчи](p40/PATCHES.md) · [Проверки](p40/INSTALLATION-VERIFICATION.md) · [Лицензии](THIRD_PARTY_NOTICES.md) · [Оригинальная Strata](https://github.com/Niko1221/Strata)
[Xolotl](https://github.com/Indras-Mirror/Xolotl) · [PolyStrata](https://github.com/VecSzn/PolyStrata) · [Maya](https://github.com/mw00/project-maya) · [Polaris](https://github.com/AvilaCarlosDev/polaris-local-ai)

Native-движок **0.1.50**, официальная база [41cf05a06a25](https://github.com/Niko1221/Strata/commit/41cf05a06a25dd29103b7b27a2279a3f60c21876). Ключей, личных настроек, логов, кэшей и SDK в ZIP нет. Проверка обученных GLM/DeepSeek и реальной RX580 пока не заявляется.
