import os
import importlib
from pathlib import Path

from telethon import TelegramClient, events
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
        ).start(bot_token=Config.BOT_TOKEN)
        
        # User client with session string
        if Config.STRING_SESSION:
            self.user = TelegramClient(
                StringSession(Config.STRING_SESSION),
                api_id=Config.API_ID,
                api_hash=Config.API_HASH,
            )
        else:
            self.user = None
        
        self._plugins_loaded = False

    async def start(self):
        """Start both bot and user clients"""
        LOGS.info(">> Booting up HellMusic...")
        
        # Start bot client
        if Config.BOT_TOKEN:
            await self.app.connect()
            if not await self.app.is_user_authorized():
                await self.app.start(bot_token=Config.BOT_TOKEN)
            
            me = await self.app.get_me()
            self.app.id = me.id
            self.app.mention = f"[{me.first_name}](tg://user?id={me.id})"
            self.app.name = me.first_name
            self.app.username = me.username
            LOGS.info(f">> {self.app.name} is online now!")
        
        # Start user client
        if Config.STRING_SESSION and self.user:
            await self.user.connect()
            if not await self.user.is_user_authorized():
                await self.user.start()
            
            me = await self.user.get_me()
            self.user.id = me.id
            self.user.mention = f"[{me.first_name}](tg://user?id={me.id})"
            self.user.name = me.first_name
            self.user.username = me.username
            
            # Join channels
            try:
                await self.user(JoinChannelRequest("Its_HellBot"))
                await self.user(JoinChannelRequest("https://t.me/joinchat/LUzuM9rrEdIwZTFl"))
            except Exception as e:
                LOGS.warning(f"Failed to join channels: {e}")
            
            LOGS.info(f">> {self.user.name} is online now!")
        
        # Load plugins after clients are initialized (to avoid circular imports)
        if not self._plugins_loaded:
            self._load_plugins("Music/plugins")
            self._plugins_loaded = True
        
        LOGS.info(">> Booted up HellMusic!")

    async def stop(self):
        """Stop both clients gracefully"""
        if self.app:
            await self.app.disconnect()
            LOGS.info(">> Bot client disconnected!")
        
        if self.user:
            await self.user.disconnect()
            LOGS.info(">> User client disconnected!")

    async def logit(self, hash: str, log: str, file: str = None):
        """Send logs to logger channel"""
        log_text = f"#{hash.upper()}\n\n{log}"
        try:
            if file:
                await self.app.send_file(
                    Config.LOGGER_ID,
                    file,
                    caption=log_text
                )
            else:
                await self.app.send_message(
                    Config.LOGGER_ID,
                    log_text,
                    link_preview=False
                )
        except Exception as e:
            raise HellBotException(f"[HellBotException]: {e}")

    def _load_plugins(self, plugin_path: str):
        """Load all plugins from the specified directory"""
        # Convert to absolute path
        plugin_dir = Path(plugin_path).resolve()
        
        if not plugin_dir.exists():
            LOGS.warning(f"Plugin directory not found: {plugin_path}")
            return
        
        plugin_count = 0
        for path in plugin_dir.rglob("*.py"):
            if path.name.startswith("_"):
                continue
            
            # Convert path to module format
            try:
                # Get relative path from current working directory
                rel_path = path.resolve().relative_to(Path.cwd().resolve())
                module_path = str(rel_path).replace("/", ".").replace("\\", ".")[:-3]
            except ValueError:
                # If relative_to fails, construct module path differently
                module_path = plugin_path.replace("/", ".").replace("\\", ".") + "." + path.stem
            
            try:
                importlib.import_module(module_path)
                plugin_count += 1
                LOGS.debug(f"Loaded plugin: {module_path}")
            except Exception as e:
                LOGS.error(f"Failed to load plugin {module_path}: {e}")
        
        LOGS.info(f">> Loaded {plugin_count} plugins successfully!")


# Global instance
hellbot = HellClient()
