import psycopg2
from psycopg2.extensions import connection as PGConnection
import streamlit as st

def get_connection(
    host: str = "localhost",
    port: int = 5432,
    dbname: str = "tonotron",
    user: str = "postgres",
    password: str = "aVs#1105"
) -> PGConnection:
    """
    Abre una conexión a la base de datos PostgreSQL.

    Parameters
    ----------
    host : str, optional
        Host del servidor.
    port : int, optional
        Puerto del servidor.
    dbname : str, optional
        Nombre de la base de datos.
    user : str, optional
        Usuario de la base de datos.
    password : str, optional
        Contraseña del usuario.

    Returns
    -------
    PGConnection
        Conexión abierta de psycopg2.
    """

    return psycopg2.connect(
        host=host,
        port=port,
        dbname=dbname,
        user=user,
        password=password
    )

