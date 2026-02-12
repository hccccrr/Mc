from telethon import events

from config import Config
from Music.core.clients import hellbot
from Music.core.decorators import UserWrapper, check_mode
from Music.helpers.formatters import formatter
from Music.utils.pages import MakePages
from Music.utils.youtube import ytube


@hellbot.app.on(events.NewMessage(pattern=r"^/song"))
@check_mode
@UserWrapper
async def songs(event):
    if event.sender_id in Config.BANNED_USERS:
        return
    
    parts = event.text.split(maxsplit=1)
    if len(parts) == 1:
        return await event.reply("Nothing given to search.")
    
    query = parts[1]
    hell = await event.reply(
        f"<b><i>Searching</i></b> \"{query}\" ...",
        file=Config.BLACK_IMG,
        parse_mode='html'
    )
    
    all_tracks = await ytube.get_data(query, False, 10)
    rand_key = formatter.gen_key(str(event.sender_id), 5)
    Config.SONG_CACHE[rand_key] = all_tracks
    await MakePages.song_page(hell, rand_key, 0)


@hellbot.app.on(events.NewMessage(pattern=r"^/lyrics"))
@check_mode
@UserWrapper
async def lyrics(event):
    if event.sender_id in Config.BANNED_USERS:
        return
    
    if not Config.LYRICS_API:
        return await event.reply("Lyrics module is disabled!")
    
    parts = event.text.split(maxsplit=1)
    if len(parts) != 2:
        return await event.reply(
            "__Nothing given to search.__ \nExample: `/lyrics loose yourself - eminem`"
        )
    
    _input_ = parts[1].strip()
    query = _input_.split("-", 1)
    
    if len(query) == 2:
        song = query[0].strip()
        artist = query[1].strip()
    else:
        song = query[0].strip()
        artist = ""
    
    text = f"**Searching lyrics ...** \n\n__Song:__ `{song}`"
    if artist != "":
        text += f"\n__Artist:__ `{artist}`"
    
    hell = await event.reply(text)
    results = await ytube.get_lyrics(song, artist)
    
    if results:
        title = results["title"]
        image = results["image"]
        lyrics = results["lyrics"]
        final = f"<b><i>• Song:</b></i> <code>{title}</code> \n<b><i>• Lyrics:</b></i> \n<code>{lyrics}</code>"
        
        if len(final) >= 4095:
            page_name = f"{title}"
            to_paste = f"<img src='{image}'/> \n{final} \n<img src='https://telegra.ph/file/2c546060b20dfd7c1ff2d.jpg'/>"
            link = await formatter.telegraph_paste(page_name, to_paste)
            await hell.edit(
                f"**Lyrics too big! Get it from here:** \n\n• [{title}]({link})",
                link_preview=False,
            )
        else:
            await hell.edit(final, parse_mode='html')
        
        chat = await event.get_chat()
        chat_title = chat.title if hasattr(chat, 'title') else chat.first_name
        sender = await event.get_sender()
        mention = f"[{sender.first_name}](tg://user?id={sender.id})"
        
        await hellbot.logit(
            "lyrics",
            f"**⤷ Lyrics:** `{title}`\n**⤷ Chat:** {chat_title} [`{event.chat_id}`]\n**⤷ User:** {mention} [`{event.sender_id}`]",
        )
    else:
        await hell.edit("Unexpected Error Occured.")


@hellbot.app.on(events.CallbackQuery(pattern=b"song_dl"))
async def song_cb(event):
    if event.sender_id in Config.BANNED_USERS:
        return
    
    data = event.data.decode().split("|")
    _, action, key, rand_key = data
    
    user = rand_key.split("_")[0]
    key = int(key)
    
    if event.sender_id != int(user):
        await event.answer("You are not allowed to do that!", alert=True)
        return
    
    if action == "adl":
        await ytube.send_song(event, rand_key, key, False)
        return
    elif action == "vdl":
        await ytube.send_song(event, rand_key, key, True)
        return
    elif action == "close":
        Config.SONG_CACHE.pop(rand_key)
        await event.delete()
        return
    else:
        all_tracks = Config.SONG_CACHE[rand_key]
        length = len(all_tracks)
        
        if key == 0 and action == "prev":
            key = length - 1
        elif key == length - 1 and action == "next":
            key = 0
        else:
            key = key + 1 if action == "next" else key - 1
    
    await MakePages.song_page(event, rand_key, key)
    
