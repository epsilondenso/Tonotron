hwork_name_query = """ 
                    SELECT 
                        housework_name 
                    FROM 
                        housework 
                    WHERE
                        housework_id = %s
                    """