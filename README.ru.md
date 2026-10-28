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

**Интерфейс RU/EN · отдельные Ultra и Adaptive.** По умолчанию — Adaptive/Auto. Явные High/XHigh сохраняют стандартное поведение Qwen. Adaptive выбирает авторский режим под задачу; память и БД не включены. [Режимы и API](p40/REASONING-MODES.md) · [Источник Mnemosyne](https://github.com/TheHubUser4860938/Strata-Mnemosyne).

**16.45 → 55.15 токена/с** в движке; полный API: 11.65 → 48.92. Замер 2026-10-29, движок 0.1.53, `C0736323`. Исторический холодный ответ без MTP против прогретого MTP/Ultra: разные режимы, не одновременный A/B. Полные 128К и новые модели не измерены. [Методика и доказательства CPU/GPU](p40/BENCHMARKS.md).

Native-профиль: **128К · KV Q4 · MTP Q2/два черновых токена · xhigh · vision на CPU**. Сборка: **Ivy Bridge O3/AVX1**, CUDA **O3/sm_61**, MSVC host **O2/Ob3**. Остальные профили начинают с F16 KV и ограничений своей модели.

Настройка измеренного профиля P40: `STRATA_Q8_SM60=1`, `STRATA_MTP_Q8_SM60=0`; второй флаг не отключает MTP Q2. Для других GPU этот выбор не измерен.

[Патчи](p40/PATCHES.md) · [Проверки](p40/INSTALLATION-VERIFICATION.md) · [Лицензии](THIRD_PARTY_NOTICES.md) · [Оригинальная Strata](https://github.com/Niko1221/Strata)
[Xolotl](https://github.com/Indras-Mirror/Xolotl) · [PolyStrata](https://github.com/VecSzn/PolyStrata) · [Maya](https://github.com/mw00/project-maya) · [Polaris](https://github.com/AvilaCarlosDev/polaris-local-ai)

Native-движок **0.1.53**, официальная база [46c152a1310f](https://github.com/Niko1221/Strata/commit/46c152a1310f77cd2f0ce2c7cd213962df14fe83). Ключей, личных настроек, логов, кэшей и SDK в ZIP нет. Проверка обученных GLM/DeepSeek и реальной RX580 пока не заявляется.
