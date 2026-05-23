import json
from pathlib import Path
from typing import Dict, List

_LOCALES: Dict[str, Dict[str, str]] = {}
_CURRENT = "en"


def _load_locale(code: str) -> Dict[str, str]:
    repo = Path(__file__).resolve().parent
    path = repo / "i18n" / f"{code}.json"
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def set_locale(code: str):
    global _CURRENT
    if code not in _LOCALES:
        _LOCALES[code] = _load_locale(code)
    _CURRENT = code


def translate(text: str) -> str:
    if not text:
        return text
    # load default locale if not loaded
    if _CURRENT not in _LOCALES:
        _LOCALES[_CURRENT] = _load_locale(_CURRENT)
    tmap = _LOCALES.get(_CURRENT, {})
    # direct match
    if text in tmap:
        return tmap[text]
    # case-insensitive
    lower = text.lower()
    for k, v in tmap.items():
        if k.lower() == lower:
            return v
    # fallback: try replace known phrases
    out = text
    # sort by length to avoid partial replaces
    for k in sorted(tmap.keys(), key=lambda x: -len(x)):
        out = out.replace(k, tmap[k])
    return out


def translate_list(items: List[str]) -> List[str]:
    return [translate(i) for i in items]


def current_locale() -> str:
    return _CURRENT
