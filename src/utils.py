import unicodedata
from datetime import date, datetime, timedelta

DATE_FORMAT = "%d/%m/%Y"


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


def parse_date(text: str) -> date | None:
    """
    Convierte un texto ``dd/mm/aaaa`` en fecha.

    Parameters
    ----------
    text : str
        Fecha escrita por el usuario.

    Returns
    -------
    date or None
        Fecha leída, o ``None`` si el texto no tiene el formato correcto.
    """
    try:
        return datetime.strptime(text, DATE_FORMAT).date()
    except ValueError:
        return None
