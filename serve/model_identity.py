"""OpenAI-compatible machine IDs are distinct from human display names."""
import hashlib
import re

_ALLOWED = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/-]*\Z")


def public_model_id(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Model ID must be a nonempty string")
    if _ALLOWED.fullmatch(value):
        return value
    result = re.sub(r"[^A-Za-z0-9._:/-]+", "-", value.strip()).strip("-./:")
    if not result:
        result = "model-" + hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]
    if not result[0].isascii() or not result[0].isalnum():
        result = "model-" + result
    return result


def configured_model_id(cfg, fallback):
    explicit = cfg.get("api_model_id")
    if explicit is not None:
        if not isinstance(explicit, str) or public_model_id(explicit) != explicit:
            raise ValueError("api_model_id must contain only portable ID characters, without spaces")
        return explicit
    return public_model_id(cfg.get("model_name") or fallback)
