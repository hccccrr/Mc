from functools import wraps
from typing import Callable

from telethon import events
from telethon.tl.types import Channel, Chat, MessageEntityUrl

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
    async def decorated(event):
        user_id = event.sender_id
        
        if str(Config.PRIVATE_MODE).lower() in ON_MODE:
            if user_id not in Config.SUDO_USERS:
                return await event.reply(
                    "**🔒 Private Mode Enabled**\n\n"
                    "This bot is in private mode and only authorized users can use it."
                )
        
        return await func(event)
    
    return decorated


def AdminWrapper(func: Callable) -> Callable:
    """
    Admin-only decorator
    Requires manage voice chats permission
    """
    @wraps(func)
    async def decorated(event):
        # Delete command message
        try:
            await event.delete()
        except Exception:
            pass
        
        # Check for anonymous admin (sender_id will be channel/chat id)
        try:
            if hasattr(event, 'from_id') and hasattr(event.from_id, 'channel_id'):
                return await event.reply(
                    "**❌ Anonymous Admin Detected**\n\n"
                    "You're an anonymous admin. Please revert to your personal account to use this command."
                )
        except:
            pass
        
        chat_id = event.chat_id
        user_id = event.sender_id
        
        # Bypass for sudo users
        if user_id in Config.SUDO_USERS:
            return await func(event)
        
        # Check admin rights
        has_rights = await get_user_rights(chat_id, user_id)
        if not has_rights:
            return await event.reply(
                "**❌ Insufficient Permissions**\n\n"
                "You need to be an admin with **Manage Voice Chats** permission to use this command."
            )
        
        return await func(event)
    
    return decorated


def AuthWrapper(func: Callable) -> Callable:
    """
    Authorized users decorator
    Allows admins and authorized users
    """
    @wraps(func)
    async def decorated(event):
        # Delete command message
        try:
            await event.delete()
        except Exception:
            pass
        
        # Check for anonymous admin
        try:
            if hasattr(event, 'from_id') and hasattr(event.from_id, 'channel_id'):
                return await event.reply(
                    "**❌ Anonymous Admin Detected**\n\n"
                    "You're an anonymous admin. Please revert to your personal account to use this command."
                )
        except:
            pass
        
        chat_id = event.chat_id
        user_id = event.sender_id
        
        # Check if VC is active
        if not await db.is_active_vc(chat_id):
            return await event.reply(
                "**❌ No Active Stream**\n\n"
                "Nothing is currently playing in the voice chat!"
            )
        
        # Check if authchat is enabled (all users allowed)
        is_authchat = await db.is_authchat(chat_id)
        
        if not is_authchat:
            # Bypass for sudo users
            if user_id in Config.SUDO_USERS:
                return await func(event)
            
            # Get authorized users list
            try:
                admins = await get_auth_users(chat_id)
            except Exception as e:
                raise HellBotException(f"[AuthError]: {e}")
            
            if not admins:
                return await event.reply(
                    "**⚠️ Admin List Outdated**\n\n"
                    "Need to refresh the admin list.\n"
                    "Use: `/reload`"
                )
            
            if user_id not in admins:
                return await event.reply(
                    "**❌ Unauthorized**\n\n"
                    "This command is only for authorized users and admins!"
                )
        
        return await func(event)
    
    return decorated


def UserWrapper(func: Callable) -> Callable:
    """
    Normal user decorator
    Allows all users except anonymous admins
    """
    @wraps(func)
    async def decorated(event):
        # Delete command message
        try:
            await event.delete()
        except Exception:
            pass
        
        # Check for anonymous admin
        try:
            if hasattr(event, 'from_id') and hasattr(event.from_id, 'channel_id'):
                return await event.reply(
                    "**❌ Anonymous Admin Detected**\n\n"
                    "You're an anonymous admin. Please revert to your personal account to use this command."
                )
        except:
            pass
        
        return await func(event)
    
    return decorated


def PlayWrapper(func: Callable) -> Callable:
    """
    Play command wrapper
    Validates and prepares playback context
    """
    @wraps(func)
    async def decorated(event):
        # Delete command message
        try:
            await event.delete()
        except Exception:
            pass
        
        # Check for anonymous admin
        try:
            if hasattr(event, 'from_id') and hasattr(event.from_id, 'channel_id'):
                return await event.reply(
                    "**❌ Anonymous Admin Detected**\n\n"
                    "You're an anonymous admin. Please revert to your personal account to use this command."
                )
        except:
            pass
        
        # Initialize flags
        video = False
        forceplay = False
        url = None
        tg_audio = None
        tg_video = None
        
        # Get URL from message using player utility
        try:
            url = await player.get_url(event)
        except:
            # Fallback: Extract URL manually
            if event.entities:
                for entity in event.entities:
                    if isinstance(entity, MessageEntityUrl):
                        url = event.text[entity.offset:entity.offset + entity.length]
                        break
            
            # Check text for URL
            if not url and event.text:
                parts = event.text.split()
                for part in parts[1:]:
                    if "youtube.com" in part or "youtu.be" in part:
                        url = part
                        break
        
        # Check for replied media
        replied_msg = await event.get_reply_message()
        if replied_msg:
            # Check for audio/voice
            if replied_msg.audio:
                tg_audio = replied_msg.audio
            elif replied_msg.voice:
                tg_audio = replied_msg.voice
            
            # Check for video
            if replied_msg.video:
                tg_video = replied_msg.video
            elif replied_msg.document:
                # Check if document is a video
                if replied_msg.document.mime_type and replied_msg.document.mime_type.startswith("video/"):
                    tg_video = replied_msg.document
        
        # Validate input
        if not tg_audio and not tg_video and not url:
            # Get command from message text
            cmd_parts = event.text.split() if event.text else []
            if len(cmd_parts) < 2:
                return await event.reply(
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
        cmd_parts = event.text.split() if event.text else []
        command = cmd_parts[0].lower().replace("/", "") if cmd_parts else ""
        
        # Store command in event object for later use
        event.command = cmd_parts
        
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
        
        return await func(event, context)
    
    return decorated


def SudoWrapper(func: Callable) -> Callable:
    """
    Sudo-only decorator
    Only allows sudo users
    """
    @wraps(func)
    async def decorated(event):
        user_id = event.sender_id
        
        if user_id not in Config.SUDO_USERS:
            return await event.reply(
                "**❌ Unauthorized**\n\n"
                "This command is only for sudo users!"
            )
        
        return await func(event)
    
    return decorated


def OwnerWrapper(func: Callable) -> Callable:
    """
    Owner-only decorator
    Only allows owner users
    """
    @wraps(func)
    async def decorated(event):
        user_id = event.sender_id
        
        if user_id not in Config.GOD_USERS:
            return await event.reply(
                "**❌ Unauthorized**\n\n"
                "This command is only for the bot owner!"
            )
        
        return await func(event)
    
    return decorated
