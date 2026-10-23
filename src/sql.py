hwork_name_query = """ 
                    SELECT 
                        housework_name 
                    FROM 
                        housework 
                    WHERE
                        housework_id = %s
                    """
roomie_telegram_id_from_hwork =   """
                            SELECT 
                            	roomies.telegram_id
                            FROM 
                            	roomies
                            INNER JOIN
                            	assignments
                            USING(roomie_id)
                            WHERE 
                                housework_id = %s;
                            """

next_roomie_from_hwork = """
                            SELECT
                                roomies.roomie_name,
                                roomies.telegram_id
                            FROM
                                roomies
                            INNER JOIN
                                assignments
                            USING(roomie_id)
                            WHERE
                                housework_id = %s;
                            """
