import os
import asyncio
import requests
from telethon import events, Button
from telethon.errors import ChatAdminRequiredError

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
            return False, f"ERROR: {response.status_code} - {response.text}"
    except Exception as e:
        return False, f"ERROR: {str(e)}"


@hellbot.app.on(events.NewMessage(pattern=r"^/(tgm|telegraph)"))
@UserWrapper
async def telegraph_upload(event):
    """Upload media to telegraph/catbox"""
    if event.sender_id in Config.BANNED_USERS:
        return
    
    if not event.is_reply:
        return await event.reply("**Please reply to a media to upload**")
    
    media = await event.get_reply_message()
    file_size = 0
    
    if media.photo:
        file_size = media.photo.size if hasattr(media.photo, 'size') else 0
    elif media.video:
        file_size = media.video.size if hasattr(media.video, 'size') else 0
    elif media.document:
        file_size = media.document.size if hasattr(media.document, 'size') else 0
    else:
        return await event.reply("**Please reply to a valid media file**")
    
    if file_size > 200 * 1024 * 1024:
        return await event.reply("**Please provide a media file under 200MB.**")
    
    text = await event.reply("**⏳ Hold on baby....♡**")
    
    try:
        local_path = await media.download_media()
        await text.edit("**📤 Uploading to telegraph...**")
        
        success, upload_path = upload_to_catbox(local_path)
        
        if success:
            await text.edit(
                f"**🌐 | [👉Your link tap here👈]({upload_path})**",
                buttons=[
                    [Button.url("✨ Tap to open link ✨", url=upload_path)]
                ],
                link_preview=False,
            )
        else:
            await text.edit(
                f"**An error occurred while uploading your file**\n\n`{upload_path}`"
            )
        
        try:
            os.remove(local_path)
        except Exception:
            pass
    
    except Exception as e:
        await text.edit(
            f"**❌ File upload failed**\n\n<i>Reason: {e}</i>",
            parse_mode='html'
        )
        try:
            os.remove(local_path)
        except Exception:
            pass


AUTO_DELETE_TIME = 30  # seconds


@hellbot.app.on(events.NewMessage(pattern=r"^/gclink"))
@UserWrapper
async def get_gc_link(event):
    if event.sender_id in Config.BANNED_USERS:
        return
    
    # Get chat id
    parts = event.text.split()
    if len(parts) > 1:
        try:
            chat_id = int(parts[1])
        except ValueError:
            return await event.reply("❌ **Invalid chat ID.**")
    else:
        chat_id = event.chat_id

    try:
        link = await hellbot.app.export_chat_invite_link(chat_id)
        sent = await event.reply(
            f"**🔗 Group Invite Link:**\n\n{link}\n\n"
            f"_This message will auto-delete in {AUTO_DELETE_TIME} seconds._"
        )

        # Auto delete
        await asyncio.sleep(AUTO_DELETE_TIME)
        await sent.delete()
        await event.delete()

    except ChatAdminRequiredError:
        await event.reply(
            "❌ **Bot needs 'Invite Users via Link' permission in that group.**"
        )
    except Exception as e:
        await event.reply(f"**ERROR:** `{e}`")
        
