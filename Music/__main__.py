from config import Config
from Music.core.calls import hellmusic
from Music.core.clients import hellbot
from Music.core.database import db
from Music.core.logger import LOGS
from Music.core.users import user_data
from Music.helpers.strings import TEXTS
from Music.version import __version__


async def start_bot():
    hmusic_version = __version__["Hell Music"]
    py_version = __version__["Python"]
    telethon_version = __version__["Telethon"]
    pycalls_version = __version__["PyTgCalls"]

    LOGS.info("All Checks Completed! Let's Start Hell-Music...")

    await user_data.setup()
    await hellbot.start()
    await hellmusic.start()
    await db.connect()

    try:
        if Config.BOT_PIC:
            await hellbot.app.send_file(
                int(Config.LOGGER_ID),
                Config.BOT_PIC,
                caption=TEXTS.BOOTED.format(
                    Config.BOT_NAME,
                    hmusic_version,
                    py_version,
                    telethon_version,
                    pycalls_version,
                    f"@{hellbot.app.me.username}",
                ),
            )
        else:
            await hellbot.app.send_message(
                int(Config.LOGGER_ID),
                TEXTS.BOOTED.format(
                    Config.BOT_NAME,
                    hmusic_version,
                    py_version,
                    telethon_version,
                    pycalls_version,
                    f"@{hellbot.app.me.username}",
                ),
            )
    except Exception as e:
        LOGS.warning(f"Error in Logger: {e}")

    LOGS.info(f">> Hell-Music [{hmusic_version}] is now online!")

    # Run until disconnected
    await hellbot.app.run_until_disconnected()

    await hellbot.app.send_message(
        Config.LOGGER_ID,
        f"#STOP\n\n**Hell-Music [{hmusic_version}] is now offline!**",
    )
    LOGS.info(f"Hell-Music [{hmusic_version}] is now offline!")


import asyncio

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_bot())
