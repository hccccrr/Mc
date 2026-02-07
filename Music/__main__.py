"""
HellMusic V3 - Main Entry Point
Modern startup system with enhanced logging
"""

import asyncio

from pyrogram import idle

from config import Config
from Music.core.calls import call_handler
from Music.core.clients import hellbot
from Music.core.database import db
from Music.core.logger import LOGS
from Music.core.users import user_data
from Music.helpers.strings import TEXTS
from Music.version import __version__


async def start_bot():
    """Main startup function for HellMusic V3"""
    
    # Get version info
    hmusic_version = __version__.get("Hell Music", "3.0")
    py_version = __version__.get("Python", "3.10+")
    pyro_version = __version__.get("Pyrogram", "2.0+")
    pycalls_version = __version__.get("PyTgCalls", "3.0+")
    
    LOGS.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    LOGS.info("🚀 Starting HellMusic V3...")
    LOGS.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    # Setup users and database
    await user_data.setup()
    await db.connect()
    
    # Start clients
    await hellbot.start()
    
    LOGS.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    LOGS.info("✅ HellMusic V3 Started Successfully!")
    LOGS.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    # Send startup message to logger
    try:
        startup_text = TEXTS.BOOTED.format(
            Config.BOT_NAME if hasattr(Config, 'BOT_NAME') else hellbot.app.name,
            hmusic_version,
            py_version,
            pyro_version,
            pycalls_version,
            hellbot.app.mention,
        )
        
        if hasattr(Config, 'BOT_PIC') and Config.BOT_PIC:
            await hellbot.app.send_photo(
                chat_id=int(Config.LOGGER_ID),
                photo=Config.BOT_PIC,
                caption=startup_text,
            )
        else:
            await hellbot.app.send_message(
                chat_id=int(Config.LOGGER_ID),
                text=startup_text,
            )
    except Exception as e:
        LOGS.warning(f"⚠️ Could not send startup message: {e}")
    
    LOGS.info(f"🎵 HellMusic V3 [{hmusic_version}] is now online!")
    LOGS.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    # Keep the bot running
    await idle()
    
    # Shutdown
    LOGS.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    LOGS.info("🛑 Shutting down HellMusic V3...")
    LOGS.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    try:
        await hellbot.app.send_message(
            chat_id=Config.LOGGER_ID,
            text=f"**#STOP**\n\n**🛑 HellMusic V3 [{hmusic_version}] is now offline!**",
        )
    except Exception:
        pass
    
    await hellbot.stop()
    
    LOGS.info(f"👋 HellMusic V3 [{hmusic_version}] stopped!")
    LOGS.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")


if __name__ == "__main__":
    # Run the bot
    try:
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        LOGS.info("⚠️ Bot stopped by user!")
    except Exception as e:
        LOGS.error(f"❌ Fatal error: {e}")
