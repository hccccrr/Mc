"""
HellMusic V3 - Main Entry Point
Clean & Safe startup system (Pyrogram + PyTgCalls compatible)
"""

import asyncio
import signal

from pyrogram import idle

from config import Config
from Music.core.clients import hellbot
from Music.core.database import db
from Music.core.logger import LOGS
from Music.core.users import user_data
from Music.helpers.strings import TEXTS
from Music.version import __version__


async def start_bot():
    """Main startup function for HellMusic V3"""

    hmusic_version = __version__.get("Hell Music", "3.0")
    py_version = __version__.get("Python", "3.10+")
    pyro_version = __version__.get("Pyrogram", "2.0+")
    pycalls_version = __version__.get("PyTgCalls", "3.0+")

    LOGS.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    LOGS.info("🚀 Starting HellMusic V3...")
    LOGS.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    # Init core systems
    await user_data.setup()
    await db.connect()

    # Start bot client
    await hellbot.start()

    LOGS.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    LOGS.info("✅ HellMusic V3 Started Successfully!")
    LOGS.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    # Notify logger chat
    try:
        text = TEXTS.BOOTED.format(
            getattr(Config, "BOT_NAME", hellbot.app.name),
            hmusic_version,
            py_version,
            pyro_version,
            pycalls_version,
            hellbot.app.mention(style="md"),
        )

        if getattr(Config, "BOT_PIC", None):
            await hellbot.app.send_photo(
                Config.LOGGER_ID,
                Config.BOT_PIC,
                caption=text,
            )
        else:
            await hellbot.app.send_message(
                Config.LOGGER_ID,
                text,
            )
    except Exception as e:
        LOGS.warning(f"⚠️ Logger notify failed: {e}")

    LOGS.info(f"🎵 HellMusic V3 [{hmusic_version}] is now online!")
    LOGS.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    # Hold process
    await idle()

    # Shutdown sequence
    LOGS.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    LOGS.info("🛑 Shutting down HellMusic V3...")
    LOGS.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    try:
        await hellbot.app.send_message(
            Config.LOGGER_ID,
            f"**#STOP**\n\n**🛑 HellMusic V3 [{hmusic_version}] is now offline!**",
        )
    except Exception:
        pass

    await hellbot.stop()
    await db.close()

    LOGS.info(f"👋 HellMusic V3 [{hmusic_version}] stopped cleanly!")


def main():
    """Safe event-loop runner (NO asyncio.run)"""
    loop = asyncio.get_event_loop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, loop.stop)

    try:
        loop.run_until_complete(start_bot())
    finally:
        loop.close()


if __name__ == "__main__":
    main()
