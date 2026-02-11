import datetime

from telethon import events

from config import Config
from Music.core.calls import hellmusic
from Music.core.clients import hellbot
from Music.core.database import db
from Music.core.decorators import UserWrapper, check_mode
from Music.helpers.buttons import Buttons
from Music.helpers.formatters import formatter
from Music.helpers.strings import TEXTS
from Music.helpers.users import MusicUser
from Music.utils.youtube import ytube


@hellbot.app.on(events.NewMessage(pattern=r"^/(start|alive)"))
@check_mode
async def start(event):
    if event.sender_id in Config.BANNED_USERS:
        return
    
    if event.is_private:
        parts = event.text.split()
        if len(parts) > 1:
            deep_cmd = parts[1]
            
            if deep_cmd.startswith("song"):
                results = await ytube.get_data(deep_cmd.split("_", 1)[1], True)
                about = TEXTS.ABOUT_SONG.format(
                    results[0]["title"],
                    results[0]["channel"],
                    results[0]["published"],
                    results[0]["views"],
                    results[0]["duration"],
                    f"@{hellbot.app.me.username}",
                )
                await event.reply(
                    about,
                    file=results[0]["thumbnail"],
                    buttons=Buttons.song_details_markup(
                        results[0]["link"],
                        results[0]["ch_link"],
                    )
                )
                return
            
            elif deep_cmd.startswith("user"):
                userid = int(deep_cmd.split("_", 1)[1])
                userdbs = await db.get_user(userid)
                songs = userdbs["songs_played"]
                level = MusicUser.get_user_level(int(songs))
                to_send = TEXTS.ABOUT_USER.format(
                    userdbs["user_name"],
                    userdbs["user_id"],
                    level,
                    songs,
                    userdbs["join_date"],
                    f"@{hellbot.app.me.username}",
                )
                await event.reply(
                    to_send,
                    buttons=Buttons.close_markup(),
                    link_preview=False,
                )
                return
            
            elif deep_cmd.startswith("help"):
                await event.reply(
                    TEXTS.HELP_PM.format(f"@{hellbot.app.me.username}"),
                    buttons=Buttons.help_pm_markup(),
                )
                return
        
        sender = await event.get_sender()
        await event.reply(
            TEXTS.START_PM.format(
                sender.first_name,
                f"@{hellbot.app.me.username}",
                hellbot.app.me.username,
            ),
            buttons=Buttons.start_pm_markup(hellbot.app.me.username),
            link_preview=False,
        )
    
    elif event.is_group:
        await event.reply(TEXTS.START_GC)


@hellbot.app.on(events.NewMessage(pattern=r"^/help"))
async def help_cmd(event):
    if event.sender_id in Config.BANNED_USERS:
        return
    
    if event.is_private:
        await event.reply(
            TEXTS.HELP_PM.format(f"@{hellbot.app.me.username}"),
            buttons=Buttons.help_pm_markup(),
        )
    elif event.is_group:
        await event.reply(
            TEXTS.HELP_GC,
            buttons=Buttons.help_gc_markup(hellbot.app.me.username)
        )


@hellbot.app.on(events.NewMessage(pattern=r"^/ping"))
async def ping(event):
    if event.sender_id in Config.BANNED_USERS:
        return
    
    start_time = datetime.datetime.now()
    hell = await event.reply("Pong!")
    calls_ping = await hellmusic.ping()
    stats = await formatter.system_stats()
    end_time = (datetime.datetime.now() - start_time).microseconds / 1000
    
    await hell.edit(
        TEXTS.PING_REPLY.format(end_time, stats["uptime"], calls_ping),
        link_preview=False,
        buttons=Buttons.close_markup(),
    )


@hellbot.app.on(events.NewMessage(pattern=r"^/sysinfo"))
@check_mode
@UserWrapper
async def sysinfo(event):
    if event.sender_id in Config.BANNED_USERS:
        return
    
    stats = await formatter.system_stats()
    await event.reply(
        TEXTS.SYSTEM.format(
            stats["core"],
            stats["cpu"],
            stats["disk"],
            stats["ram"],
            stats["uptime"],
            f"@{hellbot.app.me.username}",
        ),
        buttons=Buttons.close_markup(),
)
    
