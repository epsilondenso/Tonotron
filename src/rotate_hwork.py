import pandas as pd
import datetime
from psycopg2.extensions import connection as PGConnection

from src.connect_db import get_connection
from src.queries import query_assignment
from src.utils import next_sunday



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

    update_query = """
        UPDATE 
            assignments 
        SET 
            roomie_id = %s,
            assigned_at = %s,
            due_date = %s
        WHERE 
            housework_id = %s
        ;
    """

    cursor = connection.cursor()

    cursor.execute(
        update_query,
        (
            int(new_id.iloc[0, 0]),
            datetime.datetime.now().date(),
            due_date,
            hwork_id
        )
    )

    connection.commit()
    cursor.close()

    return None 

if __name__ == "__main__":
    for i in range(1, 6, 1):
        conn = get_connection()
        rotate_hwork(
            i, 
            conn
        )