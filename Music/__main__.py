import asyncio
import signal
import sys

from config import Config
from Music.core.calls import hellmusic
from Music.core.clients import hellbot
from Music.core.database import db
from Music.core.logger import LOGS
from Music.core.users import user_data
from Music.helpers.strings import TEXTS
from Music.version import __version__


# Global flag for shutdown
is_shutting_down = False


async def shutdown_handler(signum=None, frame=None):
    """Handle graceful shutdown"""
    global is_shutting_down
    
    if is_shutting_down:
        return
    
    is_shutting_down = True
    
    hmusic_version = __version__["Hell Music"]
    
    LOGS.info("Shutdown signal received. Stopping Hell-Music...")
    
    try:
        # Send offline message
        await hellbot.app.send_message(
            Config.LOGGER_ID,
            f"#STOP\n\n**Hell-Music [{hmusic_version}] is now offline!**",
        )
    except Exception as e:
        LOGS.error(f"Error sending shutdown message: {e}")
    
    # Stop PyTgCalls
    try:
        await hellmusic.music.stop()
        LOGS.info("PyTgCalls stopped successfully!")
    except Exception as e:
        LOGS.error(f"Error stopping PyTgCalls: {e}")
    
    # Stop clients
    try:
        await hellbot.stop()
        LOGS.info("Clients disconnected successfully!")
    except Exception as e:
        LOGS.error(f"Error stopping clients: {e}")
    
    LOGS.info(f"Hell-Music [{hmusic_version}] is now offline!")


async def start_bot():
    """Main bot startup function"""
    global is_shutting_down
    
    hmusic_version = __version__["Hell Music"]
    py_version = __version__["Python"]
    telethon_version = __version__["Telethon"]
    pycalls_version = __version__["PyTgCalls"]

    LOGS.info("All Checks Completed! Let's Start Hell-Music...")

    # Setup components
    try:
        await user_data.setup()
        await hellbot.start()
        await hellmusic.start()
        await db.connect()
    except Exception as e:
        LOGS.error(f"Error during startup: {e}")
        sys.exit(1)

    # Send boot message
    try:
        if Config.BOT_PIC:
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
                file=Config.BOT_PIC,
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

    # Keep running until interrupted
    try:
        while not is_shutting_down:
            await asyncio.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        LOGS.info("Received exit signal...")
        await shutdown_handler()
    except Exception as e:
        LOGS.error(f"Unexpected error: {e}")
        await shutdown_handler()


def signal_handler(signum, frame):
    """Handle system signals"""
    LOGS.info(f"Received signal {signum}")
    loop = asyncio.get_event_loop()
    loop.create_task(shutdown_handler(signum, frame))


if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # kill command
    
    # Get event loop
    loop = asyncio.get_event_loop()
    
    try:
        # Run the bot
        loop.run_until_complete(start_bot())
    except KeyboardInterrupt:
        LOGS.info("Bot stopped by user")
    finally:
        # Cleanup
        if not loop.is_closed():
            loop.run_until_complete(shutdown_handler())
            loop.close()
        LOGS.info("Event loop closed. Goodbye!")
