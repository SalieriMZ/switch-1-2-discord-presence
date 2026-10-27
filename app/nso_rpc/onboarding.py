"""Decide al arrancar si hace falta el tutorial y desde qué paso."""

from .config import Config

STEP_CHOOSE = 4  # "Elegir cuenta"


def wizard_start(config: Config, bot: dict | None) -> int | None:
    """None = no mostrar el tutorial; si no, el paso donde abrirlo.

    Quien ya usó nxapi (esta app o la versión de consola) tiene la cuenta-bot conectada:
    no repite la explicación ni el login, solo elige la cuenta si aún no lo hizo.
    """
    if config.tutorial_done:
        return None
    if bot is None:
        return 0
    if config.friend_nsaid:
        return None
    return STEP_CHOOSE
