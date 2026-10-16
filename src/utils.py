import unicodedata
from datetime import datetime, timedelta


def next_sunday() -> datetime:
    """
    Calcula la fecha del próximo domingo.

    Si faltan 2 días o menos (viernes o sábado), devuelve el domingo
    de la semana siguiente.

    Returns
    -------
    datetime
        Fecha y hora del domingo objetivo (misma hora que ahora).
    """
    today = datetime.now()
    days_until_sunday = (6 - today.weekday())%7 or 7
    if days_until_sunday in [1, 2]:
        days_until_sunday += 7

    return today + timedelta(days=days_until_sunday)


def normalize_name(name):
    name = name.strip().lower()
    name = unicodedata.normalize("NFD", name)
    name = "".join(
        char for char in name
        if unicodedata.category(char) != "Mn"
    )
    return " ".join(name.split())