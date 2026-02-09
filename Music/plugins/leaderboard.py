from pyrogram import filters
from pyrogram.types import Message

from config import Config
from Music.core.clients import hellbot
from Music.core.database import db
from Music.core.logger import LOGS


@hellbot.app.on_message(filters.group, group=1)
async def track_user_messages(_, message: Message):
    """
    Track all user messages in groups with anti-spam protection
    """
    # Skip if message is from bot or channel
    if not message.from_user:
        return
    
    # Skip if user is banned
    if message.from_user.id in Config.BANNED_USERS:
        return
    
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    try:
        # Track message with anti-spam check
        is_counted = await db.track_message(user_id, user_name)
        
        if not is_counted:
            # User is in spam cooldown
            cooldown = await db.get_spam_cooldown(user_id)
            if cooldown:
                minutes = int(cooldown.total_seconds() // 60)
                seconds = int(cooldown.total_seconds() % 60)
                
                # Only warn once when cooldown starts (when seconds > 19*60)
                if cooldown.total_seconds() > 19 * 60:
                    try:
                        await message.reply_text(
                            f"⚠️ **Anti-Spam Alert!**\n\n"
                            f"You sent too many messages too quickly.\n"
                            f"Your messages won't be counted for: **{minutes}m {seconds}s**\n\n"
                            f"💡 Please slow down!",
                            quote=True
                        )
                    except:
                        pass
    except Exception as e:
        LOGS.error(f"Error tracking message: {e}")
    
    # Continue propagation to other handlers
    await message.continue_propagation()


@hellbot.app.on_message(
    filters.command(["msgcount", "messagecount"]) & filters.group & ~Config.BANNED_USERS
)
async def check_message_count(_, message: Message):
    """Check user's message count"""
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    
    if not user:
        return await message.reply_text(
            "❌ You are not registered in the database yet!\n"
            "Send some messages to get started."
        )
    
    msg_count = user.get("messages_count", 0)
    songs_count = user.get("songs_played", 0)
    join_date = user.get("join_date", "Unknown")
    
    # Check if in cooldown
    cooldown = await db.get_spam_cooldown(user_id)
    cooldown_text = ""
    if cooldown:
        minutes = int(cooldown.total_seconds() // 60)
        seconds = int(cooldown.total_seconds() % 60)
        cooldown_text = f"\n\n⚠️ **Spam Cooldown:** {minutes}m {seconds}s remaining"
    
    await message.reply_text(
        f"📊 **Your Statistics**\n\n"
        f"👤 **User:** {message.from_user.mention}\n"
        f"💬 **Messages:** `{msg_count}`\n"
        f"🎵 **Songs Played:** `{songs_count}`\n"
        f"📅 **Joined:** `{join_date}`"
        f"{cooldown_text}"
    )


@hellbot.app.on_message(
    filters.command(["resetspam", "clearspam"]) & Config.SUDO_USERS
)
async def reset_spam_cooldown(_, message: Message):
    """Reset spam cooldown for a user (Sudo only)"""
    if not message.reply_to_message:
        return await message.reply_text(
            "❌ Reply to a user's message to reset their spam cooldown!"
        )
    
    user_id = message.reply_to_message.from_user.id
    user_name = message.reply_to_message.from_user.first_name
    
    # Reset cooldown
    await db.users.update_one(
        {"user_id": user_id},
        {"$set": {
            "spam_cooldown_until": None,
            "last_msg_time": []
        }}
    )
    
    await message.reply_text(
        f"✅ Spam cooldown reset for {message.reply_to_message.from_user.mention}!"
  )
  
