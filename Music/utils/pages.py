from config import Config
from Music.core.clients import hellbot
from Music.core.database import db
from Music.helpers.buttons import Buttons
from Music.helpers.formatters import formatter


class Pages:
    def __init__(self):
        pass

    async def song_page(self, message, rand_key: str, key: int):
        """Display song page with navigation"""
        # Get message object - handle both callback and direct message
        if hasattr(message, 'edit'):
            # It's already a message from callback
            m = message
        else:
            # It's an event, get the message
            m = message.message if hasattr(message, 'message') else message
        
        if Config.SONG_CACHE.get(rand_key):
            all_tracks = Config.SONG_CACHE[rand_key]
            btns = Buttons.song_markup(rand_key, all_tracks[key]["link"], key)
            cap = f"__({key+1}/{len(all_tracks)})__ **Song Downloader:**\n\n"
            cap += f"**• Title:** `{all_tracks[key]['title']}`\n\n"
            cap += f"🎶 @{hellbot.app.me.username}"
            
            # Edit media with new photo and caption
            await m.edit(
                cap,
                file=all_tracks[key]["thumbnail"],
                buttons=btns,
            )
        else:
            await m.delete()
            return await hellbot.app.send_message(
                m.chat_id, 
                "Query timed out! Please start the query again."
            )

    async def activevc_page(
        self,
        message,
        collection: list,
        page: int = 0,
        index: int = 0,
        edit: bool = False,
    ):
        """Display active voice chats page"""
        # Get message object
        if hasattr(message, 'edit'):
            m = message
        else:
            m = message.message if hasattr(message, 'message') else message
        
        grouped, total = formatter.group_the_list(collection)
        text = f"__({page+1}/{len(grouped)})__ **@{hellbot.app.me.username} Active Voice Chats:** __{total} chats__\n\n"
        btns = Buttons.active_vc_markup(len(grouped), page)
        
        try:
            for active in grouped[int(page)]:
                index += 1
                text += f"**{'0' if index < 10 else ''}{index}:** {active['title']} [`{active['chat_id']}`]\n"
                text += f"    **Listeners:** __{active['participants']}__\n"
                text += f"    **Playing:** __{active['playing']}__\n"
                text += f"    **VC Type:** __{active['vc_type']}__\n"
                text += f"    **Since:** __{active['active_since']}__\n\n"
        except IndexError:
            page = 0
            for active in grouped[int(page)]:
                index += 1
                text += f"**{'0' if index < 10 else ''}{index}:** {active['title']} [`{active['chat_id']}`]\n"
                text += f"    **Listeners:** __{active['participants']}__\n"
                text += f"    **Playing:** __{active['playing']}__\n"
                text += f"    **Since:** __{active['active_since']}__\n\n"
        
        if edit:
            await m.edit(text, buttons=btns)
        else:
            await m.reply(text, buttons=btns)

    async def authusers_page(
        self,
        message,
        rand_key: str,
        page: int = 0,
        index: int = 0,
        edit: bool = False,
    ):
        """Display authorized users page"""
        # Get message object
        if hasattr(message, 'edit'):
            m = message
        else:
            m = message.message if hasattr(message, 'message') else message
        
        collection = Config.CACHE.get(rand_key, [])
        grouped, total = formatter.group_the_list(collection, 6)
        
        # Get chat title
        chat = await hellbot.app.get_entity(m.chat_id)
        chat_title = chat.title if hasattr(chat, 'title') else "Unknown Chat"
        
        text = f"__({page+1}/{len(grouped)})__ **Authorized Users in {chat_title}:**\n    >> __{total} users__\n\n"
        btns = Buttons.authusers_markup(len(grouped), page, rand_key)
        
        try:
            for auth in grouped[int(page)]:
                index += 1
                text += f"**{'0' if index < 10 else ''}{index}:** {auth['auth_user']}\n"
                text += (
                    f"    **Auth By:** {auth['admin_name']} (`{auth['admin_id']}`)\n"
                )
                text += f"    **Since:** __{auth['auth_date']}__\n\n"
        except IndexError:
            page = 0
            for auth in grouped[int(page)]:
                index += 1
                text += f"**{'0' if index < 10 else ''}{index}:** {auth['auth_user']}\n"
                text += (
                    f"    **Auth By:** {auth['admin_name']} (`{auth['admin_id']}`)\n"
                )
                text += f"    **Since:** __{auth['auth_date']}__\n\n"
        
        if edit:
            await m.edit(text, buttons=btns)
        else:
            await m.reply(text, buttons=btns)

    async def favorite_page(
        self,
        message,
        collection: list,
        user_id: int,
        mention: str,
        page: int = 0,
        index: int = 0,
        edit: bool = False,
        delete: bool = False,
    ):
        """Display favorite tracks page"""
        # Get message object
        if hasattr(message, 'edit'):
            m = message
        else:
            m = message.message if hasattr(message, 'message') else message
        
        grouped, total = formatter.group_the_list(collection, 5)
        text = f"__({page+1}/{len(grouped)})__ {mention} **favorites:** __{total} tracks__\n\n"
        btns, final = await Buttons.favorite_markup(
            grouped, user_id, page, index, db, delete
        )
        
        if edit:
            await m.edit(f"{text}{final}", buttons=btns)
        else:
            await m.reply(f"{text}{final}", buttons=btns)

    async def queue_page(
        self,
        message,
        collection: list,
        page: int = 0,
        index: int = 0,
        edit: bool = False,
    ):
        """Display queue page"""
        # Get message object
        if hasattr(message, 'edit'):
            m = message
        else:
            m = message.message if hasattr(message, 'message') else message
        
        grouped, total = formatter.group_the_list(collection, 5)
        text = f"__({page+1}/{len(grouped)})__ **In Queue:** __{total} tracks__\n\n"
        btns = Buttons.queue_markup(len(grouped), page)
        
        try:
            for que in grouped[page]:
                index += 1
                text += f"**{'0' if index < 10 else ''}{index}:** {que['title']}\n"
                text += f"    **VC Type:** {que['vc_type']}\n"
                text += f"    **Requested By:** {que['user']}\n"
                text += f"    **Duration:** __{que['duration']}__\n\n"
        except IndexError:
            return await m.edit("**No more tracks in queue!**")
        
        if edit:
            await m.edit(text, buttons=btns)
        else:
            await m.reply(text, buttons=btns)


MakePages = Pages()
