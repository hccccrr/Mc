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


@hellbot.app.on_message(filters.command("gclink") & Config.SUDO_USERS)
@UserWrapper
async def get_gc_link(_, message: Message):
    """Get group invite link"""
    if message.chat.type not in ["group", "supergroup"]:
        return await message.reply_text(
            "**❌ This command works only in groups.**"
        )
    
    try:
        link = await hellbot.app.export_chat_invite_link(message.chat.id)
        await message.reply_text(f"**🔗 Group Invite Link:**\n\n{link}")
    except ChatAdminRequired:
        await message.reply_text(
            "**❌ I need 'Invite Users via Link' permission to generate link.**"
        )
    except Exception as e:
        await message.reply_text(f"**ERROR:** `{e}`")
