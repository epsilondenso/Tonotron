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

assigned_hwork_ids_from_rid = """
                            SELECT
                                housework_id
                            FROM
                                assignments
                            WHERE
                                roomie_id = %s
                            ORDER BY
                                housework_id
                            ;
                            """

roomies_from_tids = """
                    SELECT
                        roomie_name,
                        telegram_id
                    FROM
                        roomies
                    WHERE
                        telegram_id = ANY(%s)
                    ORDER BY
                        roomie_id
                    ;
                    """

due_date_from_hwork = """
                    SELECT
                        due_date
                    FROM
                        assignments
                    WHERE
                        housework_id = %s
                    ;
                    """

rotations_on_day = """
                    SELECT
                        COUNT(*)
                    FROM
                        rotation_log
                    WHERE
                        housework_id = %s
                    AND
                        rotated_at::date = %s
                    ;
                    """

insert_rotation_log = """
                    INSERT INTO
                        rotation_log (housework_id, rotated_at)
                    VALUES
                        (%s, %s)
                    ;
                    """

hwork_list = """
                    SELECT
                        housework_name AS tarea
                    FROM
                        housework
                    ORDER BY
                        housework_id
                    ;
                    """

roomies_by_turn = """
                    SELECT
                        turn AS turno,
                        roomie_name,
                        last_name
                    FROM
                        roomies
                    ORDER BY
                        turn
                    ;
                    """

# Siguiente roomie en orden de turno, volviendo al primero al llegar al
# último. No depende de cuántos roomies haya ni de que los turnos sean
# consecutivos. Con turno 0 devuelve al roomie del primer turno.
next_roomie_by_turn = """
                    SELECT
                        roomie_id
                    FROM
                        roomies
                    ORDER BY
                        turn <= %s,
                        turn
                    LIMIT 1
                    ;
                    """

current_turn_from_hwork = """
                    SELECT
                        turn
                    FROM
                        assignments
                    INNER JOIN
                        roomies
                    USING
                        (roomie_id)
                    WHERE
                        housework_id = %s
                    ;
                    """

# Las tablas no tienen secuencias, así que los IDs se calculan con MAX + 1.
insert_housework = """
                    INSERT INTO
                        housework (housework_id, housework_name)
                    SELECT
                        COALESCE(MAX(housework_id), 0) + 1,
                        %s
                    FROM
                        housework
                    RETURNING
                        housework_id
                    ;
                    """

insert_assignment = """
                    INSERT INTO
                        assignments (assignment_id, housework_id, roomie_id, due_date)
                    SELECT
                        COALESCE(MAX(assignment_id), 0) + 1,
                        %s,
                        %s,
                        %s
                    FROM
                        assignments
                    ;
                    """

delete_rotation_log_from_hwork = """
                    DELETE FROM
                        rotation_log
                    WHERE
                        housework_id = %s
                    ;
                    """

delete_assignment_from_hwork = """
                    DELETE FROM
                        assignments
                    WHERE
                        housework_id = %s
                    ;
                    """

delete_housework = """
                    DELETE FROM
                        housework
                    WHERE
                        housework_id = %s
                    ;
                    """

# El roomie nuevo toma el último turno.
insert_roomie = """
                    INSERT INTO
                        roomies (roomie_id, roomie_name, last_name, phone_number, telegram_id, turn)
                    SELECT
                        COALESCE(MAX(roomie_id), 0) + 1,
                        %s,
                        %s,
                        %s,
                        %s,
                        COALESCE(MAX(turn), 0) + 1
                    FROM
                        roomies
                    RETURNING
                        turn
                    ;
                    """

delete_roomie = """
                    DELETE FROM
                        roomies
                    WHERE
                        roomie_id = %s
                    RETURNING
                        turn
                    ;
                    """

# Recorre una posición los turnos posteriores al borrado. Se hace en dos
# pasos (negar y luego restaurar) porque turn es UNIQUE y un solo UPDATE
# puede chocar a media actualización.
negate_turns_after = """
                    UPDATE
                        roomies
                    SET
                        turn = -turn
                    WHERE
                        turn > %s
                    ;
                    """

restore_negated_turns = """
                    UPDATE
                        roomies
                    SET
                        turn = -turn - 1
                    WHERE
                        turn < 0
                    ;
                    """
