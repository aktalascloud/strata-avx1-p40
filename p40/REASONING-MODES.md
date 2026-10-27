# Отдельные режимы рассуждений / Explicit reasoning modes

High и XHigh используют исходный шаблон Qwen. В текущем upstream High является совместимым именем XHigh; авторский Ultra больше их не подменяет.

По умолчанию выбран **Adaptive / Auto**. Явный выбор High/XHigh или Ultra имеет приоритет. / **Adaptive / Auto** is the default; an explicit High/XHigh or Ultra choice takes precedence.

| Выбор / Choice | OpenAI Chat API |
|---|---|
| High | `reasoning_effort: "high"` |
| XHigh | `reasoning_effort: "xhigh"` |
| Ultra | `reasoning_effort: "xhigh", reason_mode: "ultra"` |
| Adaptive | `reasoning_effort: "xhigh", reason_mode: "auto"` |

Ultra and Adaptive are separate author modes. Explicit standard efforts retain stock Qwen semantics. Adaptive picks a compatible persona from the latest task; an uncertain match falls back to the standard level. It does not guarantee greater intelligence or accuracy. Cline supports the separate modes when the model advertises `supportsAuthorModes`; its Ultra control tag is also supported.

Адаптивный выбор выполняется отдельно для каждого запроса. Память, БД, embedder и закрепление режима между диалогами не перенесены. Сохраняются схемы инструментов и вложения. Неизвестные API-режимы отклоняются с HTTP400.

Источник / Attribution: [Strata-Mnemosyne](https://github.com/TheHubUser4860938/Strata-Mnemosyne), pinned `2ac28be317c8ecbabc935f6153333506fb80f3e2`, MIT. Сохранены исправления приоритета тегов, словаря задач и оформления составных режимов. Дополнительно учтены русские ключевые слова и границы Cline task/environment.

UI: русский по умолчанию; English переключается в верхней панели. Переводится интерфейс, текст пользователя, ответы, код и имена файлов не изменяются. / Russian by default, with an English switch; user content and code remain unchanged.
