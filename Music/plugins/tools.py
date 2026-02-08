import os
import requests
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from config import Config
from Music.core.clients import hellbot
from Music.core.decorators import UserWrapper


def upload_to_catbox(file_path):
    """Upload file to catbox.moe"""
    url = "https://catbox.moe/user/api.php"
    data = {"reqtype": "fileupload", "json": "true"}
    files = {"fileToUpload": open(file_path, "rb")}
    
    try:
        response = requests.post(url, data=data, files=files)
        if response.status_code == 200:
            return True, response.text.strip()
        else:
            return False, f"ᴇʀʀᴏʀ: {response.status_code} - {response.text}"
    except Exception as e:
        return False, f"ᴇʀʀᴏʀ: {str(e)}"


@hellbot.app.on_message(filters.command(["tgm", "telegraph"]) & ~Config.BANNED_USERS)
@UserWrapper
async def telegraph_upload(_, message: Message):
    """Upload media to telegraph/catbox"""
    if not message.reply_to_message:
        return await message.reply_text(
            "**Pʟᴇᴀsᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇᴅɪᴀ ᴛᴏ ᴜᴘʟᴏᴀᴅ**"
        )
    
    media = message.reply_to_message
    file_size = 0
    
    if media.photo:
        file_size = media.photo.file_size
    elif media.video:
        file_size = media.video.file_size
    elif media.document:
        file_size = media.document.file_size
    else:
        return await message.reply_text(
            "**Pʟᴇᴀsᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴠᴀʟɪᴅ ᴍᴇᴅɪᴀ ғɪʟᴇ**"
        )
    
    if file_size > 200 * 1024 * 1024:
        return await message.reply_text(
            "**Pʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴍᴇᴅɪᴀ ғɪʟᴇ ᴜɴᴅᴇʀ 200MB.**"
        )
    
    text = await message.reply_text("**❍ ʜᴏʟᴅ ᴏɴ ʙᴀʙʏ....♡**")
    
    async def progress(current, total):
        try:
            await text.edit_text(
                f"**📥 Dᴏᴡɴʟᴏᴀᴅɪɴɢ... {current * 100 / total:.1f}%**"
            )
        except Exception:
            pass
    
    try:
        local_path = await media.download(progress=progress)
        await text.edit_text("**📤 Uᴘʟᴏᴀᴅɪɴɢ ᴛᴏ ᴛᴇʟᴇɢʀᴀᴘʜ...**")
        
        success, upload_path = upload_to_catbox(local_path)
        
        if success:
            await text.edit_text(
                f"**🌐 | [👉ʏᴏᴜʀ ʟɪɴᴋ ᴛᴀᴘ ʜᴇʀᴇ👈]({upload_path})**",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "✨ ᴛᴀᴘ ᴛᴏ ᴏᴘᴇɴ ʟɪɴᴋ ✨",
                                url=upload_path,
                            )
                        ]
                    ]
                ),
                disable_web_page_preview=True,
            )
        else:
            await text.edit_text(
                f"**ᴀɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ ᴡʜɪʟᴇ ᴜᴘʟᴏᴀᴅɪɴɢ ʏᴏᴜʀ ғɪʟᴇ**\n\n`{upload_path}`"
            )
        
        try:
            os.remove(local_path)
        except Exception:
            pass
    
    except Exception as e:
        await text.edit_text(
            f"**❌ Fɪʟᴇ ᴜᴘʟᴏᴀᴅ ғᴀɪʟᴇᴅ**\n\n<i>Rᴇᴀsᴏɴ: {e}</i>"
        )
        try:
            os.remove(local_path)
        except Exception:
            pass


from pyrogram import filters
from pyrogram.types import Message
from pyrogram.errors import ChatAdminRequired

from config import Config
from Music.core.clients import hellbot
from Music.core.decorators import UserWrapper


import asyncio
from pyrogram import filters
from pyrogram.types import Message
from pyrogram.errors import ChatAdminRequired

from config import Config
from Music.core.clients import hellbot
from Music.core.decorators import UserWrapper


AUTO_DELETE_TIME = 30  # seconds (change if you want)


@hellbot.app.on_message(filters.command("gclink"))
@UserWrapper
async def get_gc_link(_, message: Message):
    # 📌 Get chat id
    if len(message.command) > 1:
        try:
            chat_id = int(message.command[1])
        except ValueError:
            return await message.reply_text("❌ **Invalid chat ID.**")
    else:
        chat_id = message.chat.id

    try:
        link = await hellbot.app.export_chat_invite_link(chat_id)
        sent = await message.reply_text(
            f"**🔗 Group Invite Link:**\n\n{link}\n\n"
            f"_This message will auto-delete in {AUTO_DELETE_TIME} seconds._"
        )

        # ⏳ Auto delete
        await asyncio.sleep(AUTO_DELETE_TIME)
        await sent.delete()
        await message.delete()

    except ChatAdminRequired:
        await message.reply_text(
            "❌ **Bot needs 'Invite Users via Link' permission in that group.**"
        )
    except Exception as e:
        await message.reply_text(f"**ERROR:** `{e}`")
