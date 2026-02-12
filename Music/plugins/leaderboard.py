from telethon import events

from config import Config
from Music.core.clients import hellbot
from Music.core.database import db
from Music.core.logger import LOGS


@hellbot.app.on(events.NewMessage)
async def track_user_messages(event):
    """Track all user messages in groups with anti-spam protection"""
    # Skip if not group
    if not event.is_group:
        return
    
    # Skip if message is from channel
    if not event.sender_id:
        return
    
    # Skip if user is banned
    if event.sender_id in Config.BANNED_USERS:
        return
    
    user_id = event.sender_id
    
    try:
        sender = await event.get_sender()
        user_name = sender.first_name
        
        # Track message with anti-spam check
        is_counted = await db.track_message(user_id, user_name)
        
        if not is_counted:
            # User is in spam cooldown
            cooldown = await db.get_spam_cooldown(user_id)
            if cooldown:
                minutes = int(cooldown.total_seconds() // 60)
                seconds = int(cooldown.total_seconds() % 60)
                
                # Only warn once when cooldown starts
                if cooldown.total_seconds() > 19 * 60:
                    try:
                        await event.reply(
                            f"⚠️ **Anti-Spam Alert!**\n\n"
                            f"You sent too many messages too quickly.\n"
                            f"Your messages won't be counted for: **{minutes}m {seconds}s**\n\n"
                            f"💡 Please slow down!"
                        )
                    except:
                        pass
    except Exception as e:
        LOGS.error(f"Error tracking message: {e}")


@hellbot.app.on(events.NewMessage(pattern=r"^/(msgcount|messagecount)"))
async def check_message_count(event):
    """Check user's message count"""
    if not event.is_group:
        return
    if event.sender_id in Config.BANNED_USERS:
        return
    
    user_id = event.sender_id
    user = await db.get_user(user_id)
    
    if not user:
        return await event.reply(
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
    
    sender = await event.get_sender()
    mention = f"[{sender.first_name}](tg://user?id={sender.id})"
    
    await event.reply(
        f"📊 **Your Statistics**\n\n"
        f"👤 **User:** {mention}\n"
        f"💬 **Messages:** `{msg_count}`\n"
        f"🎵 **Songs Played:** `{songs_count}`\n"
        f"📅 **Joined:** `{join_date}`"
        f"{cooldown_text}"
    )


@hellbot.app.on(events.NewMessage(pattern=r"^/(resetspam|clearspam)"))
async def reset_spam_cooldown(event):
    """Reset spam cooldown for a user (Sudo only)"""
    if event.sender_id not in Config.SUDO_USERS:
        return
    
    if not event.is_reply:
        return await event.reply(
            "❌ Reply to a user's message to reset their spam cooldown!"
        )
    
    replied = await event.get_reply_message()
    user_id = replied.sender_id
    sender = await replied.get_sender()
    user_name = sender.first_name
    
    # Reset cooldown
    await db.users.update_one(
        {"user_id": user_id},
        {"$set": {
            "spam_cooldown_until": None,
            "last_msg_time": []
        }}
    )
    
    mention = f"[{user_name}](tg://user?id={user_id})"
    await event.reply(
        f"✅ Spam cooldown reset for {mention}!"
    )
