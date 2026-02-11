from telethon import events

from config import Config
from Music.core.calls import hellmusic
from Music.core.clients import hellbot
from Music.core.database import db
from Music.helpers.buttons import Buttons
from Music.helpers.formatters import formatter
from Music.helpers.strings import TEXTS
from Music.utils.admins import get_auth_users
from Music.utils.play import player
from Music.utils.queue import Queue
from Music.utils.youtube import ytube


@hellbot.app.on(events.CallbackQuery(pattern=b"close"))
async def close_cb(event):
    if event.sender_id in Config.BANNED_USERS:
        return
    try:
        await event.delete()
        await event.answer("Closed!", alert=True)
    except:
        pass


@hellbot.app.on(events.CallbackQuery(pattern=b"controls"))
async def controls_cb(event):
    if event.sender_id in Config.BANNED_USERS:
        return
    
    data = event.data.decode().split("|")
    video_id = data[1]
    chat_id = int(data[2])
    btns = Buttons.controls_markup(video_id, chat_id)
    
    try:
        await event.edit(buttons=btns)
    except:
        return


@hellbot.app.on(events.CallbackQuery(pattern=b"player"))
async def player_cb(event):
    if event.sender_id in Config.BANNED_USERS:
        return
    
    data = event.data.decode().split("|")
    _, video_id, chat_id = data
    btns = Buttons.player_markup(chat_id, video_id, hellbot.app.me.username)
    
    try:
        await event.edit(buttons=btns)
    except:
        return


@hellbot.app.on(events.CallbackQuery(pattern=b"ctrl"))
async def controler_cb(event):
    if event.sender_id in Config.BANNED_USERS:
        return
    
    data = event.data.decode().split("|")
    _, action, chat_id = data
    chat_id = int(chat_id)
    
    if chat_id != event.chat_id:
        return await event.answer("This message is not for this chat!", alert=True)
    
    is_active = await db.is_active_vc(chat_id)
    if not is_active:
        return await event.answer("Voice chat is not active!", alert=True)
    
    is_authchat = await db.is_authchat(event.chat_id)
    if not is_authchat:
        if event.sender_id not in Config.SUDO_USERS:
            try:
                admins = await get_auth_users(chat_id)
            except Exception as e:
                return await event.answer(
                    f"There was an error while fetching admin list.\n\n{e}",
                    alert=True,
                )
            if not admins:
                return await event.answer("Need to refresh admin list.", alert=True)
            else:
                if event.sender_id not in admins:
                    return await event.answer(
                        "This command is only for authorized users and admins!",
                        alert=True,
                    )
    
    sender = await event.get_sender()
    mention = f"[{sender.first_name}](tg://user?id={sender.id})"
    
    if action == "play":
        is_paused = await db.get_watcher(event.chat_id, "pause")
        if is_paused:
            await db.set_watcher(event.chat_id, "pause", False)
            await hellmusic.resume_vc(event.chat_id)
            await event.answer("Resumed!", alert=True)
            return await event.respond(f"__VC Resumed by:__ {mention}")
        else:
            await db.set_watcher(event.chat_id, "pause", True)
            await hellmusic.pause_vc(event.chat_id)
            await event.answer("Paused!", alert=True)
            return await event.respond(f"__VC Paused by:__ {mention}")
    
    elif action == "mute":
        is_muted = await db.get_watcher(event.chat_id, "mute")
        if is_muted:
            return await event.answer("Already muted!", alert=True)
        else:
            await db.set_watcher(event.chat_id, "mute", True)
            await hellmusic.mute_vc(event.chat_id)
            await event.answer("Muted!", alert=True)
            return await event.respond(f"__VC Muted by:__ {mention}")
    
    elif action == "unmute":
        is_muted = await db.get_watcher(event.chat_id, "mute")
        if is_muted:
            await db.set_watcher(event.chat_id, "mute", False)
            await hellmusic.unmute_vc(event.chat_id)
            await event.answer("Unmuted!", alert=True)
            return await event.respond(f"__VC Unmuted by:__ {mention}")
        else:
            return await event.answer("Already unmuted!", alert=True)
    
    elif action == "end":
        await hellmusic.leave_vc(event.chat_id)
        await db.set_loop(event.chat_id, 0)
        await event.answer("Left the VC!", alert=True)
        return await event.respond(f"__VC Stopped by:__ {mention}")
    
    elif action == "loop":
        is_loop = await db.get_loop(event.chat_id)
        final = is_loop + 3
        final = 10 if final > 10 else final
        await db.set_loop(event.chat_id, final)
        await event.answer(f"Loop set to {final}", alert=True)
        return await event.respond(
            f"__Loop set to {final}__ by: {mention}\n\nPrevious loop was {is_loop}"
        )
    
    elif action == "replay":
        hell = await event.respond("Processing ...")
        que = Queue.get_queue(event.chat_id)
        if que == []:
            await hell.delete()
            return await event.answer("No songs in queue to replay!", alert=True)
        await event.answer("Replaying!", alert=True)
        await player.replay(event.chat_id, hell)
    
    elif action == "skip":
        hell = await event.respond("Processing ...")
        que = Queue.get_queue(event.chat_id)
        if que == []:
            await hell.delete()
            return await event.answer("No songs in queue to skip!", alert=True)
        if len(que) == 1:
            await hell.delete()
            return await event.answer(
                "No more songs in queue to skip! Use /end or /stop to stop the VC.",
                alert=True,
            )
        is_loop = await db.get_loop(event.chat_id)
        if is_loop != 0:
            await db.set_loop(event.chat_id, 0)
        await player.skip(event.chat_id, hell)
    
    elif action == "bass":
        effects = await db.get_audio_effects(event.chat_id)
        current_bass = effects.get("bass_boost", 0)
        
        if current_bass == 0:
            new_bass = 3
        elif current_bass == 3:
            new_bass = 6
        elif current_bass == 6:
            new_bass = 10
        else:
            new_bass = 0
        
        speed = effects.get("speed", 1.0)
        success = await hellmusic.apply_effects(event.chat_id, new_bass, speed)
        
        if success:
            bass_label = "Off" if new_bass == 0 else f"+{new_bass} dB"
            await event.answer(f"Bass Boost: {bass_label}", alert=True)
            await event.respond(f"**🎸 Bass Boost: {bass_label}**\nBy: {mention}")
        else:
            await event.answer("Failed to apply bass boost!", alert=True)
    
    elif action == "speed":
        effects = await db.get_audio_effects(event.chat_id)
        current_speed = effects.get("speed", 1.0)
        
        if current_speed == 1.0:
            new_speed = 1.25
        elif current_speed == 1.25:
            new_speed = 1.5
        elif current_speed == 1.5:
            new_speed = 0.75
        elif current_speed == 0.75:
            new_speed = 0.5
        else:
            new_speed = 1.0
        
        bass = effects.get("bass_boost", 0)
        success = await hellmusic.apply_effects(event.chat_id, bass, new_speed)
        
        if success:
            speed_label = f"{new_speed}x"
            await event.answer(f"Speed: {speed_label}", alert=True)
            await event.respond(f"**⚡ Speed: {speed_label}**\nBy: {mention}")
        else:
            await event.answer("Failed to apply speed change!", alert=True)


@hellbot.app.on(events.CallbackQuery(pattern=b"help"))
async def help_cb(event):
    if event.sender_id in Config.BANNED_USERS:
        return
    
    data = event.data.decode().split("|")[1]
    
    if data == "admin":
        return await event.edit(
            TEXTS.HELP_ADMIN, 
            buttons=Buttons.help_back()
        )
    elif data == "user":
        return await event.edit(
            TEXTS.HELP_USER, 
            buttons=Buttons.help_back()
        )
    elif data == "sudo":
        return await event.edit(
            TEXTS.HELP_SUDO, 
            buttons=Buttons.help_back()
        )
    elif data == "others":
        return await event.edit(
            TEXTS.HELP_OTHERS, 
            buttons=Buttons.help_back()
        )
    elif data == "owner":
        return await event.edit(
            TEXTS.HELP_OWNERS, 
            buttons=Buttons.help_back()
        )
    elif data == "back":
        return await event.edit(
            TEXTS.HELP_PM.format(f"@{hellbot.app.me.username}"),
            buttons=Buttons.help_pm_markup(),
        )
    elif data == "start":
        sender = await event.get_sender()
        return await event.edit(
            TEXTS.START_PM.format(
                sender.first_name,
                f"@{hellbot.app.me.username}",
                hellbot.app.me.username,
            ),
            buttons=Buttons.start_pm_markup(hellbot.app.me.username),
            link_preview=False,
        )


@hellbot.app.on(events.CallbackQuery(pattern=b"source"))
async def source_cb(event):
    if event.sender_id in Config.BANNED_USERS:
        return
    
    await event.edit(
        TEXTS.SOURCE.format(f"@{hellbot.app.me.username}"),
        buttons=Buttons.source_markup(),
        link_preview=False,
    )
    
