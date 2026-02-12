from telethon import events

from config import Config
from Music.core.clients import hellbot
from Music.core.database import db
from Music.core.decorators import UserWrapper, check_mode
from Music.helpers.buttons import Buttons
from Music.helpers.formatters import formatter
from Music.helpers.users import MusicUser
from Music.utils.admins import get_user_type
from Music.utils.leaderboard import leaders


@hellbot.app.on(events.NewMessage(pattern=r"^/(me|profile)"))
@check_mode
@UserWrapper
async def user_profile(event):
    if not event.is_group:
        return
    if event.sender_id in Config.BANNED_USERS:
        return
    
    user = await db.get_user(event.sender_id)
    if not user:
        return await event.reply(
            "You are not yet registered on my database. Click on button below to register yourself.",
            buttons=Buttons.start_markup(hellbot.app.me.username)
        )
    
    sender = await event.get_sender()
    mention = f"[{sender.first_name}](tg://user?id={sender.id})"
    
    context = {
        "id": event.sender_id,
        "mention": mention,
        "songs_played": user.get("songs_played", 0),
        "messages_count": user.get("messages_count", 0),
        "join_date": user["join_date"],
        "user_type": await get_user_type(event.chat_id, event.sender_id),
    }
    
    await event.reply(
        MusicUser.get_profile_text(context, f"@{hellbot.app.me.username}"),
        buttons=Buttons.close_markup(),
    )


@hellbot.app.on(events.NewMessage(pattern=r"^/stats"))
@UserWrapper
async def stats(event):
    if event.sender_id not in Config.SUDO_USERS:
        return
    
    hell = await event.reply("Just a sec... fetching stats")
    users = await db.total_users_count()
    chats = await db.total_chats_count()
    gbans = await db.total_gbans_count()
    block = await db.total_block_count()
    songs = await db.total_songs_count()
    actvc = await db.total_actvc_count()
    stats = await formatter.system_stats()
    
    context = {
        1: users,
        2: chats,
        3: gbans,
        4: block,
        5: songs,
        6: actvc,
        7: stats["core"],
        8: stats["cpu"],
        9: stats["disk"],
        10: stats["ram"],
        11: stats["uptime"],
        12: f"@{hellbot.app.me.username}",
    }
    
    await hell.edit(
        MusicUser.get_stats_text(context),
        buttons=Buttons.close_markup(),
    )


@hellbot.app.on(events.NewMessage(pattern=r"^/(leaderboard|topusers)"))
@UserWrapper
async def topusers(event):
    if not event.is_group:
        return
    if event.sender_id in Config.BANNED_USERS:
        return
    
    hell = await event.reply("Just a sec... fetching top users")
    context = {
        "mention": f"@{hellbot.app.me.username}",
        "username": hellbot.app.me.username,
        "client": hellbot.app,
    }
    
    # Show both leaderboards by default
    text = await leaders.generate(context, "both")
    btns = Buttons.close_markup()
    
    await hell.edit(
        text,
        link_preview=False,
        buttons=btns,
    )


@hellbot.app.on(events.NewMessage(pattern=r"^/(topchatters|activechatters)"))
@UserWrapper
async def top_chatters(event):
    if not event.is_group:
        return
    if event.sender_id in Config.BANNED_USERS:
        return
    
    hell = await event.reply("Just a sec... fetching top chatters")
    context = {
        "mention": f"@{hellbot.app.me.username}",
        "username": hellbot.app.me.username,
        "client": hellbot.app,
    }
    
    # Show only message leaderboard
    text = await leaders.generate(context, "messages")
    btns = Buttons.close_markup()
    
    await hell.edit(
        text,
        link_preview=False,
        buttons=btns,
    )


@hellbot.app.on(events.NewMessage(pattern=r"^/(topmusic|topsongs)"))
@UserWrapper
async def top_music(event):
    if not event.is_group:
        return
    if event.sender_id in Config.BANNED_USERS:
        return
    
    hell = await event.reply("Just a sec... fetching top music lovers")
    context = {
        "mention": f"@{hellbot.app.me.username}",
        "username": hellbot.app.me.username,
        "client": hellbot.app,
    }
    
    # Show only songs leaderboard
    text = await leaders.generate(context, "songs")
    btns = Buttons.close_markup()
    
    await hell.edit(
        text,
        link_preview=False,
        buttons=btns,
    )
    
