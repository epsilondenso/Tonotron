import pandas as pd
import datetime
from psycopg2.extensions import connection as PGConnection

from src.connect_db import get_connection
from src.queries import query_assignment
from src.utils import next_sunday
from src.sql import update_assignment



def rotate_hwork(hwork_id: int, 
                 connection: PGConnection ) -> None:
    """
    Rota una tarea doméstica al roomie del siguiente turno.

    Avanza el turno (cíclico de 1 a 6), actualiza ``roomie_id``,
    ``assigned_at`` y ``due_date`` en ``assignments`` y hace commit.

    Parameters
    ----------
    hwork_id : int
        ID de la tarea doméstica a rotar.
    connection : PGConnection
        Conexión abierta a la base de datos.

    Returns
    -------
    None
    """

    h_id, r_id, turn = query_assignment(
        connection, 
        hwork_id
    ) 

    new_turn = turn + 1 if turn < 6 else 1 

    due_date = None if h_id == 4 else next_sunday().date()

    r_id_query = """
        SELECT 
            roomie_id 
        FROM 
            roomies 
        WHERE 
            turn = %s
        ;
    """

    new_id = pd.read_sql(
        con=connection, 
        sql=r_id_query,
        params=(new_turn,)
    )

    assign_hwork(
        hwork_id,
        int(new_id.iloc[0, 0]),
        due_date,
        connection
    )

    return None 


def assign_hwork(hwork_id: int,
                 roomie_id: int,
                 due_date: datetime.date | None,
                 connection: PGConnection) -> None:
    """
    Asigna una tarea doméstica a un roomie y hace commit.

    Actualiza ``roomie_id``, ``assigned_at`` (hoy) y ``due_date``
    en ``assignments``.

    Parameters
    ----------
    hwork_id : int
        ID de la tarea doméstica.
    roomie_id : int
        ID del roomie al que se asigna.
    due_date : datetime.date or None
        Fecha límite de la tarea.
    connection : PGConnection
        Conexión abierta a la base de datos.

    Returns
    -------
    None
    """

    with connection.cursor() as cursor:
        cursor.execute(
            update_assignment,
            (
                roomie_id,
                datetime.datetime.now().date(),
                due_date,
                hwork_id
            )
        )

    connection.commit()

    return None

if __name__ == "__main__":
    for i in range(1, 6, 1):
        conn = get_connection()
        rotate_hwork(
            i, 
            conn
        )