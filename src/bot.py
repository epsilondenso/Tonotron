import os

from dotenv import load_dotenv

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler
    )

from src.handlers import (
    terminada,
    mis_tareas,
    rol_semanal,
    responsable,
    asignar,
    termine_mis_tareas
)

load_dotenv()
BOT_TOKEN = os.getenv("PRUEBAS_TOKEN")

def main() -> None:
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("terminada", terminada))
    app.add_handler(CommandHandler("mis_tareas",  mis_tareas))
    app.add_handler(CommandHandler("rol_semanal",  rol_semanal))
    app.add_handler(CommandHandler("responsable",  responsable))
    app.add_handler(CommandHandler("asignar",  asignar))
    app.add_handler(CommandHandler("termine_mis_tareas",  termine_mis_tareas))
    app.run_polling()


if __name__ == "__main__":
    main()
