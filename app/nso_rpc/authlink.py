"""Detecta el link de "Elegir esta cuenta" que Nintendo da al iniciar sesión."""

import re
from urllib.parse import parse_qs

_LINK = re.compile(r"npf71b963c1b7b6d119://auth[^\s\"'<>]*")


def extract_auth_link(text: str) -> str | None:
    """Devuelve el link npf71b963c1b7b6d119://auth#... si trae session_token_code; si no, None."""
    match = _LINK.search(text or "")
    if not match:
        return None
    link = match.group(0)
    _, _, fragment = link.partition("#")
    if not parse_qs(fragment).get("session_token_code"):
        return None
    return link
