import os

from dotenv import load_dotenv
import pandas as pd

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

from src.connect_db import get_connection
from src.rotate_hwork import rotate_hwork
from src.queries import get_housework_id
from src.sql import hwork_name_query, roomie_telegram_id_from_hwork

# Sustituye estos valores por tus datos reales.
load_dotenv()
BOT_TOKEN = os.getenv("PRUEBAS_TOKEN")
ADMIN_USERS = {5848779012, 5993413477}  # IDs de Telegram admin: ANTONIO Y DENSEL

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
        next_roomie = pd.read_sql(roomie_telegram_id_from_hwork, connection, params=(hwork_id,)).iloc[0,0]

        await update.message.reply_text(
            f"¡Tarea '{true_name}' rotada correctamente!"
        )

    except Exception:
        connection.rollback()
        await update.message.reply_text(
            "No se pudo actualizar la tarea."
        )
        raise

    finally:
        connection.close()


def main() -> None:
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("terminada", terminada))
    app.run_polling()


if __name__ == "__main__":
    main()
