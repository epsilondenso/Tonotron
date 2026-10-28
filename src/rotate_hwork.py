import os

import pandas as pd
import datetime
from psycopg2.extensions import connection as PGConnection

from src.connect_db import get_connection
from src.queries import query_assignment
from src.utils import next_sunday
from src.sql import (
    update_assignment,
    due_date_from_hwork,
    rotations_on_day,
    insert_rotation_log
)

# Máximo de rotaciones por tarea al día (/terminada y /termine_mis_tareas).
ROTATIONS_PER_DAY = int(os.getenv("ROTATIONS_PER_DAY", "1"))
# Días en que se puede rotar una tarea no vencida: viernes, sábado y domingo.
ROTATION_WEEKDAYS = {1, 4, 5, 6}
# "Comprar agua": no lleva fecha límite y puede rotarse cualquier día.
WATER_HWORK_ID = 4



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

    due_date = None if h_id == WATER_HWORK_ID else next_sunday().date()

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

    # Se registra en la misma transacción; assign_hwork hace el commit.
    with connection.cursor() as cursor:
        cursor.execute(
            insert_rotation_log,
            (hwork_id, datetime.datetime.now())
        )

    assign_hwork(
        hwork_id,
        int(new_id.iloc[0, 0]),
        due_date,
        connection
    )

    return None


def rotation_block_reason(hwork_id: int,
                          connection: PGConnection) -> str | None:
    """
    Indica si una tarea no puede rotarse hoy y por qué.

    Una tarea puede rotarse de viernes a domingo, o cualquier día si ya
    está vencida o es ``WATER_HWORK_ID``, y como máximo
    ``ROTATIONS_PER_DAY`` veces al día.

    Parameters
    ----------
    hwork_id : int
        ID de la tarea doméstica.
    connection : PGConnection
        Conexión abierta a la base de datos.

    Returns
    -------
    str or None
        Motivo del bloqueo, o ``None`` si la tarea puede rotarse.
    """

    today = datetime.date.today()

    due_date = pd.read_sql(due_date_from_hwork, connection, params = (hwork_id,)).iloc[0,0]
    is_overdue = not pd.isna(due_date) and pd.to_datetime(due_date).date() < today

    any_day = hwork_id == WATER_HWORK_ID

    if today.weekday() not in ROTATION_WEEKDAYS and not is_overdue and not any_day:
        return "solo se puede terminar de viernes a domingo, salvo que ya esté vencida."

    rotations_today = pd.read_sql(rotations_on_day, connection, params = (hwork_id, today)).iloc[0,0]

    if rotations_today >= ROTATIONS_PER_DAY:
        return f"ya alcanzó el límite de {ROTATIONS_PER_DAY} rotación(es) por día."

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