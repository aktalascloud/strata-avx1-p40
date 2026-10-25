# Strata Legacy GPU

[English](README.md) · [Русский](README.ru.md) · [Скачать](https://github.com/aktalascloud/strata-legacy-gpu/releases/latest)

**Пакет LLM для Windows: процессоры AVX1, NVIDIA Pascal/P40 и AMD Polaris/RX580.** OpenAI-совместимый API; бэкенды CPU, CUDA и Vulkan.

| Железо | Бэкенд | Проверка |
| --- | --- | --- |
| Ivy Bridge / AVX1, без AVX2 | CPU | CPU- и API-тесты |
| NVIDIA Pascal / Tesla P40 | CUDA12.9, sm61 | Рабочая конфигурация Qwen |
| AMD Polaris / RX5808ГБ | Vulkan + вычисления на CPU | Бэкенд собран; проверка на RX580 ещё нужна |

**Модели:** Qwen3.8 Flash Next, GLM5.3 Flash, DeepSeekV4; для V4.1/Engram есть отдельный путь DSV41. Для MTP нужна совместимая обученная голова; V4.1 использует DSpark. Ограничения моделей и устройств: [руководство](backends/API-AND-MTP.md).

## Запуск

1. Скачайте Windows ZIP и проверьте `SHA256SUMS.txt`.
2. Распакуйте; запустите **INSTALL.cmd**, затем **START.cmd**.
3. Панель: `http://127.0.0.1:8093/`; OpenAI API: `http://127.0.0.1:8093/v1`.

**STOP.cmd** завершает принятые запросы. **CHECK.cmd** проверяет установку. **AUTOSTART.cmd** регистрирует независимый запуск Windows; Codex не требуется. Веса отдельно; загрузка — с **докачкой и SHA-256**, без исходного checkpoint.

Текущий опубликованный ZIP содержит Qwen/P40; единый ZIP CPU/CUDA/Vulkan готовится. Имеющиеся веса и настройки сохраняются. Выбирайте свободный порт; OpenWebUI8080 не изменяется.

## Измеренный результат Qwen

**16.45 → 48.77 токена/с** в движке; полный API: 11.65 → 44.65. Замер 2026-10-25, движок 0.1.49.3, `45B99DC2`. Исторический холодный ответ без MTP против прогретого MTP/xhigh: разные режимы, не одновременный A/B. Полные 128К и новые модели не измерены. [Методика и доказательства CPU/GPU](p40/BENCHMARKS.md).

Сборка: **Ivy Bridge O3 / AVX1**, CUDA **O3 / sm61**, host MSVC **O2/Ob3**. Профиль Qwen: **128К, KV Q4, MTP Q2/два draft-токена, xhigh, CPU vision**. [Патчи](p40/PATCHES.md) · [Проверки](p40/INSTALLATION-VERIFICATION.md) · [Лицензии](THIRD_PARTY_NOTICES.md).

[Оригинальная Strata](https://github.com/Niko1221/Strata) · [Xolotl](https://github.com/Indras-Mirror/Xolotl) · [PolyStrata](https://github.com/VecSzn/PolyStrata) · [Maya](https://github.com/mw00/project-maya) · [Источник Polaris](https://github.com/AvilaCarlosDev/polaris-local-ai).
Движок **0.1.49.3**, официальная основа [7dd5cf18e68c](https://github.com/Niko1221/Strata/commit/7dd5cf18e68c639a8773e096c5c79f971ea2a9f5). В архиве нет весов, ключей, приватных настроек, логов, кэшей и SDK.
