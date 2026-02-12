import os

from telethon import Button
from telethon.tl.types import MessageEntityUrl, MessageEntityTextUrl

from config import Config
from Music.core.calls import hellmusic
from Music.core.clients import hellbot
from Music.core.database import db
from Music.core.logger import LOGS
from Music.helpers.buttons import Buttons
from Music.helpers.strings import TEXTS

from .queue import Queue
from .thumbnail import thumb
from .youtube import ytube


class Player:
    def __init__(self) -> None:
        pass

    async def get_url(self, message):
        """Extract URL from message (Telethon version)"""
        msg = [message]
        replied = await message.get_reply_message()
        if replied:
            msg.append(replied)
        
        url = ""
        offset = length = None
        
        for m in msg:
            if offset:
                break
            
            if m.entities:
                for entity in m.entities:
                    if isinstance(entity, MessageEntityUrl):
                        url = m.text or m.message
                        offset, length = entity.offset, entity.length
                        break
                    elif isinstance(entity, MessageEntityTextUrl):
                        return entity.url
        
        if offset is None:
            return None
        return url[offset : offset + length]

    async def play(self, message, context: dict, edit: bool = True):
        """Play track in voice chat"""
        (
            chat_id,
            user_id,
            duration,
            file,
            title,
            user,
            video_id,
            vc_type,
            force,
        ) = context.values()
        
        if force:
            await hellmusic.leave_vc(chat_id, True)
        
        if video_id == "telegram":
            file_path = file
        else:
            try:
                if edit:
                    await message.edit("Downloading ...")
                else:
                    await message.reply("Downloading ...")
                file_path = await ytube.download(
                    video_id, True, True if vc_type == "video" else False
                )
            except Exception as e:
                if edit:
                    await message.edit(str(e))
                else:
                    await message.reply(str(e))
                return
        
        position = Queue.put_queue(
            chat_id,
            user_id,
            duration,
            file_path,
            title,
            user,
            video_id,
            vc_type,
            force,
        )
        
        if position == 0:
            photo = thumb.generate((359), (297, 302), video_id)
            try:
                await hellmusic.join_vc(
                    chat_id, file_path, True if vc_type == "video" else False
                )
            except Exception as e:
                await message.delete()
                await hellbot.app.send_message(chat_id, str(e))
                Queue.clear_queue(chat_id)
                if os.path.exists(file_path):
                    os.remove(file_path)
                if photo and os.path.exists(photo):
                    os.remove(photo)
                return
            
            btns = Buttons.player_markup(chat_id, video_id, hellbot.app.me.username)
            
            if photo:
                sent = await hellbot.app.send_message(
                    chat_id,
                    TEXTS.PLAYING.format(
                        hellbot.app.mention,
                        title,
                        duration,
                        user,
                    ),
                    file=photo,
                    buttons=btns,
                )
                if os.path.exists(photo):
                    os.remove(photo)
            else:
                sent = await hellbot.app.send_message(
                    chat_id,
                    TEXTS.PLAYING.format(
                        hellbot.app.mention,
                        title,
                        duration,
                        user,
                    ),
                    buttons=btns,
                )
            
            previous = Config.PLAYER_CACHE.get(chat_id)
            if previous:
                try:
                    await previous.delete()
                except Exception:
                    pass
            Config.PLAYER_CACHE[chat_id] = sent
        else:
            sent = await hellbot.app.send_message(
                chat_id,
                TEXTS.QUEUE.format(
                    position,
                    title,
                    duration,
                    user,
                ),
                buttons=Buttons.close_markup(),
            )
            prev_q = Config.QUEUE_CACHE.get(chat_id)
            if prev_q:
                try:
                    await prev_q.delete()
                except Exception:
                    pass
            Config.QUEUE_CACHE[chat_id] = sent
            return await message.delete()
        
        await message.delete()
        await db.update_songs_count(1)
        await db.update_user(user_id, "songs_played", 1)
        
        chat = await hellbot.app.get_entity(chat_id)
        chat_name = chat.title if hasattr(chat, 'title') else str(chat_id)
        await hellbot.logit(
            f"play {vc_type}",
            f"**├ Song:** `{title}` \n**├ Chat:** {chat_name} [`{chat_id}`] \n**├ User:** {user}",
        )

    async def skip(self, chat_id: int, message):
        """Skip current track"""
        await message.edit("Skipping ...")
        await hellmusic.change_vc(chat_id)
        await message.delete()

    async def replay(self, chat_id: int, message):
        """Replay current track"""
        que = Queue.get_current(chat_id)
        if not que:
            return await message.edit("Nothing is playing to replay")
        
        video = True if que["vc_type"] == "video" else False
        photo = thumb.generate((359), (297, 302), que["video_id"])
        
        if que["file"] == que["video_id"]:
            file_path = await ytube.download(que["video_id"], True, video)
        else:
            file_path = que["file"]
        
        try:
            await hellmusic.replay_vc(chat_id, file_path, video)
        except Exception as e:
            await message.delete()
            await hellbot.app.send_message(chat_id, str(e))
            Queue.clear_queue(chat_id)
            if os.path.exists(que["file"]):
                os.remove(que["file"])
            if photo and os.path.exists(photo):
                os.remove(photo)
            return
        
        btns = Buttons.player_markup(chat_id, que["video_id"], hellbot.app.me.username)
        
        if photo:
            sent = await hellbot.app.send_message(
                chat_id,
                TEXTS.PLAYING.format(
                    hellbot.app.mention,
                    que["title"],
                    que["duration"],
                    que["user"],
                ),
                file=photo,
                buttons=btns,
            )
            if os.path.exists(photo):
                os.remove(photo)
        else:
            sent = await hellbot.app.send_message(
                chat_id,
                TEXTS.PLAYING.format(
                    hellbot.app.mention,
                    que["title"],
                    que["duration"],
                    que["user"],
                ),
                buttons=btns,
            )
        
        previous = Config.PLAYER_CACHE.get(chat_id)
        if previous:
            try:
                await previous.delete()
            except Exception:
                pass
        Config.PLAYER_CACHE[chat_id] = sent
        await message.delete()

    async def playlist(
        self, message, user_dict: dict, collection: list, video: bool = False
    ):
        """Play playlist"""
        vc_type = "video" if video else "voice"
        count = failed = 0
        user_id, user_mention = user_dict.values()
        
        chat_id = message.chat_id
        
        if await db.is_active_vc(chat_id):
            await message.edit(
                "This chat have an active vc. Adding songs from playlist in the queue... \n\n__This might take some time!__"
            )
        
        previously = len(Queue.get_queue(chat_id))
        
        for i in collection:
            try:
                data = (await ytube.get_data(i, True, 1))[0]
                
                if count == 0 and previously == 0:
                    file_path = await ytube.download(data["id"], True, video)
                    _queue = Queue.put_queue(
                        chat_id,
                        user_id,
                        data["duration"],
                        file_path,
                        data["title"],
                        user_mention,
                        data["id"],
                        vc_type,
                        False,
                    )
                    
                    try:
                        photo = thumb.generate((359), (297, 302), data["id"])
                        await hellmusic.join_vc(chat_id, file_path, video)
                    except Exception as e:
                        await message.edit(str(e))
                        Queue.clear_queue(chat_id)
                        if os.path.exists(file_path):
                            os.remove(file_path)
                        if photo and os.path.exists(photo):
                            os.remove(photo)
                        return
                    
                    btns = Buttons.player_markup(
                        chat_id, data["id"], hellbot.app.me.username
                    )
                    
                    if photo:
                        sent = await hellbot.app.send_message(
                            chat_id,
                            TEXTS.PLAYING.format(
                                hellbot.app.mention,
                                data["title"],
                                data["duration"],
                                user_mention,
                            ),
                            file=photo,
                            buttons=btns,
                        )
                        if os.path.exists(photo):
                            os.remove(photo)
                    else:
                        sent = await hellbot.app.send_message(
                            chat_id,
                            TEXTS.PLAYING.format(
                                hellbot.app.mention,
                                data["title"],
                                data["duration"],
                                user_mention,
                            ),
                            buttons=btns,
                        )
                    
                    old = Config.PLAYER_CACHE.get(chat_id)
                    if old:
                        try:
                            await old.delete()
                        except Exception:
                            pass
                    Config.PLAYER_CACHE[chat_id] = sent
                else:
                    _queue = Queue.put_queue(
                        chat_id,
                        user_id,
                        data["duration"],
                        data["id"],
                        data["title"],
                        user_mention,
                        data["id"],
                        vc_type,
                        False,
                    )
                count += 1
            except Exception as e:
                LOGS.error(str(e))
                failed += 1
        
        await message.edit(
            f"**Added all tracks to queue!** \n\n**Total tracks: `{count}`** \n**Failed: `{failed}`**"
        )


player = Player()
