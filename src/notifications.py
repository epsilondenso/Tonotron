import os
import html
import datetime
from dotenv import load_dotenv

import pandas as pd

from telegram.ext import Application, ContextTypes

from src.connect_db import get_connection
from src.handlers import mention_html
from src.utils import DATE_FORMAT
from src.sql import hwork_due_on, overdue_hwork

load_dotenv()

# Chat donde se publican los avisos. Si no se define (o está vacío), el de producción.
NOTIFICATION_CHAT = int(os.getenv("ID_CHAT_NOTIFICACIONES") or os.getenv("ID_CHAT_PROD"))
# Hora local (HH:MM) a la que se revisan las fechas límite cada día.
NOTIFICATION_TIME = datetime.datetime.strptime(
    os.getenv("NOTIFICATION_TIME", "10:00"), "%H:%M"
).time()
# Con cuántos días de anticipación se avisa que una tarea está por vencer.
NOTICE_DAYS_BEFORE = 2


def format_aviso(tarea: pd.Series, detalle: str) -> str:
    """
    Arma el bloque HTML de una tarea dentro de un aviso.

    Parameters
    ----------
    tarea : pd.Series
        Fila de ``hwork_due_on`` u ``overdue_hwork``.
    detalle : str
        Texto que acompaña a la fecha límite (p. ej. ``"vence en 2 días"``).

    Returns
    -------
    str
        Bloque listo para enviar con ``parse_mode="HTML"``.
    """

    fecha_limite = pd.to_datetime(tarea["fecha_limite"]).strftime(DATE_FORMAT)
    mention = mention_html(tarea["le_toca_a"], tarea["telegram_id"])

    return (
        f"<b>{html.escape(str(tarea['tarea']))}</b>\n"
        f"👤 Le toca a: {mention}\n"
        f"📅 Fecha límite: {fecha_limite} ({detalle})"
    )


def build_notification(today: datetime.date, connection) -> str | None:
    """
    Arma el aviso diario de tareas por vencer y vencidas.

    Una tarea está por vencer si su ``due_date`` es exactamente
    ``NOTICE_DAYS_BEFORE`` días después de ``today``, y vencida si su
    ``due_date`` es anterior a ``today``. Las tareas sin fecha límite
    ("Comprar agua") nunca aparecen.

    Parameters
    ----------
    today : datetime.date
        Día de referencia (hoy, en hora local).
    connection : PGConnection
        Conexión abierta a la base de datos.

    Returns
    -------
    str or None
        Mensaje listo para enviar con ``parse_mode="HTML"``, o ``None``
        si no hay nada que avisar.
    """

    por_vencer = pd.read_sql(
        hwork_due_on, connection,
        params = (today + datetime.timedelta(days = NOTICE_DAYS_BEFORE),)
    )
    vencidas = pd.read_sql(overdue_hwork, connection, params = (today,))

    secciones = []

    if not vencidas.empty:
        bloques = []
        for _, tarea in vencidas.iterrows():
            dias = (today - pd.to_datetime(tarea["fecha_limite"]).date()).days
            bloques.append(format_aviso(tarea, f"vencida hace {dias} día(s)"))

        secciones.append(
            "<b>🚨 Tareas vencidas:</b>\n\n" + "\n\n".join(bloques)
        )

    if not por_vencer.empty:
        bloques = [
            format_aviso(tarea, f"vence en {NOTICE_DAYS_BEFORE} días")
            for _, tarea in por_vencer.iterrows()
        ]

        secciones.append(
            "<b>⏰ Tareas por vencer:</b>\n\n" + "\n\n".join(bloques)
        )

    if not secciones:
        return None

    return "\n\n".join(secciones)


async def avisar_vencimientos(context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Job diario: publica en ``NOTIFICATION_CHAT`` las tareas por vencer y vencidas.

    No guarda estado: una tarea vencida se vuelve a avisar cada día hasta
    que alguien la rota o la reasigna, porque eso cambia su ``due_date``.

    Parameters
    ----------
    context : ContextTypes.DEFAULT_TYPE
        Contexto del job; se usa ``context.bot`` para enviar el mensaje.

    Returns
    -------
    None
    """

    connection = get_connection()

    try:
        mensaje = build_notification(datetime.date.today(), connection)

        if mensaje is not None:
            await context.bot.send_message(
                chat_id = NOTIFICATION_CHAT,
                text = mensaje,
                parse_mode = "HTML"
            )

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def schedule_notifications(app: Application) -> None:
    """
    Programa ``avisar_vencimientos`` todos los días a ``NOTIFICATION_TIME``.

    La hora se interpreta en la zona horaria local del proceso (``TZ``),
    la misma que usan los límites de rotación.

    Parameters
    ----------
    app : Application
        Aplicación del bot, ya construida.

    Returns
    -------
    None
    """

    if app.job_queue is None:
        raise RuntimeError(
            "JobQueue no disponible: instala python-telegram-bot[job-queue]."
        )

    local_tz = datetime.datetime.now().astimezone().tzinfo

    app.job_queue.run_daily(
        avisar_vencimientos,
        time = NOTIFICATION_TIME.replace(tzinfo = local_tz),
        name = "avisar_vencimientos"
    )

    return None
