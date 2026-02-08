from typing import Optional
from pyrogram import Client, filters
from pyrogram.errors import ChatAdminRequired
from pyrogram.raw.functions.channels import GetFullChannel
from pyrogram.raw.functions.messages import GetFullChat
from pyrogram.raw.functions.phone import CreateGroupCall, DiscardGroupCall
from pyrogram.raw.types import InputGroupCall, InputPeerChannel, InputPeerChat
from pyrogram.types import ChatPrivileges, Message

from config import Config
from Music.core.clients import hellbot
from Music.core.database import db
from Music.core.decorators import UserWrapper


async def get_assistant(chat_id: int):
    """Get assistant client for the chat"""
    # Assuming you have this function in your database module
    # If not, you'll need to implement it
    try:
        from Music.core.userbot import get_userbot
        return await get_userbot(chat_id)
    except:
        return hellbot.userbot  # Fallback to main userbot


async def get_group_call(
    client: Client, message: Message, err_msg: str = ""
) -> Optional[InputGroupCall]:
    """Get active group call"""
    assistant = await get_assistant(message.chat.id)
    chat_peer = await assistant.resolve_peer(message.chat.id)
    
    if isinstance(chat_peer, (InputPeerChannel, InputPeerChat)):
        if isinstance(chat_peer, InputPeerChannel):
            full_chat = (
                await assistant.invoke(GetFullChannel(channel=chat_peer))
            ).full_chat
        elif isinstance(chat_peer, InputPeerChat):
            full_chat = (
                await assistant.invoke(GetFullChat(chat_id=chat_peer.chat_id))
            ).full_chat
        
        if full_chat is not None:
            return full_chat.call
    
    await message.reply_text(f"**No group ᴠᴏɪᴄᴇ ᴄʜᴀᴛ Found** {err_msg}")
    return False


@hellbot.app.on_message(filters.command(["vcstart", "startvc"]) & ~Config.BANNED_USERS)
@UserWrapper
async def start_group_call(_, message: Message):
    """Start voice chat in the group"""
    chat_id = message.chat.id
    assistant = await get_assistant(chat_id)
    
    if assistant is None:
        return await message.reply_text("**ᴇʀʀᴏʀ ᴡɪᴛʜ ᴀꜱꜱɪꜱᴛᴀɴᴛ**")
    
    ass = await assistant.get_me()
    assid = ass.id
    
    msg = await message.reply_text("**ꜱᴛᴀʀᴛɪɴɢ ᴛʜᴇ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ...**")
    
    try:
        peer = await assistant.resolve_peer(chat_id)
        await assistant.invoke(
            CreateGroupCall(
                peer=InputPeerChannel(
                    channel_id=peer.channel_id,
                    access_hash=peer.access_hash,
                ),
                random_id=assistant.rnd_id() // 9000000000,
            )
        )
        await msg.edit_text("**ᴠᴏɪᴄᴇ ᴄʜᴀᴛ ꜱᴛᴀʀᴛᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ⚡️~!**")
    except ChatAdminRequired:
        try:
            await hellbot.app.promote_chat_member(
                chat_id,
                assid,
                privileges=ChatPrivileges(
                    can_manage_chat=False,
                    can_delete_messages=False,
                    can_manage_video_chats=True,
                    can_restrict_members=False,
                    can_change_info=False,
                    can_invite_users=False,
                    can_pin_messages=False,
                    can_promote_members=False,
                ),
            )
            peer = await assistant.resolve_peer(chat_id)
            await assistant.invoke(
                CreateGroupCall(
                    peer=InputPeerChannel(
                        channel_id=peer.channel_id,
                        access_hash=peer.access_hash,
                    ),
                    random_id=assistant.rnd_id() // 9000000000,
                )
            )
            await hellbot.app.promote_chat_member(
                chat_id,
                assid,
                privileges=ChatPrivileges(
                    can_manage_chat=False,
                    can_delete_messages=False,
                    can_manage_video_chats=False,
                    can_restrict_members=False,
                    can_change_info=False,
                    can_invite_users=False,
                    can_pin_messages=False,
                    can_promote_members=False,
                ),
            )
            await msg.edit_text("**ᴠᴏɪᴄᴇ ᴄʜᴀᴛ ꜱᴛᴀʀᴛᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ⚡️~!**")
        except Exception as e:
            await msg.edit_text(
                f"**ɢɪᴠᴇ ᴛʜᴇ ʙᴏᴛ ᴀʟʟ ᴘᴇʀᴍɪꜱꜱɪᴏɴꜱ ᴀɴᴅ ᴛʀʏ ᴀɢᴀɪɴ ⚡**\n\n"
                f"**Error:** `{e}`"
            )


@hellbot.app.on_message(filters.command(["vcend", "endvc"]) & ~Config.BANNED_USERS)
@UserWrapper
async def stop_group_call(_, message: Message):
    """Stop voice chat in the group"""
    chat_id = message.chat.id
    assistant = await get_assistant(chat_id)
    
    if assistant is None:
        return await message.reply_text("**ᴇʀʀᴏʀ ᴡɪᴛʜ ᴀꜱꜱɪꜱᴛᴀɴᴛ**")
    
    ass = await assistant.get_me()
    assid = ass.id
    
    msg = await message.reply_text("**ᴄʟᴏꜱɪɴɢ ᴛʜᴇ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ...**")
    
    try:
        if not (
            group_call := (
                await get_group_call(
                    assistant, message, err_msg=", ɢʀᴏᴜᴘ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ ᴀʟʀᴇᴀᴅʏ ᴇɴᴅᴇᴅ"
                )
            )
        ):
            return
        
        await assistant.invoke(DiscardGroupCall(call=group_call))
        await msg.edit_text("**ᴠᴏɪᴄᴇ ᴄʜᴀᴛ ᴄʟᴏꜱᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ⚡️~!**")
    except Exception as e:
        if "GROUPCALL_FORBIDDEN" in str(e):
            try:
                await hellbot.app.promote_chat_member(
                    chat_id,
                    assid,
                    privileges=ChatPrivileges(
                        can_manage_chat=False,
                        can_delete_messages=False,
                        can_manage_video_chats=True,
                        can_restrict_members=False,
                        can_change_info=False,
                        can_invite_users=False,
                        can_pin_messages=False,
                        can_promote_members=False,
                    ),
                )
                if not (
                    group_call := (
                        await get_group_call(
                            assistant, message, err_msg=", ɢʀᴏᴜᴘ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ ᴀʟʀᴇᴀᴅʏ ᴇɴᴅᴇᴅ"
                        )
                    )
                ):
                    return
                
                await assistant.invoke(DiscardGroupCall(call=group_call))
                await hellbot.app.promote_chat_member(
                    chat_id,
                    assid,
                    privileges=ChatPrivileges(
                        can_manage_chat=False,
                        can_delete_messages=False,
                        can_manage_video_chats=False,
                        can_restrict_members=False,
                        can_change_info=False,
                        can_invite_users=False,
                        can_pin_messages=False,
                        can_promote_members=False,
                    ),
                )
                await msg.edit_text("**ᴠᴏɪᴄᴇ ᴄʜᴀᴛ ᴄʟᴏꜱᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ⚡️~!**")
            except Exception as err:
                await msg.edit_text(
                    f"**ɢɪᴠᴇ ᴛʜᴇ ʙᴏᴛ ᴀʟʟ ᴘᴇʀᴍɪꜱꜱɪᴏɴꜱ ᴀɴᴅ ᴛʀʏ ᴀɢᴀɪɴ**\n\n"
                    f"**Error:** `{err}`"
                )
        else:
            await msg.edit_text(f"**Error:** `{e}`")


