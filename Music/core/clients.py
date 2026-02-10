from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.channels import JoinChannelRequest

from config import Config
from Music.utils.exceptions import HellBotException

from .logger import LOGS


class HellClient:
    def __init__(self):
        # Bot client
        self.app = TelegramClient(
            "HellMusic",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
        )

        # User client (assistant)
        self.user = TelegramClient(
            StringSession(Config.STRING_SESSION),
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
        )

    async def start(self):
        LOGS.info(">> Booting up HellMusic...")
        
        if Config.BOT_TOKEN:
            await self.app.start(bot_token=Config.BOT_TOKEN)
            me = await self.app.get_me()
            self.app.id = me.id
            self.app.name = me.first_name
            self.app.username = me.username
            # Store me object for later use
            self.app.me = me
            LOGS.info(f">> {self.app.name} is online now!")
        
        if Config.STRING_SESSION:
            await self.user.start()
            me = await self.user.get_me()
            self.user.id = me.id
            self.user.name = me.first_name
            self.user.username = me.username
            # Store me object for later use
            self.user.me = me
            
            try:
                await self.user(JoinChannelRequest("https://t.me/PBX_UPDATE"))
                await self.user(JoinChannelRequest("https://t.me/PBX_CHAT"))
            except:
                pass
            
            LOGS.info(f">> {self.user.name} is online now!")
        
        LOGS.info(">> Booted up HellMusic!")

    async def logit(self, hash: str, log: str, file: str = None):
        log_text = f"#{hash.upper()} \n\n{log}"
        try:
            if file:
                await self.app.send_file(
                    Config.LOGGER_ID, file, caption=log_text
                )
            else:
                await self.app.send_message(
                    Config.LOGGER_ID, log_text, link_preview=False
                )
        except Exception as e:
            raise HellBotException(f"[HellBotException]: {e}")


hellbot = HellClient()
