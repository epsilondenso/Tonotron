import os

from dotenv import load_dotenv

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler
    )

from src.handlers.terminada import terminada

load_dotenv()
BOT_TOKEN = os.getenv("PRUEBAS_TOKEN")

def main() -> None:
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("terminada", terminada))
    app.run_polling()


if __name__ == "__main__":
    main()
