roomie_id_from_tid =    """
                        SELECT
                            roomie_id
                        FROM
                            roomies
                        WHERE
                            telegram_id = %s
                        ;

                        """
roomie_name_from_rid = """
                        SELECT
                            roomie_name
                        FROM
                            roomies
                        WHERE
                            roomie_id = %s
                        ;
                        """

hwork_name_query = """ 
                    SELECT 
                        housework_name 
                    FROM 
                        housework 
                    WHERE
                        housework_id = %s
                    ;
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
assigned_hwork_from_rid =   """
                            SELECT  
                            	housework_name AS tarea, 
                            	due_date AS fecha_limite,
                            	assigned_at AS fecha_asignación
                            FROM
                            	assignments
                            INNER JOIN
                            	housework
                            USING
                            	(housework_id)

                            WHERE 
                            	roomie_id = %s
                            ;
                            """

weekly_rol =    """
                SELECT
                	housework_name AS tarea, 
                	roomie_name AS le_toca_a, 
                	due_date AS fecha_limite
                FROM
                    assignments
                INNER JOIN
                    housework
                USING 
                    (housework_id)
                INNER JOIN
                    roomies
                USING
                    (roomie_id)
                ;
                """
responsible_from_hwork =    """
                            SELECT
                                housework_name AS tarea,
                                roomie_name AS le_toca_a,
                                telegram_id,
                                due_date AS fecha_limite
                            FROM
                                assignments
                            INNER JOIN
                                housework
                            USING
                                (housework_id)
                            INNER JOIN
                                roomies
                            USING
                                (roomie_id)
                            WHERE
                                housework_id = %s
                            ;
                            """

hwork_names_query = """
                    SELECT
                        housework_id,
                        housework_name
                    FROM
                        housework
                    ;
                    """

roomie_names_query = """
                    SELECT
                        roomie_id,
                        roomie_name
                    FROM
                        roomies
                    ;
                    """

update_assignment = """
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
