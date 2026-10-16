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
from queries.queries import hwork_name_query

# Sustituye estos valores por tus datos reales.
BOT_TOKEN = "8750452341:AAECLsAPQYb56XXi9oAOje9-Cm3-kZgZEVA"
AUTHORIZED_USERS = {5993413477}  # IDs de Telegram autorizados


async def terminada(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    user_id = update.effective_user.id

    if user_id not in AUTHORIZED_USERS:
        await update.message.reply_text("No tienes autorización.")
        return

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



        rotate_hwork(hwork_id, connection)

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
