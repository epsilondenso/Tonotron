from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

from src.connect_db import get_connection
from src.rotate_hwork import rotate_hwork

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

    if len(context.args) != 1 or not context.args[0].isdigit():
        await update.message.reply_text(
            "Uso: /terminada ID\nEjemplo: /terminada 3"
        )
        return

    hwork_id = int(context.args[0])

    if hwork_id not in range(1, 6):
        await update.message.reply_text("ID de tarea inválido.")
        return

    connection = get_connection()

    try:
        rotate_hwork(hwork_id, connection)
        await update.message.reply_text(
            f"¡Tarea {hwork_id} rotada correctamente!"
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
