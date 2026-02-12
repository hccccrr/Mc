import datetime
import random

from telethon import events

from config import Config
from Music.core.clients import hellbot
from Music.core.database import db
from Music.core.decorators import UserWrapper, check_mode
from Music.helpers.buttons import Buttons
from Music.helpers.formatters import formatter
from Music.utils.pages import MakePages
from Music.utils.play import player
from Music.utils.youtube import ytube


@hellbot.app.on(events.NewMessage(pattern=r"^/(favs|myfavs|favorites|delfavs)"))
@check_mode
@UserWrapper
async def favorites(event):
    if event.sender_id in Config.BANNED_USERS:
        return
    
    delete = False
    hell = await event.reply("Fetching favorites ...")
    favs = await db.get_all_favorites(event.sender_id)
    
    if not favs:
        return await hell.edit("You dont have any favorite tracks added to the bot!")
    
    cmd = event.text.split()[0]
    if cmd[1] == "d":
        delete = True
    
    sender = await event.get_sender()
    mention = f"[{sender.first_name}](tg://user?id={sender.id})"
    
    await MakePages.favorite_page(
        hell, favs, event.sender_id, mention, 0, 0, True, delete
    )


@hellbot.app.on(events.CallbackQuery(pattern=b"add_favorite"))
async def add_favorites(event):
    if event.sender_id in Config.BANNED_USERS:
        return
    
    data = event.data.decode().split("|")
    _, video_id = data
    
    track = await db.get_favorite(event.sender_id, video_id)
    if track:
        return await event.answer("Already in your favorites!", alert=True)
    
    count = len(await db.get_all_favorites(event.sender_id))
    if count == Config.MAX_FAVORITES:
        return await event.answer(
            f"You can't have more than {Config.MAX_FAVORITES} favorites!",
            alert=True,
        )
    
    details = await ytube.get_data(video_id, True)
    context = {
        "video_id": details[0]["id"],
        "title": details[0]["title"],
        "duration": details[0]["duration"],
        "add_date": datetime.datetime.now().strftime("%d-%m-%Y %H:%M"),
    }
    await db.add_favorites(event.sender_id, video_id, context)
    await event.answer(
        f"Added to your favorites!\n\n{details[0]['title'][:50]}", alert=True
    )


@hellbot.app.on(events.CallbackQuery(pattern=b"myfavs"))
async def myfavs_cb(event):
    if event.sender_id in Config.BANNED_USERS:
        return
    
    data = event.data.decode().split("|")
    _, action, user_id, page, delete = data
    
    if int(user_id) != event.sender_id:
        return await event.answer("This is not for you!", alert=True)
    
    if action == "close":
        await event.delete()
        await event.answer("Closed!", alert=True)
    elif action == "play":
        btns = Buttons.playfavs_markup(int(user_id))
        await event.edit(
            "**❤️ Favorites Play:** \n\n__Choose the stream type to play your favorites list:__",
            buttons=btns,
        )
    else:
        collection = await db.get_all_favorites(int(user_id))
        last_page, _ = formatter.group_the_list(collection, 5, length=True)
        last_page -= 1
        
        page = int(page)
        if page == 0 and action == "prev":
            new_page = last_page
        elif page == last_page and action == "next":
            new_page = 0
        else:
            new_page = page + 1 if action == "next" else page - 1
        
        index = new_page * 5
        to_del = False if int(delete) == 1 else True
        
        sender = await event.get_sender()
        mention = f"[{sender.first_name}](tg://user?id={sender.id})"
        
        await MakePages.favorite_page(
            event,
            collection,
            int(user_id),
            mention,
            new_page,
            index,
            True,
            to_del,
        )


@hellbot.app.on(events.CallbackQuery(pattern=b"delfavs"))
async def delfavs_cb(event):
    if event.sender_id in Config.BANNED_USERS:
        return
    
    data = event.data.decode().split("|")
    _, action, user_id = data
    
    if int(user_id) != event.sender_id:
        return await event.answer("This is not for you!", alert=True)
    
    collection = await db.get_all_favorites(int(user_id))
    
    if action == "all":
        for i in collection:
            await db.rem_favorites(int(user_id), i["video_id"])
        return await event.edit("Deleted all your favorites!")
    else:
        is_deleted = await db.rem_favorites(int(user_id), action)
        if is_deleted:
            await event.answer("Deleted from your favorites!", alert=True)
            collection = await db.get_all_favorites(int(user_id))
            sender = await event.get_sender()
            mention = f"[{sender.first_name}](tg://user?id={sender.id})"
            await MakePages.favorite_page(
                event, collection, int(user_id), mention, 0, 0, True, True
            )
        else:
            await event.answer("Not in your favorites!", alert=True)


@hellbot.app.on(events.CallbackQuery(pattern=b"favsplay"))
async def favsplay_cb(event):
    if event.sender_id in Config.BANNED_USERS:
        return
    
    data = event.data.decode().split("|")
    _, action, user_id = data
    
    if int(user_id) != event.sender_id:
        return await event.answer("This is not for you!", alert=True)
    
    if action == "close":
        await event.delete()
        return await event.answer("Closed!", alert=True)
    else:
        await event.edit("Playing your favorites")
        all_tracks = await db.get_all_favorites(int(user_id))
        random.shuffle(all_tracks)
        video = True if action == "video" else False
        
        sender = await event.get_sender()
        mention = f"[{sender.first_name}](tg://user?id={sender.id})"
        
        context = {
            "user_id": event.sender_id,
            "user_mention": mention,
        }
        await player.playlist(event, context, all_tracks, video)
