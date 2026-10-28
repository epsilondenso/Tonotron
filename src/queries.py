from psycopg2.extensions import connection as PGConnection
from src.utils import normalize_name
from src.sql import hwork_names_query, roomie_names_query

def get_id_by_name(name: str,
                   names_query: str,
                   connection: PGConnection) -> int | None:
    """
    Busca un ID comparando nombres normalizados.

    Parameters
    ----------
    name : str
        Nombre a buscar, tal como lo escribió el usuario.
    names_query : str
        Consulta que devuelve pares ``(id, nombre)``.
    connection : PGConnection
        Conexión abierta a la base de datos.

    Returns
    -------
    int or None
        ID del primer registro cuyo nombre coincide, o ``None``.
    """

    normalized_name = normalize_name(name)

    with connection.cursor() as cursor:
        cursor.execute(names_query)

        for row_id, row_name in cursor.fetchall():
            if normalize_name(row_name) == normalized_name:
                return row_id

    return None


def get_housework_id(name: str, connection: PGConnection) -> int | None:
    """
    Obtiene el ID de una tarea doméstica a partir de su nombre.

    Parameters
    ----------
    name : str
        Nombre de la tarea (se normaliza antes de comparar).
    connection : PGConnection
        Conexión abierta a la base de datos.

    Returns
    -------
    int or None
        ID de la tarea, o ``None`` si no existe.
    """

    return get_id_by_name(name, hwork_names_query, connection)


def get_roomie_id(name: str, connection: PGConnection) -> int | None:
    """
    Obtiene el ID de un roomie a partir de su nombre.

    Parameters
    ----------
    name : str
        Nombre del roomie (se normaliza antes de comparar).
    connection : PGConnection
        Conexión abierta a la base de datos.

    Returns
    -------
    int or None
        ID del roomie, o ``None`` si no existe.
    """

    return get_id_by_name(name, roomie_names_query, connection)