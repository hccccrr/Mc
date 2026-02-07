"""
HellMusic V3 - Decorators
Modern permission and authorization decorators
"""

from functools import wraps
from typing import Callable

from pyrogram import Client
from pyrogram.types import Message

from config import Config
from Music.utils.admins import get_auth_users, get_user_rights
from Music.utils.exceptions import HellBotException
from Music.utils.play import player

from .database import db

# Mode keywords
ON_MODE = ["on", "enable", "yes", "true", "1"]


def check_mode(func: Callable) -> Callable:
    """
    Check if private mode is enabled
    Only allow sudo users if private mode is on
    """
    @wraps(func)
    async def decorated(client: Client, message: Message):
        user_id = message.from_user.id
        
        if str(Config.PRIVATE_MODE).lower() in ON_MODE:
            if user_id not in Config.SUDO_USERS:
                return await message.reply_text(
                    "**🔒 Private Mode Enabled**\n\n"
                    "This bot is in private mode and only authorized users can use it."
                )
        
        return await func(client, message)
    
    return decorated


def AdminWrapper(func: Callable) -> Callable:
    """
    Admin-only decorator
    Requires manage voice chats permission
    """
    @wraps(func)
    async def decorated(client: Client, message: Message):
        # Delete command message
        try:
            await message.delete()
        except Exception:
            pass
        
        # Check for anonymous admin
        if message.sender_chat:
            return await message.reply_text(
                "**❌ Anonymous Admin Detected**\n\n"
                "You're an anonymous admin. Please revert to your personal account to use this command."
            )
        
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        # Bypass for sudo users
        if user_id in Config.SUDO_USERS:
            return await func(client, message)
        
        # Check admin rights
        has_rights = await get_user_rights(chat_id, user_id)
        if not has_rights:
            return await message.reply_text(
                "**❌ Insufficient Permissions**\n\n"
                "You need to be an admin with **Manage Voice Chats** permission to use this command."
            )
        
        return await func(client, message)
    
    return decorated


def AuthWrapper(func: Callable) -> Callable:
    """
    Authorized users decorator
    Allows admins and authorized users
    """
    @wraps(func)
    async def decorated(client: Client, message: Message):
        # Delete command message
        try:
            await message.delete()
        except Exception:
            pass
        
        # Check for anonymous admin
        if message.sender_chat:
            return await message.reply_text(
                "**❌ Anonymous Admin Detected**\n\n"
                "You're an anonymous admin. Please revert to your personal account to use this command."
            )
        
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        # Check if VC is active
        if not await db.is_active_vc(chat_id):
            return await message.reply_text(
                "**❌ No Active Stream**\n\n"
                "Nothing is currently playing in the voice chat!"
            )
        
        # Check if authchat is enabled (all users allowed)
        is_authchat = await db.is_authchat(chat_id)
        
        if not is_authchat:
            # Bypass for sudo users
            if user_id in Config.SUDO_USERS:
                return await func(client, message)
            
            # Get authorized users list
            try:
                admins = await get_auth_users(chat_id)
            except Exception as e:
                raise HellBotException(f"[AuthError]: {e}")
            
            if not admins:
                return await message.reply_text(
                    "**⚠️ Admin List Outdated**\n\n"
                    "Need to refresh the admin list.\n"
                    "Use: `/reload`"
                )
            
            if user_id not in admins:
                return await message.reply_text(
                    "**❌ Unauthorized**\n\n"
                    "This command is only for authorized users and admins!"
                )
        
        return await func(client, message)
    
    return decorated


def UserWrapper(func: Callable) -> Callable:
    """
    Normal user decorator
    Allows all users except anonymous admins
    """
    @wraps(func)
    async def decorated(client: Client, message: Message):
        # Delete command message
        try:
            await message.delete()
        except Exception:
            pass
        
        # Check for anonymous admin
        if message.sender_chat:
            return await message.reply_text(
                "**❌ Anonymous Admin Detected**\n\n"
                "You're an anonymous admin. Please revert to your personal account to use this command."
            )
        
        return await func(client, message)
    
    return decorated


def PlayWrapper(func: Callable) -> Callable:
    """
    Play command wrapper
    Validates and prepares playback context
    """
    @wraps(func)
    async def decorated(client: Client, message: Message):
        # Delete command message
        try:
            await message.delete()
        except Exception:
            pass
        
        # Check for anonymous admin
        if message.sender_chat:
            return await message.reply_text(
                "**❌ Anonymous Admin Detected**\n\n"
                "You're an anonymous admin. Please revert to your personal account to use this command."
            )
        
        # Initialize flags
        video = False
        forceplay = False
        url = None
        tg_audio = None
        tg_video = None
        
        # Get URL from message
        url = await player.get_url(message)
        
        # Check for replied media
        if message.reply_to_message:
            tg_audio = (
                message.reply_to_message.audio 
                or message.reply_to_message.voice 
                or None
            )
            tg_video = (
                message.reply_to_message.video
                or message.reply_to_message.document
                or None
            )
        
        # Validate input
        if not tg_audio and not tg_video and not url:
            if len(message.command) < 2:
                return await message.reply_text(
                    "**❌ Invalid Input**\n\n"
                    "**Usage:**\n"
                    "• Reply to an audio/video file\n"
                    "• Provide a YouTube link\n"
                    "• Search with a query\n\n"
                    "**Examples:**\n"
                    "`/play Faded`\n"
                    "`/vplay Despacito`"
                )
        
        # Parse command flags
        command = message.command[0].lower()
        
        if command.startswith("v"):  # vplay, vfplay
            video = True
        
        if command.startswith("f"):  # fplay, fvplay
            forceplay = True
            if len(command) > 1 and command[1] == "v":
                video = True
        
        # Video file forces video mode
        if tg_video:
            video = True
        
        # Create context dictionary
        context = {
            "is_video": video,
            "is_force": forceplay,
            "is_url": url,
            "is_tgaudio": tg_audio,
            "is_tgvideo": tg_video,
        }
        
        return await func(client, message, context)
    
    return decorated


def SudoWrapper(func: Callable) -> Callable:
    """
    Sudo-only decorator
    Only allows sudo users
    """
    @wraps(func)
    async def decorated(client: Client, message: Message):
        user_id = message.from_user.id
        
        if user_id not in Config.SUDO_USERS:
            return await message.reply_text(
                "**❌ Unauthorized**\n\n"
                "This command is only for sudo users!"
            )
        
        return await func(client, message)
    
    return decorated


def OwnerWrapper(func: Callable) -> Callable:
    """
    Owner-only decorator
    Only allows owner users
    """
    @wraps(func)
    async def decorated(client: Client, message: Message):
        user_id = message.from_user.id
        
        if user_id not in Config.GOD_USERS:
            return await message.reply_text(
                "**❌ Unauthorized**\n\n"
                "This command is only for the bot owner!"
            )
        
        return await func(client, message)
    
    return decorated
