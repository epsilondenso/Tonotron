import os
import html
from dotenv import load_dotenv

import pandas as pd

from telegram import Update
from telegram.ext import ContextTypes

from src.connect_db import get_connection
from src.rotate_hwork import rotate_hwork
from src.queries import get_housework_id
from src.sql import (
    hwork_name_query,
    next_roomie_from_hwork,
    roomie_telegram_id_from_hwork,
    assigned_hwork_from_rid,
    roomie_id_from_tid,
    roomie_name_from_rid
)

load_dotenv()
ADMIN_USERS = {os.getenv("ADMIN_USER_1"), os.getenv("ADMIN_USER_2")}

async def terminada(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    user_id = update.effective_user.id
    



    if not context.args:
        await update.message.reply_text(
            "Uso: /terminada nombre de la tarea\n"
            "Ejemplo: /terminada limpiar cocina"
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
        true_name = pd.read_sql(hwork_name_query, connection, params = (hwork_id,)).iloc[0,0]

        tid_fom_hwork = pd.read_sql(roomie_telegram_id_from_hwork, connection, params=(hwork_id,)).iloc[0,0]

        if user_id not in ADMIN_USERS | {int(tid_fom_hwork)}:
            await update.message.reply_text("No tienes autorización para rotar esta tarea.\nNo eres admin o no la tienes asignada")
            return

        rotate_hwork(hwork_id, connection)
        next_name, next_tid = pd.read_sql(
            next_roomie_from_hwork, connection, params=(hwork_id,)
        ).iloc[0]
        mention = f'<a href="tg://user?id={int(next_tid)}">{html.escape(next_name)}</a>'

        await update.message.reply_text(
            f"¡Tarea '{html.escape(true_name)}' rotada correctamente!\n"
            f"Ahora le toca a {mention}.",
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
    context: ContextTypes.DEFAULT_TYPE,
) -> None:

    try:
        user_id = update.effective_user.id
        connection = get_connection()
        roomie_id = pd.read_sql(roomie_id_from_tid, connection, params = (int(user_id),)).iloc[0,0]
        roomie_name = pd.read_sql(roomie_name_from_rid, connection, params = (int(roomie_id),)).iloc[0,0]
        tareas = pd.read_sql(assigned_hwork_from_rid, connection, params = (int(roomie_id),))
        if tareas.empty:
            await update.message.reply_text(
                f"Hola, {roomie_name}. Por ahora no tienes tareas asignadas, pero cuídate la espalda."
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
            "Toñotrón no pudo consultar tus tareas asignadas."
        )
        raise

    finally:
        connection.close()