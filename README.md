# Toñotrón

Bot de Telegram que lleva el rol de tareas domésticas de la casa. Cada tarea está asignada a un roomie; cuando la termina, el bot la rota al siguiente turno, le pone nueva fecha límite y menciona en el chat a quien le toca ahora.

Stack: Python 3.13 · [python-telegram-bot](https://docs.python-telegram-bot.org/) 22 (polling) · PostgreSQL 18 · pandas para leer consultas · Docker Compose para desplegar.

---

## Comandos

| Comando | Quién | Dónde | Qué hace |
|---|---|---|---|   
| `/terminada <tarea>` | El responsable de la tarea o un admin | Solo chats permitidos | Rota la tarea al siguiente turno y avisa a los admins. |
| `/termine_mis_tareas` | Cualquier roomie registrado | Solo chats permitidos | Intenta rotar todas las tareas del usuario; reporta cuáles se rotaron y cuáles quedaron bloqueadas. |
| `/asignar <roomie> <tarea> [dd/mm/aaaa]` | Solo admins | Solo chats permitidos | Asigna una tarea a alguien a mano. Sin fecha → próximo domingo. No cuenta como rotación. |
| `/mis_tareas` | Cualquier roomie registrado | Cualquier chat | Lista las tareas del usuario con fecha límite y fecha de asignación. |
| `/rol` | Cualquier roomie registrado | Cualquier chat | Muestra todas las tareas con su responsable y fecha límite. |
| `/responsable <tarea>` | Cualquiera | Cualquier chat | Muestra quién tiene una tarea y su fecha límite (con mención). |
| `/ayuda` | Cualquiera | Cualquier chat | Muestra cómo se usa cada comando. |

Los nombres de tareas y roomies se comparan **normalizados** (minúsculas, sin acentos, espacios colapsados), así que `/terminada LIMPIAR  cocína` encuentra "Limpiar cocina".

---

## Reglas de negocio

**Rotación** (`rotate_hwork`)
- Los roomies tienen un `turn` del 1 al 6 (único). Rotar pasa la tarea al `turn + 1`, y del 6 vuelve al 1. **El 6 está fijo en el código.**
- Al rotar: `assigned_at` = hoy, `due_date` = `next_sunday()`, y se escribe una fila en `rotation_log`.

**Fecha límite** (`next_sunday`)
- Es el domingo siguiente, pero si hoy es viernes o sábado salta al domingo de la semana siguiente (casi todas las tareas se hacen el fin de semana y las realizaciones de una misma tarea deben estar espaciadas no menos de 5 días). Si hoy es domingo, también es el siguiente domingo.

**Bloqueos** (`rotation_block_reason`) — aplican a `/terminada` y `/termine_mis_tareas`, no a `/asignar`:
1. **Día de la semana**: solo se puede rotar en los días de `ROTATION_WEEKDAYS` (pensado para viernes–domingo), salvo que la tarea ya esté vencida.
2. **Límite diario**: cada tarea se puede rotar como máximo `ROTATIONS_PER_DAY` veces por día (se cuenta en `rotation_log`).

**"Comprar agua"** (`WATER_HWORK_ID = 4`): no lleva fecha límite y puede rotarse cualquier día (sí respeta el límite diario). En `/asignar` solo se le pone fecha si se da explícitamente.

**Permisos**
- Admins: los Telegram IDs en `ADMIN_USER_1` y `ADMIN_USER_2`. Se les menciona cada vez que hay rotación.
- Chats permitidos: `ID_CHAT_PRUEBAS` e `ID_CHAT_PROD`. Los comandos que modifican datos solo funcionan ahí.

---

## Estructura

```
src/
  bot.py          Punto de entrada: registra los CommandHandler y hace polling.
  handlers.py     Un handler async por comando + helpers de formato (menciones HTML, aviso a admins).
  rotate_hwork.py Lógica de rotación, asignación y bloqueos. Constantes de negocio aquí.
  queries.py      Búsqueda de IDs por nombre normalizado; query_assignment().
  sql.py          Todas las consultas SQL como strings (parámetros con %s).
  connect_db.py   get_connection() con las variables DB_*.
  utils.py        next_sunday(), normalize_name(), parse_date(); DATE_FORMAT = dd/mm/aaaa.
db/
  tonotron_schema.sql            Dump del esquema (sin datos).
  migrations/001_rotation_log.sql Tabla rotation_log (no está en el dump).
  consultas.sql                  Consulta suelta para revisar asignaciones.
  init/                          (ignorada por git) scripts que Postgres corre al crear el volumen.
```

Patrón de cada handler: validar chat/permisos/argumentos → abrir conexión → consultar con `pd.read_sql` → modificar con cursor + `commit` (dentro de `assign_hwork`) → responder en HTML. En error hace `rollback`, responde un mensaje genérico y relanza la excepción; siempre cierra la conexión.

---

## Base de datos

- **`roomies`**: `roomie_id`, `roomie_name`, `last_name`, `phone_number`, `telegram_id` (varchar), `turn` (único), `is_admin`.
- **`housework`**: `housework_id`, `housework_name` (único).
- **`assignments`**: una fila por tarea con su responsable actual: `housework_id`, `roomie_id`, `due_date`, `assigned_at`, `completed_at`. Las rotaciones **actualizan** la fila (no insertan), así que no hay historial aquí.
- **`rotation_log`**: `housework_id`, `rotated_at` (timestamp sin zona, hora local). Solo para el límite diario.

> `is_admin` y `completed_at` existen pero el código no los usa: los admins vienen del `.env`.

---

## Configuración

Copiar `.env.example` a `.env` y llenar:

| Variable | Uso |
|---|---|
| `PRUEBAS_TOKEN` | Token que usa **actualmente** `bot.py`. |
| `TELEGRAM_BOT_TOKEN` | Token de producción (aún no se lee en el código). |
| `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` | Conexión a Postgres. En Docker, `DB_HOST`/`DB_PORT` los sobreescribe el compose. |
| `ROTATIONS_PER_DAY` | `1` en producción; algo grande (p. ej. `1000`) para pruebas. |
| `ADMIN_USER_1`, `ADMIN_USER_2` | Telegram IDs de los admins. **Obligatorias** (no están en `.env.example`). |
| `ID_CHAT_PRUEBAS`, `ID_CHAT_PROD` | IDs de los chats permitidos. **Obligatorias** (no están en `.env.example`). |

Si falta alguna de las obligatorias, `handlers.py` truena al importarse (`int(None)`).

---

## Correr

**Local** (con un Postgres ya levantado), desde la raíz del repo:

```bash
pip install -r requirements.txt
python -m src.bot
```

Hay que correrlo como módulo (`-m`) porque los imports son `from src...`.

**Docker Compose**:

```bash
docker compose up -d --build
docker compose logs -f bot
```

- `db` usa el volumen `pgdata`. **Solo la primera vez** (volumen vacío) ejecuta lo que haya en `db/init/`. Para una base nueva, poner ahí, en orden: el esquema, las migraciones y un script con los datos (roomies, tareas y una asignación inicial por tarea). Esa carpeta no se sube a git porque contiene datos personales.
- Para una base que ya existe, aplicar migraciones a mano:
  ```bash
  docker compose exec -T db psql -U $DB_USER -d $DB_NAME < db/migrations/001_rotation_log.sql
  ```
- El bot corre con `TZ=America/Mexico_City`: los límites por día y los días de rotación dependen de la hora local.

`python -m src.rotate_hwork` rota las tareas 1–5 de golpe; es un script de prueba, no usarlo contra producción.

---

## Pendientes y detalles a recordar

- `ROTATION_WEEKDAYS = {1, 4, 5, 6}` incluye el **martes** (1), aunque el comentario y el mensaje de bloqueo dicen "viernes a domingo". Probablemente quedó de una prueba.
- `bot.py` usa `PRUEBAS_TOKEN`; para producción hay que cambiarlo a `TELEGRAM_BOT_TOKEN` (o hacerlo configurable).
- `ASIGNADA_USAGE` dice `/asignada`, pero el comando registrado es `/asignar`.
- `/mis_tareas` y `/rol_semanal` fallan con el mensaje genérico si quien escribe no está en `roomies` (no hay validación como en `/termine_mis_tareas`).
- El número de turnos (6) está fijo en `rotate_hwork`; si cambia el número de roomies hay que tocarlo.
- `query_assignment` arma su SQL con f-string en lugar de parámetros.
- No hay tests.
