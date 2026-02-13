from telethon import events

from config import Config
from Music.core.calls import hellmusic
from Music.core.clients import hellbot
from Music.core.database import db
from Music.core.decorators import AuthWrapper, check_mode
from Music.helpers.formatters import formatter
from Music.utils.play import player
from Music.utils.queue import Queue
from Music.utils.youtube import ytube


@hellbot.app.on(events.NewMessage(pattern=r"^/(mute|unmute)"))
@check_mode
@AuthWrapper
async def mute_unmute(event):
    if not event.is_group:
        return
    if event.sender_id in Config.BANNED_USERS:
        return
    
    cmd = event.text.split()[0]
    is_muted = await db.get_watcher(event.chat_id, "mute")
    sender = await event.get_sender()
    mention = f"[{sender.first_name}](tg://user?id={sender.id})"
    
    if cmd == "/unmute":
        if is_muted:
            await db.set_watcher(event.chat_id, "mute", False)
            await hellmusic.unmute_vc(event.chat_id)
            return await event.reply(f"__VC Unmuted by:__ {mention}")
        else:
            return await event.reply("Voice Chat is not muted!")
    else:
        if is_muted:
            return await event.reply("Voice Chat is already muted!")
        else:
            await db.set_watcher(event.chat_id, "mute", True)
            await hellmusic.mute_vc(event.chat_id)
            return await event.reply(f"__VC Muted by:__ {mention}")


@hellbot.app.on(events.NewMessage(pattern=r"^/(pause|resume)"))
@check_mode
@AuthWrapper
async def pause_resume(event):
    if not event.is_group:
        return
    if event.sender_id in Config.BANNED_USERS:
        return
    
    cmd = event.text.split()[0]
    is_paused = await db.get_watcher(event.chat_id, "pause")
    sender = await event.get_sender()
    mention = f"[{sender.first_name}](tg://user?id={sender.id})"
    
    if cmd == "/resume":
        if is_paused:
            await db.set_watcher(event.chat_id, "pause", False)
            await hellmusic.resume_vc(event.chat_id)
            return await event.reply(f"__VC Resumed by:__ {mention}")
        else:
            return await event.reply("Voice Chat is not paused!")
    else:
        if is_paused:
            return await event.reply("Voice Chat is already paused!")
        else:
            await db.set_watcher(event.chat_id, "pause", True)
            await hellmusic.pause_vc(event.chat_id)
            return await event.reply(f"__VC Paused by:__ {mention}")


@hellbot.app.on(events.NewMessage(pattern=r"^/(stop|end)"))
@check_mode
@AuthWrapper
async def stop_end(event):
    if not event.is_group:
        return
    if event.sender_id in Config.BANNED_USERS:
        return
    
    await hellmusic.leave_vc(event.chat_id)
    await db.set_loop(event.chat_id, 0)
    sender = await event.get_sender()
    mention = f"[{sender.first_name}](tg://user?id={sender.id})"
    await event.reply(f"__VC Stopped by:__ {mention}")


@hellbot.app.on(events.NewMessage(pattern=r"^/loop"))
@check_mode
@AuthWrapper
async def loop(event):
    if not event.is_group:
        return
    if event.sender_id in Config.BANNED_USERS:
        return
    
    parts = event.text.split()
    if len(parts) < 2:
        return await event.reply(
            "Please specify the number of times to loop the song! \n\nMaximum loop range is **10**. Give **0** to disable loop."
        )
    
    try:
        loop = int(parts[1])
    except Exception:
        return await event.reply(
            "Please enter a valid number! \n\nMaximum loop range is **10**. Give **0** to disable loop."
        )
    
    is_loop = await db.get_loop(event.chat_id)
    sender = await event.get_sender()
    mention = f"[{sender.first_name}](tg://user?id={sender.id})"
    
    if loop == 0:
        if is_loop == 0:
            return await event.reply("There is no active loop in this chat!")
        await db.set_loop(event.chat_id, 0)
        return await event.reply(
            f"__Loop disabled by:__ {mention}\n\nPrevious loop was: `{is_loop}`"
        )
    
    if 1 <= loop <= 10:
        final = is_loop + loop
        final = 10 if final > 10 else final
        await db.set_loop(event.chat_id, final)
        await event.reply(
            f"__Loop set to:__ `{final}`\n__By:__ {mention} \n\nPrevious loop was: `{is_loop}`"
        )
    else:
        return await event.reply(
            "Please enter a valid number! \n\nMaximum loop range is **10**. Give **0** to disable loop."
        )


@hellbot.app.on(events.NewMessage(pattern=r"^/replay"))
@check_mode
@AuthWrapper
async def replay(event):
    if not event.is_group:
        return
    if event.sender_id in Config.BANNED_USERS:
        return
    
    is_active = await db.is_active_vc(event.chat_id)
    if not is_active:
        return await event.reply("No active Voice Chat found here!")
    
    hell = await event.reply("Replaying...")
    que = Queue.get_queue(event.chat_id)
    if que == []:
        return await hell.edit("No songs in the queue to replay!")
    await player.replay(event.chat_id, hell)


@hellbot.app.on(events.NewMessage(pattern=r"^/skip"))
@check_mode
@AuthWrapper
async def skip(event):
    if not event.is_group:
        return
    if event.sender_id in Config.BANNED_USERS:
        return
    
    is_active = await db.is_active_vc(event.chat_id)
    if not is_active:
        return await event.reply("No active Voice Chat found here!")
    
    hell = await event.reply("Processing ...")
    que = Queue.get_queue(event.chat_id)
    if que == []:
        return await hell.edit("No songs in the queue to skip!")
    if len(que) == 1:
        return await hell.edit(
            "No more songs in queue to skip! Use /end or /stop to stop the VC."
        )
    
    is_loop = await db.get_loop(event.chat_id)
    if is_loop != 0:
        await hell.edit("Disabled Loop to skip the current song!")
        await db.set_loop(event.chat_id, 0)
    await player.skip(event.chat_id, hell)


@hellbot.app.on(events.NewMessage(pattern=r"^/seek"))
@check_mode
@AuthWrapper
async def seek(event):
    if not event.is_group:
        return
    if event.sender_id in Config.BANNED_USERS:
        return
    
    is_active = await db.is_active_vc(event.chat_id)
    if not is_active:
        return await event.reply("No active Voice Chat found here!")
    
    parts = event.text.split()
    if len(parts) < 2:
        return await event.reply(
            "Please specify the time to seek! \n\n**Example:** \n__- Seek  10 secs forward >__ `/seek 10`. \n__- Seek  10 secs backward >__ `/seek -10`."
        )
    
    hell = await event.reply("Seeking...")
    try:
        if parts[1][0] == "-":
            seek_time = int(parts[1][1:])
            seek_type = 0
        else:
            seek_time = int(parts[1])
            seek_type = 1
    except:
        return await hell.edit("Please enter numeric characters only!")
    
    que = Queue.get_queue(event.chat_id)
    if que == []:
        return await hell.edit("No songs in the queue to seek!")
    
    played = int(que[0]["played"])
    duration = formatter.mins_to_secs(que[0]["duration"])
    
    if seek_type == 0:
        if (played - seek_time) <= 10:
            return await hell.edit(
                "Cannot seek when only 10 seconds are left! Use a lesser value."
            )
        to_seek = played - seek_time
    else:
        if (duration - (played + seek_time)) <= 10:
            return await hell.edit(
                "Cannot seek when only 10 seconds are left! Use a lesser value."
            )
        to_seek = played + seek_time
    
    video = True if que[0]["vc_type"] == "video" else False
    if que[0]["file"] == que[0]["video_id"]:
        file_path = await ytube.download(que[0]["video_id"], True, video)
    else:
        file_path = que[0]["file"]
    
    try:
        context = {
            "chat_id": que[0]["chat_id"],
            "file": file_path,
            "duration": que[0]["duration"],
            "seek": formatter.secs_to_mins(to_seek),
            "video": video,
        }
        await hellmusic.seek_vc(context)
    except:
        return await hell.edit("Something went wrong!")
    
    Queue.update_duration(event.chat_id, seek_type, seek_time)
    await hell.edit(
        f"Seeked `{seek_time}` seconds {'forward' if seek_type == 1 else 'backward'}!"
    )

