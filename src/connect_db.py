import os

from dotenv import load_dotenv
import psycopg2
from psycopg2.extensions import connection as PGConnection

load_dotenv()

def get_connection(
    host: str | None = None,
    port: int | None = None,
    dbname: str | None = None,
    user: str | None = None,
    password: str | None = None
) -> PGConnection:
    """
    Abre una conexión a la base de datos PostgreSQL.

    Parameters
    ----------
    host : str, optional
        Host del servidor. Por defecto ``DB_HOST`` o ``"localhost"``.
    port : int, optional
        Puerto del servidor. Por defecto ``DB_PORT`` o ``5432``.
    dbname : str, optional
        Nombre de la base de datos. Por defecto ``DB_NAME`` o ``"tonotron"``.
    user : str, optional
        Usuario de la base de datos. Por defecto ``DB_USER`` o ``"postgres"``.
    password : str, optional
        Contraseña del usuario. Por defecto ``DB_PASSWORD``.

    Returns
    -------
    PGConnection
        Conexión abierta de psycopg2.
    """

    return psycopg2.connect(
        host=host or os.getenv("DB_HOST", "localhost"),
        port=port or int(os.getenv("DB_PORT", "5432")),
        dbname=dbname or os.getenv("DB_NAME", "tonotron"),
        user=user or os.getenv("DB_USER", "postgres"),
        password=password or os.getenv("DB_PASSWORD")
    )

