import pandas as pd

def query_assignment(connection, 
                     hwork_id:int):

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
