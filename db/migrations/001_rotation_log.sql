-- Registro de rotaciones hechas con /terminada y /termine_mis_tareas.
-- Sirve para limitar cuántas veces al día se puede rotar cada tarea.
-- /asignar no escribe aquí, así que las reasignaciones de admins no cuentan.

CREATE TABLE IF NOT EXISTS public.rotation_log (
    rotation_id serial PRIMARY KEY,
    housework_id integer NOT NULL REFERENCES public.housework (housework_id),
    rotated_at timestamp without time zone NOT NULL
);

CREATE INDEX IF NOT EXISTS rotation_log_housework_rotated_idx
    ON public.rotation_log (housework_id, rotated_at);
