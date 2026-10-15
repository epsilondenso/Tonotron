import pandas as pd
from psycopg2.extensions import connection as PGConnection

def query_assignment(connection: PGConnection, 
                     hwork_id:int) -> tuple[int, int, int]:
    """
    Obtiene la asignación actual de una tarea doméstica.

    Parameters
    ----------
    connection : PGConnection
        Conexión abierta a la base de datos.
    hwork_id : int
        ID de la tarea doméstica.

    Returns
    -------
    tuple[int, int, int]
        ``(housework_id, roomie_id, turn)`` de la primera asignación encontrada.
    """

    query = f"""
     SELECT 
	    housework_id,
	    roomie_id,
	    turn
     FROM 
     	assignments 
     INNER JOIN 
     	roomies 
     	USING(roomie_id) 
     INNER JOIN  
     	housework 
     	USING(housework_id) 
     WHERE
        housework_id = {hwork_id}
     ORDER BY 
     	assignment_id 
     ASC
     ;
     """    
    hwork_df = pd.read_sql(sql = query, con = connection)
    h_id, r_id, turn = hwork_df.iloc[0]

    return h_id, r_id, turn
