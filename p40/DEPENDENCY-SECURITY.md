# Runtime dependency security

The Windows package includes **Pillow 13.0.0** for Python 3.13, fixing [GHSA-78g4-xqwv-q3g8](https://github.com/python-pillow/Pillow/security/advisories/GHSA-78g4-xqwv-q3g8). Official wheel SHA-256: `9dda0788a9932776a75d8bcc020076edc308ce2508b51f6739a45e3158b3fc42`. MIT-CMU and bundled codec notices are retained.

Native engine bytes and source qualification are unchanged. Seven codec roundtrips, seven normalization formats, EXIF rotation and twenty existing vision unit cases passed on the AVX1 host. Two test names from the newer PR were absent in this source; they are not counted as passed. No model or speed requests were made.

For a source installation, apply [pillow13-security.patch](patches/pillow13-security.patch) before installing requirements. It contains the reviewed upstream PR's Python-version markers and three packaging locks. Python 3.10 remains on affected Pillow 12.3.0; this package uses Python 3.13. The ready-made ZIP already includes the fix.

Пакет Windows содержит **Pillow 13.0.0** с исправлением обработки изображений. Нативный движок не пересобирался. При установке из исходников сначала примените указанный патч зависимостей; готовый ZIP уже исправлен. Замеров ускорения в этой ревизии нет.
