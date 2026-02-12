import asyncio
import random

from telethon import events

from config import Config
from Music.core.clients import hellbot
from Music.core.database import db
from Music.core.decorators import AuthWrapper, PlayWrapper, UserWrapper, check_mode
from Music.helpers.buttons import Buttons
from Music.helpers.formatters import formatter
from Music.helpers.strings import TEXTS
from Music.utils.pages import MakePages
from Music.utils.play import player
from Music.utils.queue import Queue
from Music.utils.thumbnail import thumb
from Music.utils.youtube import ytube


@hellbot.app.on(events.NewMessage(pattern=r"^/(play|vplay|fplay|fvplay)(?:\s|$)"))
@check_mode
@PlayWrapper
async def play_music(event, context: dict):
    """Handle play commands"""
    # Check group and banned
    if not event.is_group:
        return
    if event.sender_id in Config.BANNED_USERS:
        return
    
    sender = await event.get_sender()
    user_name = sender.first_name
    user_id = event.sender_id
    
    # Add/update user in database
    if not await db.is_user_exist(user_id):
        await db.add_user(user_id, user_name)
    else:
        try:
            await db.update_user(user_id, "user_name", user_name)
        except:
            pass
    
    hell = await event.reply("Processing ...")
    
    # Get context from decorator
    video = context["video"]
    force = context["force"]
    url = context["url"]
    tgaud = context["tgaud"]
    tgvid = context["tgvid"]
    
    play_limit = formatter.mins_to_secs(f"{Config.PLAY_LIMIT}:00")
    
    # Handle Telegram audio
    if tgaud:
        size_check = formatter.check_limit(tgaud.size, Config.TG_AUDIO_SIZE_LIMIT)
        if not size_check:
            return await hell.edit(
                f"Audio file size exceeds the size limit of {formatter.bytes_to_mb(Config.TG_AUDIO_SIZE_LIMIT)}MB."
            )
        time_check = formatter.check_limit(tgaud.duration, play_limit)
        if not time_check:
            return await hell.edit(
                f"Audio duration limit of {Config.PLAY_LIMIT} minutes exceeded."
            )
        
        await hell.edit("Downloading ...")
        replied = await event.get_reply_message()
        file_path = await hellbot.app.download_media(replied)
        
        mention = f"[{sender.first_name}](tg://user?id={sender.id})"
        play_context = {
            "chat_id": event.chat_id,
            "user_id": event.sender_id,
            "duration": formatter.secs_to_mins(tgaud.duration),
            "file": file_path,
            "title": "Telegram Audio",
            "user": mention,
            "video_id": "telegram",
            "vc_type": "voice",
            "force": force,
        }
        await player.play(hell, play_context)
        return
    
    # Handle Telegram video
    if tgvid:
        size_check = formatter.check_limit(tgvid.size, Config.TG_VIDEO_SIZE_LIMIT)
        if not size_check:
            return await hell.edit(
                f"Video file size exceeds the size limit of {formatter.bytes_to_mb(Config.TG_VIDEO_SIZE_LIMIT)}MB."
            )
        time_check = formatter.check_limit(tgvid.duration, play_limit)
        if not time_check:
            return await hell.edit(
                f"Video duration limit of {Config.PLAY_LIMIT} minutes exceeded."
            )
        
        await hell.edit("Downloading ...")
        replied = await event.get_reply_message()
        file_path = await hellbot.app.download_media(replied)
        
        mention = f"[{sender.first_name}](tg://user?id={sender.id})"
        play_context = {
            "chat_id": event.chat_id,
            "user_id": event.sender_id,
            "duration": formatter.secs_to_mins(tgvid.duration),
            "file": file_path,
            "title": "Telegram Video",
            "user": mention,
            "video_id": "telegram",
            "vc_type": "video",
            "force": force,
        }
        await player.play(hell, play_context)
        return
    
    # Handle YouTube URL
    if url:
        if not ytube.check(url):
            return await hell.edit("Invalid YouTube URL.")
        
        if "playlist" in url:
            await hell.edit("Processing the playlist ...")
            try:
                song_list = await ytube.get_playlist(url)
                if not song_list:
                    return await hell.edit("Failed to fetch playlist or playlist is empty.")
                random.shuffle(song_list)
                
                mention = f"[{sender.first_name}](tg://user?id={sender.id})"
                play_context = {
                    "user_id": event.sender_id,
                    "user_mention": mention,
                }
                await player.playlist(hell, play_context, song_list, video)
            except Exception as e:
                return await hell.edit(f"**Error fetching playlist:**\n`{e}`")
            return
        
        try:
            await hell.edit("Searching ...")
            result = await ytube.get_data(url, False)
            if not result or len(result) == 0:
                return await hell.edit("No results found. Please try again with a different URL or query.")
        except Exception as e:
            return await hell.edit(f"**Error:**\n`{e}`")
        
        mention = f"[{sender.first_name}](tg://user?id={sender.id})"
        play_context = {
            "chat_id": event.chat_id,
            "user_id": event.sender_id,
            "duration": result[0]["duration"],
            "file": result[0]["id"],
            "title": result[0]["title"],
            "user": mention,
            "video_id": result[0]["id"],
            "vc_type": "video" if video else "voice",
            "force": force,
        }
        await player.play(hell, play_context)
        return
    
    # Handle search query
    try:
        parts = event.text.split(maxsplit=1)
        query = parts[1]
    except IndexError:
        return await hell.edit("Please provide a song name or YouTube URL.")
    
    try:
        await hell.edit("Searching ...")
        result = await ytube.get_data(query, False)
        if not result or len(result) == 0:
            return await hell.edit("No results found. Please try again with a different query.")
    except Exception as e:
        return await hell.edit(f"**Error:**\n`{e}`")
    
    mention = f"[{sender.first_name}](tg://user?id={sender.id})"
    play_context = {
        "chat_id": event.chat_id,
        "user_id": event.sender_id,
        "duration": result[0]["duration"],
        "file": result[0]["id"],
        "title": result[0]["title"],
        "user": mention,
        "video_id": result[0]["id"],
        "vc_type": "video" if video else "voice",
        "force": force,
    }
    await player.play(hell, play_context)


@hellbot.app.on(events.NewMessage(pattern=r"^/(current|playing)(?:\s|$)"))
@UserWrapper
async def playing(event):
    """Show currently playing track"""
    if not event.is_group:
        return
    if event.sender_id in Config.BANNED_USERS:
        return
    
    chat_id = event.chat_id
    is_active = await db.is_active_vc(chat_id)
    if not is_active:
        return await event.reply("No active voice chat found here.")
    
    que = Queue.get_current(chat_id)
    if not que:
        return await event.reply("Nothing is playing here.")
    
    photo = thumb.generate((359), (297, 302), que["video_id"])
    btns = Buttons.player_markup(chat_id, que["video_id"], hellbot.app.me.username)
    to_send = TEXTS.PLAYING.format(
        f"@{hellbot.app.me.username}",
        que["title"],
        que["duration"],
        que["user"],
    )
    
    if photo:
        sent = await event.reply(to_send, file=photo, buttons=btns)
    else:
        sent = await event.reply(to_send, buttons=btns)
    
    previous = Config.PLAYER_CACHE.get(chat_id)
    if previous:
        try:
            await previous.delete()
        except Exception:
            pass
    Config.PLAYER_CACHE[chat_id] = sent


@hellbot.app.on(events.NewMessage(pattern=r"^/(queue|que|q)$"))
@UserWrapper
async def queued_tracks(event):
    """Show queue"""
    if not event.is_group:
        return
    if event.sender_id in Config.BANNED_USERS:
        return
    
    hell = await event.reply("Getting Queue...")
    chat_id = event.chat_id
    is_active = await db.is_active_vc(chat_id)
    
    if not is_active:
        return await hell.edit("No active voice chat found here.")
    
    collection = Queue.get_queue(chat_id)
    if not collection:
        return await hell.edit("Nothing is playing here.")
    
    await MakePages.queue_page(hell, collection, 0, 0, True)


@hellbot.app.on(events.NewMessage(pattern=r"^/(clean|reload)(?:\s|$)"))
@AuthWrapper
async def clean_queue(event):
    """Clear queue"""
    if event.sender_id in Config.BANNED_USERS:
        return
    
    Queue.clear_queue(event.chat_id)
    hell = await event.reply("**Cleared Queue.**")
    await asyncio.sleep(10)
    await hell.delete()


@hellbot.app.on(events.CallbackQuery(pattern=b"queue"))
async def queued_tracks_cb(event):
    """Handle queue pagination callbacks"""
    if event.sender_id in Config.BANNED_USERS:
        return
    
    data = event.data.decode().split("|")
    _, action, page = data
    key = int(page)
    
    collection = Queue.get_queue(event.chat_id)
    length, _ = formatter.group_the_list(collection, 5, True)
    length -= 1
    
    if key == 0 and action == "prev":
        new_page = length
    elif key == length and action == "next":
        new_page = 0
    else:
        new_page = key + 1 if action == "next" else key - 1
    
    index = new_page * 5
    await MakePages.queue_page(event, collection, new_page, index, True)
