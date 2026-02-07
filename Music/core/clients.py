"""
HellMusic V3 - Client Manager
Modern Pyrogram client initialization with enhanced features
"""

from pyrogram import Client
from pyrogram.enums import ParseMode

from config import Config
from Music.utils.exceptions import HellBotException

from .logger import LOGS


class HellClient:
    """Advanced client management for HellMusic V3"""
    
    def __init__(self):
        # Bot client configuration
        self.app = Client(
            name="HellMusicV3",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            plugins=dict(root="Music.plugins"),
            workers=200,
            parse_mode=ParseMode.MARKDOWN,
            sleep_threshold=60,
            max_concurrent_transmissions=4,
        )

        # Userbot client configuration
        self.user = Client(
            name="HellAssistantV3",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            session_string=Config.HELLBOT_SESSION,
            no_updates=True,
            parse_mode=ParseMode.MARKDOWN,
        )

    async def start(self):
        """Initialize and start all clients"""
        LOGS.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        LOGS.info("🎵 Starting HellMusic V3...")
        LOGS.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        # Start bot client
        if Config.BOT_TOKEN:
            await self.app.start()
            me = await self.app.get_me()
            
            # Store bot info
            self.app.id = me.id
            self.app.mention = me.mention
            self.app.name = me.first_name
            self.app.username = me.username
            
            LOGS.info(f"✅ Bot Client: @{self.app.username}")
            LOGS.info(f"📌 Bot ID: {self.app.id}")
            LOGS.info(f"👤 Bot Name: {self.app.name}")
        else:
            LOGS.error("❌ BOT_TOKEN not found!")
            raise HellBotException("BOT_TOKEN is required!")
        
        # Start userbot client
        if Config.HELLBOT_SESSION:
            try:
                await self.user.start()
                me = await self.user.get_me()
                
                # Store userbot info
                self.user.id = me.id
                self.user.mention = me.mention
                self.user.name = me.first_name
                self.user.username = me.username if me.username else "Assistant"
                
                LOGS.info(f"✅ Assistant: @{self.user.username}")
                LOGS.info(f"📌 Assistant ID: {self.user.id}")
                
                # Auto-join support channels
                try:
                    await self.user.join_chat("Its_HellBot")
                    await self.user.join_chat("HellBot_Chats")
                    LOGS.info("✅ Joined support channels")
                except Exception as e:
                    LOGS.warning(f"⚠️ Could not join channels: {e}")
                    
            except Exception as e:
                LOGS.error(f"❌ Failed to start assistant: {e}")
                LOGS.warning("⚠️ Running without assistant (limited features)")
        else:
            LOGS.warning("⚠️ HELLBOT_SESSION not provided")
            LOGS.warning("⚠️ Running without assistant (limited features)")
        
        LOGS.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        LOGS.info("🎉 HellMusic V3 Started Successfully!")
        LOGS.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    async def stop(self):
        """Stop all clients gracefully"""
        LOGS.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        LOGS.info("🛑 Stopping HellMusic V3...")
        LOGS.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        if self.app:
            await self.app.stop()
            LOGS.info("✅ Bot client stopped")
            
        if self.user:
            try:
                await self.user.stop()
                LOGS.info("✅ Assistant stopped")
            except Exception:
                pass
                
        LOGS.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        LOGS.info("👋 HellMusic V3 Stopped!")
        LOGS.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    async def logit(self, hash: str, log: str, file: str = None):
        """
        Send logs to logger channel
        
        Args:
            hash: Log tag/category
            log: Log message
            file: Optional file to send
        """
        log_text = f"**#{hash.upper()}**\n\n{log}"
        
        try:
            if file:
                await self.app.send_document(
                    chat_id=Config.LOGGER_ID,
                    document=file,
                    caption=log_text[:1024],  # Telegram caption limit
                )
            else:
                await self.app.send_message(
                    chat_id=Config.LOGGER_ID,
                    text=log_text,
                    disable_web_page_preview=True,
                )
        except Exception as e:
            LOGS.error(f"❌ Failed to send log: {e}")
            raise HellBotException(f"[LogError]: {e}")

    async def send_error_log(self, error: Exception, context: str = ""):
        """
        Send error logs to logger channel
        
        Args:
            error: Exception object
            context: Additional context about the error
        """
        error_text = (
            f"**🚨 ERROR LOG**\n\n"
            f"**Context:** {context}\n"
            f"**Error Type:** `{type(error).__name__}`\n"
            f"**Error Message:** `{str(error)}`"
        )
        
        try:
            await self.logit("ERROR", error_text)
        except Exception:
            LOGS.error(f"❌ Critical error logging failure: {error}")


# Global client instance
hellbot = HellClient()
