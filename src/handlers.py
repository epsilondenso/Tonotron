import os
import html
from datetime import date
from dotenv import load_dotenv

import pandas as pd

from telegram import Update
from telegram.ext import ContextTypes

from src.connect_db import get_connection
from src.rotate_hwork import (
    rotate_hwork,
    assign_hwork,
    rotation_block_reason,
    WATER_HWORK_ID
)
from src.queries import get_housework_id, get_roomie_id
from src.utils import next_sunday, parse_date, DATE_FORMAT
from src.sql import (
    hwork_name_query,
    next_roomie_from_hwork,
    roomie_telegram_id_from_hwork,
    assigned_hwork_from_rid,
    assigned_hwork_ids_from_rid,
    roomie_id_from_tid,
    roomie_name_from_rid,
    weekly_rol,
    responsible_from_hwork,
    roomies_from_tids,
    hwork_list,
    roomies_by_turn,
    next_roomie_by_turn,
    insert_housework,
    insert_assignment,
    delete_rotation_log_from_hwork,
    delete_assignment_from_hwork,
    delete_housework,
    insert_roomie,
    delete_roomie,
    negate_turns_after,
    restore_negated_turns
)

load_dotenv()

ADMIN_USERS = {int(os.getenv("ADMIN_USER_1")), int(os.getenv("ADMIN_USER_2"))}
PERMITED_CHATS = {int(os.getenv("ID_CHAT_PRUEBAS")), 
                  int(os.getenv("ID_CHAT_PROD"))}
                  #int(os.getenv("ID_PRIV")),
                  #int(os.getenv("ID_PRIV_PRUEBAS"))}
ASIGNADA_USAGE = (
    "USO:\n"
    "/asignar nombre_roomie nombre de la tarea [dd/mm/aaaa]\n"
    "Ejemplo:\n" 
    "/asignar Joshua limpiar cocina 01/11/2026\n"
    "Notas:\n"
    "-  Si no indicas fecha, se asigna para el próximo domingo.\n"
    "-  A la tarea 'Comprar agua' no se le asigna fecha límite por defecto."
)
NUEVA_TAREA_USAGE = (
    "USO:\n"
    "/nueva_tarea agregar nombre de la tarea\n"
    "/nueva_tarea borrar nombre de la tarea\n"
    "Ejemplos:\n"
    "/nueva_tarea agregar lavar baño\n"
    "/nueva_tarea borrar lavar baño\n"
    "Notas:\n"
    "-  La tarea nueva se asigna al roomie del primer turno, para el próximo domingo.\n"
    "-  'Comprar agua' no se puede borrar."
)
NUEVO_ROOMIE_USAGE = (
    "USO:\n"
    "/nuevo_roomie agregar nombre apellido teléfono [telegram_id]\n"
    "/nuevo_roomie borrar nombre\n"
    "Ejemplos:\n"
    "/nuevo_roomie agregar Ana López 5512345678 123456789\n"
    "/nuevo_roomie borrar Ana\n"
    "Notas:\n"
    "-  Si no das el telegram_id, usa el comando respondiendo a un mensaje de la persona.\n"
    "-  El roomie nuevo toma el último turno.\n"
    "-  No se puede borrar a alguien con tareas asignadas; reasígnalas antes con /asignar."
)
ROOMIE_FIELD_MAX_LEN = 15
HWORK_NAME_MAX_LEN = 50

def is_permited_chat(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> bool:
    chat = update.effective_chat
    return int(chat.id) in PERMITED_CHATS



def mention_html(name: str, telegram_id: int) -> str:
    """
    Arma una mención de Telegram en HTML.

    Parameters
    ----------
    name : str
        Texto visible de la mención.
    telegram_id : int
        ID de Telegram de la persona mencionada.

    Returns
    -------
    str
        Enlace ``tg://user`` con el nombre escapado.
    """

    return f'<a href="tg://user?id={int(telegram_id)}">{html.escape(str(name))}</a>'


def admin_notice(connection) -> str:
    """
    Arma el aviso HTML que menciona a los admins tras una rotación.

    Parameters
    ----------
    connection : PGConnection
        Conexión abierta a la base de datos.

    Returns
    -------
    str
        Aviso listo para enviar con ``parse_mode="HTML"``.
    """

    admins = pd.read_sql(roomies_from_tids, connection, params = (list(ADMIN_USERS),))
    mentions = ", ".join(
        mention_html(admin["roomie_name"], admin["telegram_id"])
        for _, admin in admins.iterrows()
    )

    return f"🔔 {mentions}: Toñotrón rotó tareas."


def format_responsable(tarea: pd.Series) -> str:
    """
    Arma el mensaje HTML con la tarea, su responsable y su fecha límite.

    Parameters
    ----------
    tarea : pd.Series
        Fila de ``responsible_from_hwork``.

    Returns
    -------
    str
        Mensaje listo para enviar con ``parse_mode="HTML"``.
    """

    if pd.isna(tarea["fecha_limite"]):
        fecha_limite = "No aplica"
    else:
        fecha_limite = pd.to_datetime(tarea["fecha_limite"]).strftime(DATE_FORMAT)

    mention = mention_html(tarea["le_toca_a"], tarea["telegram_id"])

    return (
        f"<b>{html.escape(str(tarea['tarea']))}</b>\n"
        f"👤 Le toca a: {mention}\n"
        f"📅 Fecha límite: {fecha_limite}"
    )


def rotate_and_report(hwork_id: int, connection) -> str:
    """
    Rota una tarea y arma el mensaje HTML con el nuevo responsable.

    Parameters
    ----------
    hwork_id : int
        ID de la tarea doméstica a rotar.
    connection : PGConnection
        Conexión abierta a la base de datos.

    Returns
    -------
    str
        Mensaje listo para enviar con ``parse_mode="HTML"``.
    """

    true_name = pd.read_sql(hwork_name_query, connection, params = (hwork_id,)).iloc[0,0]

    rotate_hwork(hwork_id, connection)
    next_name, next_tid = pd.read_sql(
        next_roomie_from_hwork, connection, params=(hwork_id,)
    ).iloc[0]
    mention = mention_html(next_name, next_tid)

    return (
        f"¡Tarea '{html.escape(true_name)}' rotada correctamente!\n"
        f"Ahora le toca a {mention}."
    )


async def terminada(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    user_id = update.effective_user.id
    

    if not is_permited_chat(update, context):
        await update.message.reply_text(
            "Este comando solo puede usarse en el chat de roomies" 
        )
        return 
    
    if not context.args:
        await update.message.reply_text(
            "USO:\n" 
            "/terminada nombre de la tarea\n"
            "Ejemplo:\n"
             "/terminada limpiar cocina"
        )
        return

    task_name = " ".join(context.args)
    connection = get_connection()

    try:
        hwork_id = get_housework_id(task_name, connection)
        if hwork_id is None:
            await update.message.reply_text(
                f"No se encontró la tarea '{task_name}'."
            )
            return

        tid_fom_hwork = pd.read_sql(roomie_telegram_id_from_hwork, connection, params=(hwork_id,)).iloc[0,0]

        if int(user_id) not in ADMIN_USERS | {int(tid_fom_hwork)}:
            await update.message.reply_text("No tienes autorización para rotar esta tarea.\nNo eres admin o no la tienes asignada")
            return

        block_reason = rotation_block_reason(hwork_id, connection)
        if block_reason is not None:
            true_name = pd.read_sql(hwork_name_query, connection, params = (hwork_id,)).iloc[0,0]
            await update.message.reply_text(
                f"⏳ La tarea '{true_name}' {block_reason}"
            )
            return

        await update.message.reply_text(
            rotate_and_report(hwork_id, connection)
            + "\n\n" + admin_notice(connection),
            parse_mode="HTML",
        )

    except Exception:
        connection.rollback()
        await update.message.reply_text(
            "No se pudo actualizar la tarea."
        )
        raise

    finally:
        connection.close()

################
## MIS TAREAS ##
################

async def mis_tareas(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:

    try:
        user_id = update.effective_user.id
        connection = get_connection()
        roomie_id = pd.read_sql(roomie_id_from_tid, connection, params = (int(user_id),)).iloc[0,0]
        roomie_name = pd.read_sql(roomie_name_from_rid, connection, params = (int(roomie_id),)).iloc[0,0]
        tareas = pd.read_sql(assigned_hwork_from_rid, connection, params = (int(roomie_id),))
        if tareas.empty:
            await update.message.reply_text(
                f"Hola, {roomie_name}. Por ahora no tienes tareas asignadas."
            )
            return
        else:
            tareas["fecha_limite"] = pd.to_datetime(
                tareas["fecha_limite"]
            ).dt.strftime("%d/%m/%Y")
            
            tareas["fecha_asignación"] = pd.to_datetime(
                tareas["fecha_asignación"]
            ).dt.strftime("%d/%m/%Y")
            
            bloques = []
            
            for _, tarea in tareas.iterrows():
                bloques.append(
                    f"<b>{html.escape(str(tarea['tarea']))}</b>\n"
                    f"📅 Fecha límite: {tarea['fecha_limite']}\n"
                    f"🕒 Asignada: {tarea['fecha_asignación']}"
                )
            
            mensaje = (
                "<b>Tienes asignadas las siguientes tareas:</b>\n\n"
                + "\n\n".join(bloques)
            )
            
            await update.message.reply_text(mensaje,
                                            parse_mode = "HTML")


    except Exception:
        connection.rollback()
        await update.message.reply_text(
            "Toñotrón no pudo consultar tus tareas asignadas. "
        )
        raise

    finally:
        connection.close()

#################
## ROL SEMANAL ##
#################

async def rol_semanal(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:

    try:
        user_id = update.effective_user.id
        connection = get_connection()
        roomie_id = pd.read_sql(roomie_id_from_tid, connection, params = (int(user_id),)).iloc[0,0]
        roomie_name = pd.read_sql(roomie_name_from_rid, connection, params = (int(roomie_id),)).iloc[0,0]
        rol_sem = pd.read_sql(weekly_rol, connection)
        if rol_sem.empty:
            await update.message.reply_text(
                f"Hola, {roomie_name}. La asignación semanal está vacía, debe haber algún error."
            )
            return
        else:
            rol_sem["fecha_limite"] = pd.to_datetime(
                rol_sem["fecha_limite"]
            ).dt.strftime("%d/%m/%Y")

            bloques = []
            
            for _, rol in rol_sem.iterrows():
                bloques.append(
                    f"<b>{html.escape(str(rol['tarea']))}</b>\n"
                    f"👤 Le toca a: {rol['le_toca_a']}\n"
                    f"📅 Fecha límite: {rol['fecha_limite']}"
                )
            
            mensaje = (
                "<b>Este es el rol actual:</b>\n\n"
                + "\n\n".join(bloques)
            )
            
            await update.message.reply_text(mensaje,
                                            parse_mode = "HTML")

    except Exception:
        connection.rollback()
        await update.message.reply_text(
            "Toñotrón no pudo consultar el rol."
        )
        raise

    finally:
        connection.close()


#################
## RESPONSABLE ##
#################

async def responsable(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:

    if not context.args:
        await update.message.reply_text(
            "USO:\n"
            "/responsable nombre de la tarea\n"
            "Ejemplo:\n"
            "/responsable limpiar cocina"
        )
        return

    task_name = " ".join(context.args)
    connection = get_connection()

    try:
        hwork_id = get_housework_id(task_name, connection)
        if hwork_id is None:
            await update.message.reply_text(
                f"No se encontró la tarea '{task_name}'."
            )
            return

        tarea = pd.read_sql(responsible_from_hwork, connection, params = (int(hwork_id),)).iloc[0]

        await update.message.reply_text(format_responsable(tarea),
                                        parse_mode = "HTML")

    except Exception:
        connection.rollback()
        await update.message.reply_text(
            "Toñotrón no pudo consultar el responsable de la tarea. "
        )
        raise

    finally:
        connection.close()

#############
## ASIGNAR ##
#############

async def asignar(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    
    if not is_permited_chat(update, context):
        await update.message.reply_text(
            "Este comando solo puede usarse en el chat de roomies" 
        )
        return

    if int(update.effective_user.id) not in ADMIN_USERS:
        await update.message.reply_text("No tienes autorización para asignar tareas.\nSolo los admins pueden hacerlo.")
        return

    if len(context.args) < 2:
        await update.message.reply_text(ASIGNADA_USAGE)
        return

    roomie_name, *task_words = context.args

    # Si la última palabra trae dígitos, se interpreta como fecha límite.
    if any(char.isdigit() for char in task_words[-1]):
        due_date = parse_date(task_words[-1])
        task_words = task_words[:-1]

        due_date_given = True

        if due_date is None or not task_words:
            await update.message.reply_text(ASIGNADA_USAGE)
            return

        if due_date < date.today():
            await update.message.reply_text(
                "La fecha límite no puede ser anterior a hoy.\n\n" + ASIGNADA_USAGE
            )
            return
    else:
        due_date = next_sunday().date()
        due_date_given = False

    task_name = " ".join(task_words)
    connection = get_connection()

    try:
        roomie_id = get_roomie_id(roomie_name, connection)
        if roomie_id is None:
            await update.message.reply_text(
                f"No se encontró al roomie '{roomie_name}'.\n\n" + ASIGNADA_USAGE
            )
            return

        hwork_id = get_housework_id(task_name, connection)
        if hwork_id is None:
            await update.message.reply_text(
                f"No se encontró la tarea '{task_name}'.\n\n" + ASIGNADA_USAGE
            )
            return
        
        if int(hwork_id) == WATER_HWORK_ID and not due_date_given: #Comprar agua no lleva fecha límite
            due_date = None

        assign_hwork(int(hwork_id), int(roomie_id), due_date, connection)

        tarea = pd.read_sql(responsible_from_hwork, connection, params = (int(hwork_id),)).iloc[0]

        await update.message.reply_text(
            "¡Tarea asignada correctamente!\n\n" + format_responsable(tarea),
            parse_mode = "HTML"
        )

    except Exception:
        connection.rollback()
        await update.message.reply_text(
            "Toñotrón no pudo asignar la tarea."
        )
        raise

    finally:
        connection.close()

########################
## TERMINÉ MIS TAREAS ##
########################

async def termine_mis_tareas(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    
    if not is_permited_chat(update, context):
        await update.message.reply_text(
            "Este comando solo puede usarse en el chat de roomies" 
        )
        return

    user_id = update.effective_user.id
    connection = get_connection()

    try:
        roomie = pd.read_sql(roomie_id_from_tid, connection, params = (int(user_id),))
        if roomie.empty:
            await update.message.reply_text(
                "No estás registrado como roomie."
            )
            return

        roomie_id = int(roomie.iloc[0,0])
        hwork_ids = pd.read_sql(assigned_hwork_ids_from_rid, connection, params = (roomie_id,))["housework_id"]

        if hwork_ids.empty:
            await update.message.reply_text(
                "No tienes tareas asignadas, no hay nada que terminar."
            )
            return

        bloques = []
        rotated_any = False

        for hwork_id in hwork_ids:
            block_reason = rotation_block_reason(int(hwork_id), connection)

            if block_reason is None:
                bloques.append(rotate_and_report(int(hwork_id), connection))
                rotated_any = True
            else:
                true_name = pd.read_sql(hwork_name_query, connection, params = (int(hwork_id),)).iloc[0,0]
                bloques.append(f"⏳ La tarea '{html.escape(true_name)}' {block_reason}")

        if rotated_any:
            bloques.append(admin_notice(connection))

        await update.message.reply_text(
            "\n\n".join(bloques),
            parse_mode = "HTML"
        )

    except Exception:
        connection.rollback()
        await update.message.reply_text(
            "Toñotrón no pudo terminar todas tus tareas. Revisa /mis_tareas."
        )
        raise

    finally:
        connection.close()

################
## VER TAREAS ##
################

async def ver_tareas(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:

    connection = get_connection()

    try:
        tareas = pd.read_sql(hwork_list, connection)
        if tareas.empty:
            await update.message.reply_text(
                "No hay tareas registradas."
            )
            return

        lineas = [
            f"• {html.escape(str(tarea))}"
            for tarea in tareas["tarea"]
        ]

        await update.message.reply_text(
            "<b>Tareas registradas:</b>\n\n" + "\n".join(lineas),
            parse_mode = "HTML"
        )

    except Exception:
        connection.rollback()
        await update.message.reply_text(
            "Toñotrón no pudo consultar la lista de tareas."
        )
        raise

    finally:
        connection.close()

#################
## VER ROOMIES ##
#################

async def ver_roomies(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:

    connection = get_connection()

    try:
        roomies = pd.read_sql(roomies_by_turn, connection)
        if roomies.empty:
            await update.message.reply_text(
                "No hay roomies registrados."
            )
            return

        lineas = [
            f"{roomie['turno']}. {html.escape(str(roomie['roomie_name']))} "
            f"{html.escape(str(roomie['last_name']))}"
            for _, roomie in roomies.iterrows()
        ]

        await update.message.reply_text(
            "<b>Roomies por turno:</b>\n\n" + "\n".join(lineas),
            parse_mode = "HTML"
        )

    except Exception:
        connection.rollback()
        await update.message.reply_text(
            "Toñotrón no pudo consultar la lista de roomies."
        )
        raise

    finally:
        connection.close()

#################
## NUEVA TAREA ##
#################

async def nueva_tarea(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:

    if not is_permited_chat(update, context):
        await update.message.reply_text(
            "Este comando solo puede usarse en el chat de roomies"
        )
        return

    if int(update.effective_user.id) not in ADMIN_USERS:
        await update.message.reply_text("No tienes autorización para modificar tareas.\nSolo los admins pueden hacerlo.")
        return

    if len(context.args) < 2 or context.args[0].lower() not in ("agregar", "borrar"):
        await update.message.reply_text(NUEVA_TAREA_USAGE)
        return

    action = context.args[0].lower()
    task_name = " ".join(context.args[1:])

    if action == "agregar" and len(task_name) > HWORK_NAME_MAX_LEN:
        await update.message.reply_text(
            f"El nombre de la tarea no puede pasar de {HWORK_NAME_MAX_LEN} caracteres."
        )
        return

    connection = get_connection()

    try:
        hwork_id = get_housework_id(task_name, connection)

        if action == "agregar":
            if hwork_id is not None:
                await update.message.reply_text(
                    f"La tarea '{task_name}' ya existe."
                )
                return

            first_roomie = pd.read_sql(next_roomie_by_turn, connection, params = (0,))
            if first_roomie.empty:
                await update.message.reply_text(
                    "No hay roomies registrados a quien asignar la tarea."
                )
                return

            with connection.cursor() as cursor:
                cursor.execute(insert_housework, (task_name,))
                new_hwork_id = cursor.fetchone()[0]
                cursor.execute(
                    insert_assignment,
                    (new_hwork_id, int(first_roomie.iloc[0,0]), next_sunday().date())
                )

            connection.commit()

            tarea = pd.read_sql(responsible_from_hwork, connection, params = (int(new_hwork_id),)).iloc[0]

            await update.message.reply_text(
                "¡Tarea agregada correctamente!\n\n" + format_responsable(tarea),
                parse_mode = "HTML"
            )

        else:
            if hwork_id is None:
                await update.message.reply_text(
                    f"No se encontró la tarea '{task_name}'."
                )
                return

            # El bot depende de este ID para tratar "Comprar agua" de forma especial.
            if int(hwork_id) == WATER_HWORK_ID:
                await update.message.reply_text(
                    "La tarea 'Comprar agua' no se puede borrar."
                )
                return

            true_name = pd.read_sql(hwork_name_query, connection, params = (int(hwork_id),)).iloc[0,0]

            with connection.cursor() as cursor:
                cursor.execute(delete_rotation_log_from_hwork, (int(hwork_id),))
                cursor.execute(delete_assignment_from_hwork, (int(hwork_id),))
                cursor.execute(delete_housework, (int(hwork_id),))

            connection.commit()

            await update.message.reply_text(
                f"Tarea '{true_name}' borrada correctamente."
            )

    except Exception:
        connection.rollback()
        await update.message.reply_text(
            "Toñotrón no pudo modificar las tareas."
        )
        raise

    finally:
        connection.close()

##################
## NUEVO ROOMIE ##
##################

async def nuevo_roomie(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:

    if not is_permited_chat(update, context):
        await update.message.reply_text(
            "Este comando solo puede usarse en el chat de roomies"
        )
        return

    if int(update.effective_user.id) not in ADMIN_USERS:
        await update.message.reply_text("No tienes autorización para modificar roomies.\nSolo los admins pueden hacerlo.")
        return

    if not context.args or context.args[0].lower() not in ("agregar", "borrar"):
        await update.message.reply_text(NUEVO_ROOMIE_USAGE)
        return

    action, *params = context.args
    action = action.lower()

    if action == "agregar":
        reply_to = update.message.reply_to_message

        # Sin telegram_id explícito, se toma el del autor del mensaje respondido.
        if len(params) == 4:
            name, last_name, phone, telegram_id = params
        elif len(params) == 3 and reply_to is not None:
            name, last_name, phone = params
            telegram_id = str(reply_to.from_user.id)
        else:
            await update.message.reply_text(NUEVO_ROOMIE_USAGE)
            return

        if not telegram_id.isdigit():
            await update.message.reply_text(
                "El telegram_id debe ser un número.\n\n" + NUEVO_ROOMIE_USAGE
            )
            return

        if any(len(field) > ROOMIE_FIELD_MAX_LEN for field in (name, last_name, phone, telegram_id)):
            await update.message.reply_text(
                f"Nombre, apellido, teléfono y telegram_id no pueden pasar de {ROOMIE_FIELD_MAX_LEN} caracteres."
            )
            return

    elif len(params) != 1:
        await update.message.reply_text(NUEVO_ROOMIE_USAGE)
        return

    connection = get_connection()

    try:
        if action == "agregar":
            # Los comandos buscan a los roomies por nombre, así que no puede repetirse.
            if get_roomie_id(name, connection) is not None:
                await update.message.reply_text(
                    f"Ya hay un roomie llamado '{name}'. Usa otro nombre."
                )
                return

            if not pd.read_sql(roomie_id_from_tid, connection, params = (int(telegram_id),)).empty:
                await update.message.reply_text(
                    "Ese telegram_id ya está registrado."
                )
                return

            with connection.cursor() as cursor:
                cursor.execute(insert_roomie, (name, last_name, phone, telegram_id))
                turn = cursor.fetchone()[0]

            connection.commit()

            await update.message.reply_text(
                "¡Roomie agregado correctamente!\n\n"
                f"{mention_html(name, telegram_id)} tiene el turno {turn}.",
                parse_mode = "HTML"
            )

        else:
            roomie_id = get_roomie_id(params[0], connection)
            if roomie_id is None:
                await update.message.reply_text(
                    f"No se encontró al roomie '{params[0]}'."
                )
                return

            roomie_name = pd.read_sql(roomie_name_from_rid, connection, params = (int(roomie_id),)).iloc[0,0]
            tareas = pd.read_sql(assigned_hwork_from_rid, connection, params = (int(roomie_id),))

            if not tareas.empty:
                await update.message.reply_text(
                    f"No se puede borrar a {roomie_name} porque tiene asignadas: "
                    + ", ".join(tareas["tarea"])
                    + ".\nReasígnalas antes con /asignar."
                )
                return

            with connection.cursor() as cursor:
                cursor.execute(delete_roomie, (int(roomie_id),))
                turn = cursor.fetchone()[0]
                cursor.execute(negate_turns_after, (turn,))
                cursor.execute(restore_negated_turns)

            connection.commit()

            await update.message.reply_text(
                f"Roomie '{roomie_name}' borrado correctamente. "
                "Los turnos siguientes se recorrieron una posición."
            )

    except Exception:
        connection.rollback()
        await update.message.reply_text(
            "Toñotrón no pudo modificar los roomies."
        )
        raise

    finally:
        connection.close()

###########
## AYUDA ##
###########

async def ayuda(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:

    await update.message.reply_text(
        "COMANDOS DE TOÑOTRÓN\n\n"
        "━━ CONSULTA ━━\n\n"
        "/mis_tareas\n"
        "    Muestra tus tareas asignadas.\n\n"
        "/rol\n"
        "    Muestra el rol actual de todas las tareas.\n\n"
        "/responsable nombre de la tarea\n"
        "    Muestra a quién le toca una tarea.\n"
        "    Ejemplo:\n"
        "        /responsable limpiar cocina\n\n"
        "/ver_tareas\n"
        "    Muestra la lista de tareas registradas.\n\n"
        "/ver_roomies\n"
        "    Muestra la lista de roomies con su turno.\n\n"
        "━━ ROTACIÓN DE TAREAS ━━\n\n"
        "/terminada nombre de la tarea\n"
        "    Rota la tarea al siguiente roomie. Solo quien la tiene asignada o un admin.\n"
        "    Ejemplo:\n"
        "        /terminada limpiar cocina\n\n"
        "/termine_mis_tareas\n"
        "    Rota todas las tareas que tienes asignadas.\n\n"
        "━━ SOLO ADMINS ━━\n\n"
        "/asignar nombre_roomie nombre de la tarea [dd/mm/aaaa]\n"
        "    Asigna una tarea a un roomie.\n"
        "    Ejemplo:\n"
        "        /asignar Joshua limpiar cocina 01/11/2026"
    )
